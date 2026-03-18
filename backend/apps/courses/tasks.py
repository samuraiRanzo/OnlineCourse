import os
import subprocess
import shutil
import tempfile
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


def get_ffmpeg():
    explicit = getattr(settings, 'FFMPEG_PATH', None)
    if explicit and os.path.isfile(explicit):
        return explicit
    which = shutil.which('ffmpeg')
    if which:
        return which
    windows_locations = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    for path in windows_locations:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        'ffmpeg not found. Set FFMPEG_PATH in .env or install ffmpeg. '
        'Download: https://www.gyan.dev/ffmpeg/builds/'
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def transcode_to_hls(self, lesson_id):
    """
    Transcodes a raw uploaded video into HLS format.

    Works in two modes:
    - Local dev: reads/writes files from/to the local filesystem
    - Production (Supabase Storage): downloads the raw file to a temp
      directory, transcodes, then uploads the HLS segments to Supabase
      Storage and deletes the raw file from storage.
    """
    from apps.courses.models import Lesson

    try:
        ffmpeg = get_ffmpeg()
        lesson = Lesson.objects.get(pk=lesson_id)

        if not lesson.video_file:
            logger.warning(f'Lesson {lesson_id} has no video_file — skipping')
            return

        use_supabase = getattr(settings, 'USE_SUPABASE_STORAGE', False)

        if use_supabase:
            _transcode_supabase(ffmpeg, lesson)
        else:
            _transcode_local(ffmpeg, lesson)

    except FileNotFoundError as exc:
        logger.error(str(exc))
        raise

    except Lesson.DoesNotExist:
        logger.error(f'Lesson {lesson_id} not found')

    except subprocess.CalledProcessError as exc:
        logger.error(
            f'FFmpeg failed for lesson {lesson_id}:\n'
            f'stderr: {exc.stderr.decode(errors="replace")}'
        )
        raise self.retry(exc=exc)


def _transcode_local(ffmpeg, lesson):
    """Local dev: read from disk, write HLS to disk, delete raw file."""
    raw_path = lesson.video_file.path
    out_dir  = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(lesson.id))
    os.makedirs(out_dir, exist_ok=True)

    playlist_path = os.path.join(out_dir, 'index.m3u8')
    segment_tmpl  = os.path.join(out_dir, 'seg%03d.ts')
    hls_time      = str(getattr(settings, 'HLS_SEGMENT_SECONDS', 60))
    preset        = getattr(settings, 'FFMPEG_PRESET', 'ultrafast')

    logger.info(f'[local] Transcoding lesson {lesson.id}: {raw_path}')

    subprocess.run([
        ffmpeg, '-i', raw_path,
        '-c:v', 'libx264', '-crf', '23', '-preset', preset,
        '-c:a', 'aac', '-b:a', '128k',
        '-hls_time', hls_time,
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', segment_tmpl,
        playlist_path, '-y',
    ], check=True, capture_output=True)

    lesson.hls_path  = f'videos/hls/{lesson.id}/index.m3u8'
    lesson.hls_ready = True
    lesson.save(update_fields=['hls_path', 'hls_ready'])

    logger.info(f'[local] Transcode complete for lesson {lesson.id}')

    # Delete raw file — no longer needed
    try:
        if os.path.isfile(raw_path):
            os.remove(raw_path)
            lesson.video_file = None
            lesson.save(update_fields=['video_file'])
            raw_dir = os.path.dirname(raw_path)
            if os.path.isdir(raw_dir) and not os.listdir(raw_dir):
                os.rmdir(raw_dir)
    except OSError as e:
        logger.warning(f'Could not delete raw file: {e}')


def _transcode_supabase(ffmpeg, lesson):
    """
    Production: download raw file from Supabase Storage to a temp dir,
    transcode to HLS, upload all segments back to Supabase Storage,
    then delete the raw file from storage.
    """
    import boto3
    from botocore.client import Config

    s3 = boto3.client(
        's3',
        endpoint_url          = settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        config                = Config(signature_version='s3v4'),
        region_name           = settings.AWS_S3_REGION_NAME,
    )
    bucket   = settings.AWS_STORAGE_BUCKET_NAME
    raw_key  = str(lesson.video_file)   # e.g. "videos/raw/abc.mp4"
    hls_prefix = f'videos/hls/{lesson.id}'

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_local     = os.path.join(tmpdir, 'input.mp4')
        playlist_path = os.path.join(tmpdir, 'index.m3u8')
        segment_tmpl  = os.path.join(tmpdir, 'seg%03d.ts')

        # 1. Download raw file from Supabase Storage
        logger.info(f'[supabase] Downloading s3://{bucket}/{raw_key}')
        s3.download_file(bucket, raw_key, raw_local)

        # 2. Transcode
        hls_time = str(getattr(settings, 'HLS_SEGMENT_SECONDS', 60))
        preset   = getattr(settings, 'FFMPEG_PRESET', 'ultrafast')

        logger.info(f'[supabase] Transcoding lesson {lesson.id}')
        subprocess.run([
            ffmpeg, '-i', raw_local,
            '-c:v', 'libx264', '-crf', '23', '-preset', preset,
            '-c:a', 'aac', '-b:a', '128k',
            '-hls_time', hls_time,
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', segment_tmpl,
            playlist_path, '-y',
        ], check=True, capture_output=True)

        # 3. Upload all HLS files back to Supabase Storage
        for fname in os.listdir(tmpdir):
            if fname.endswith(('.m3u8', '.ts')):
                local_path    = os.path.join(tmpdir, fname)
                storage_key   = f'{hls_prefix}/{fname}'
                content_type  = 'application/vnd.apple.mpegurl' if fname.endswith('.m3u8') else 'video/mp2t'
                logger.info(f'[supabase] Uploading {storage_key}')
                s3.upload_file(
                    local_path, bucket, storage_key,
                    ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'}
                )

    # 4. Update lesson record
    lesson.hls_path  = f'{hls_prefix}/index.m3u8'
    lesson.hls_ready = True
    lesson.save(update_fields=['hls_path', 'hls_ready'])
    logger.info(f'[supabase] Transcode complete for lesson {lesson.id}')

    # 5. Delete raw file from Supabase Storage
    try:
        s3.delete_object(Bucket=bucket, Key=raw_key)
        lesson.video_file = None
        lesson.save(update_fields=['video_file'])
        logger.info(f'[supabase] Deleted raw file {raw_key}')
    except Exception as e:
        logger.warning(f'Could not delete raw file from Supabase: {e}')
