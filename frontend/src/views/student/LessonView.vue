<template>
  <div class="page-content" v-if="lesson">
    <div class="lf-content-sidebar">
      <!-- ── Main viewer ── -->
      <div class="lesson-viewer">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <span :class="['badge', lesson.type === 'video' ? 'badge-black' : 'badge-orange']">
            {{ lesson.type === 'video' ? '🎬 Video' : '📄 Text' }}
          </span>
          <span class="text-muted text-sm">Lesson {{ lessonIndex + 1 }} of {{ course?.lessons?.length }}</span>
        </div>
        <h2 class="display" style="font-size:32px;letter-spacing:.5px;margin-bottom:16px">{{ lesson.title }}</h2>

        <!-- Video block -->
        <div v-if="lesson.type === 'video'">
          <div v-if="lesson.hls_ready && lesson.hls_url" class="video-wrap">
            <video ref="videoEl" controls style="width:100%;border-radius:6px;background:#000;display:block" />
          </div>
          <div v-else-if="lesson.hls_path && !lesson.hls_ready" class="video-processing">
            <div style="font-size:36px;margin-bottom:8px">⏳</div>
            <div style="font-weight:600;font-size:16px">Video is being processed</div>
            <p class="text-muted text-sm" style="margin-top:6px">Check back in a few minutes.</p>
          </div>
          <div v-else-if="lesson.video_url" class="video-embed">
            <iframe :src="lesson.video_url" allowfullscreen />
          </div>
          <div v-else class="video-processing">
            <div style="font-size:36px;margin-bottom:8px">🎬</div>
            <p class="text-muted text-sm">No video uploaded yet.</p>
          </div>
          <p v-if="lesson.content" class="lesson-text" style="margin-top:16px">{{ lesson.content }}</p>
        </div>

        <!-- Text lesson -->
        <div v-else class="lesson-text" v-html="formatContent(lesson.content)" />

        <!-- Nav -->
        <div class="lesson-nav">
          <button v-if="prevLesson" class="btn btn-ghost" @click="goLesson(prevLesson.id)">← {{ prevLesson.title }}</button>
          <div v-else />
          <button v-if="nextLesson" class="btn btn-primary" @click="goLesson(nextLesson.id)">Next: {{ nextLesson.title }} →</button>
          <button v-else-if="course?.exam && allDone" class="btn btn-primary" @click="$router.push(`/my-courses/${courseId}/exam`)">Take Exam →</button>
          <span v-else class="badge badge-green">✓ Course Complete</span>
        </div>

        <!-- ── Attachments ── -->
        <div v-if="lesson.attachments?.length" class="attachments-block">
          <div class="attachments-title">📎 Lesson Resources</div>
          <div class="attachments-grid">
            <a
              v-for="a in lesson.attachments"
              :key="a.id"
              :href="a.stream_url"
              target="_blank"
              rel="noopener noreferrer"
              class="attachment-card"
            >
              <span class="attachment-card-icon">{{ fileIcon(a.extension) }}</span>
              <div class="attachment-card-info">
                <div class="attachment-card-name">{{ a.name }}</div>
                <div class="attachment-card-meta">{{ a.extension?.toUpperCase() }} · {{ formatBytes(a.file_size) }}</div>
              </div>
              <span class="attachment-card-dl">⬇</span>
            </a>
          </div>
        </div>

        <!-- ── Q&A ── -->
        <div class="qa-section">
          <div class="qa-header">
            <div class="display" style="font-size:22px;letter-spacing:.3px">
              Questions
              <span v-if="qaStore.questions.length" class="qa-count">{{ qaStore.questions.length }}</span>
            </div>
          </div>

          <!-- Post question — students only -->
          <div v-if="auth.isStudent" class="qa-compose">
            <textarea
              v-model="newQuestion"
              class="qa-textarea"
              placeholder="Ask a question about this lesson…"
              rows="3"
            />
            <div style="display:flex;justify-content:flex-end;margin-top:8px">
              <button
                class="btn btn-primary btn-sm"
                :disabled="!newQuestion.trim() || postingQuestion"
                @click="handlePostQuestion"
              >{{ postingQuestion ? 'Posting…' : 'Post Question' }}</button>
            </div>
          </div>

          <div v-if="qaStore.loading" class="text-muted text-sm" style="padding:16px 0">Loading questions…</div>

          <div v-else-if="!qaStore.questions.length" class="qa-empty">
            <span style="font-size:28px">💬</span>
            <p class="text-muted text-sm" style="margin-top:8px">No questions yet. Be the first to ask!</p>
          </div>

          <div v-else class="qa-list">
            <div
              v-for="q in qaStore.questions"
              :key="q.id"
              class="qa-question"
              :class="{ resolved: q.is_resolved }"
            >
              <!-- Question header -->
              <div class="qa-question-header">
                <div class="qa-avatar">{{ q.author_name?.charAt(0).toUpperCase() }}</div>
                <div style="flex:1">
                  <div style="font-size:14px;font-weight:600">{{ q.author_name }}</div>
                  <div class="text-muted text-sm">{{ formatDate(q.created_at) }}</div>
                </div>
                <span v-if="q.is_resolved" class="badge badge-green" style="font-size:10px">✓ Resolved</span>
                <div style="display:flex;gap:6px;flex-shrink:0">
                  <button
                    v-if="auth.isAdmin"
                    class="btn btn-ghost btn-sm"
                    @click="handleToggleResolved(q)"
                  >{{ q.is_resolved ? 'Unresolve' : 'Mark Resolved' }}</button>
                  <button
                    v-if="auth.isAdmin || q.author === auth.user?.id"
                    class="btn btn-danger btn-sm"
                    @click="handleDeleteQuestion(q.id)"
                  >Delete</button>
                </div>
              </div>

              <!-- Question body -->
              <div class="qa-question-body">{{ q.body }}</div>

              <!-- Answers -->
              <div class="qa-answers">
                <div
                  v-for="a in q.answers" :key="a.id"
                  class="qa-answer"
                  :class="{ 'teacher-answer': a.is_teacher }"
                >
                  <div class="qa-answer-header">
                    <div class="qa-avatar sm" :style="a.is_teacher ? 'background:var(--lf-black)' : ''">
                      {{ a.author_name?.charAt(0).toUpperCase() }}
                    </div>
                    <div style="flex:1">
                      <div style="font-size:13px;font-weight:600">
                        {{ a.author_name }}
                        <span v-if="a.is_teacher" class="badge badge-black" style="font-size:9px;margin-left:6px">Teacher</span>
                      </div>
                      <div class="text-muted text-sm">{{ formatDate(a.created_at) }}</div>
                    </div>
                    <button
                      v-if="auth.isAdmin || a.author === auth.user?.id"
                      class="btn btn-ghost btn-sm"
                      @click="handleDeleteAnswer(q.id, a.id)"
                    >Delete</button>
                  </div>
                  <div class="qa-answer-body">{{ a.body }}</div>
                </div>

                <!-- Reply compose -->
                <div class="qa-reply-compose">
                  <textarea
                    v-model="replyText[q.id]"
                    class="qa-textarea sm"
                    :placeholder="auth.isAdmin ? 'Write your answer…' : 'Write a reply…'"
                    rows="2"
                  />
                  <button
                    class="btn btn-secondary btn-sm"
                    style="margin-top:6px"
                    :disabled="!replyText[q.id]?.trim()"
                    @click="handlePostAnswer(q.id)"
                  >{{ auth.isAdmin ? '✓ Answer' : '↩ Reply' }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- end Q&A -->

      </div>
      <!-- end main viewer -->

      <!-- ── Sidebar ── -->
      <div class="lf-card lf-sticky-card" style="padding:0;overflow:hidden">
        <div style="padding:16px 18px;border-bottom:1.5px solid var(--lf-gray-200)">
          <strong style="font-size:14px">Course Contents</strong>
        </div>
        <div class="lesson-list" style="border:none;border-radius:0">
          <div
            v-for="(l, i) in course?.lessons" :key="l.id"
            class="lesson-item"
            :class="{ active: l.id === lessonId }"
            @click="goLesson(l.id)"
          >
            <div class="lesson-num" :style="completedIds.includes(l.id) ? 'background:var(--lf-orange);color:white' : ''">
              {{ completedIds.includes(l.id) ? '✓' : i + 1 }}
            </div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ l.title }}</div>
              <div class="lesson-item-type">{{ l.type === 'video' ? '🎬 Video' : '📄 Text' }}</div>
            </div>
          </div>
          <div
            v-if="course?.exam"
            class="lesson-item"
            style="cursor:pointer"
            @click="allDone && $router.push(`/my-courses/${courseId}/exam`)"
          >
            <div class="lesson-num" style="background:var(--lf-orange);color:white">✍</div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ course.exam?.title ?? 'Exam' }}</div>
              <div class="lesson-item-type">{{ allDone ? 'Ready to take' : 'Complete all lessons first' }}</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore }    from '@/stores/auth'
import { useCoursesStore } from '@/stores/courses'
import { useQaStore }      from '@/stores/qa'
import { useToast }        from 'primevue/usetoast'

const route   = useRoute()
const router  = useRouter()
const auth    = useAuthStore()
const courses = useCoursesStore()
const qaStore = useQaStore()
const toast   = useToast()

const courseId = computed(() => route.params.courseId)
const lessonId = computed(() => route.params.lessonId)

const course       = computed(() => courses.current)
const enrollment   = computed(() => courses.enrollments.find(e => e.course === courseId.value))
const completedIds = computed(() => enrollment.value?.completed_lesson_ids ?? [])

const lessonIndex = computed(() => course.value?.lessons?.findIndex(l => l.id === lessonId.value) ?? 0)
const lesson      = computed(() => course.value?.lessons?.[lessonIndex.value])
const prevLesson  = computed(() => lessonIndex.value > 0 ? course.value?.lessons?.[lessonIndex.value - 1] : null)
const nextLesson  = computed(() => lessonIndex.value < (course.value?.lessons?.length ?? 0) - 1 ? course.value?.lessons?.[lessonIndex.value + 1] : null)
const allDone     = computed(() => course.value?.lessons?.every(l => completedIds.value.includes(l.id)) ?? false)

// ── hls.js ───────────────────────────────────────────────────────────────
const videoEl = ref(null)
let   hls     = null

async function loadHls() {
  await nextTick()
  if (!videoEl.value || !lesson.value?.hls_url) return
  if (hls) { hls.destroy(); hls = null }
  const url = lesson.value.hls_url
  const { default: Hls } = await import('hls.js')
  if (Hls.isSupported()) {
    hls = new Hls({
      xhrSetup(xhr) {
        const token = localStorage.getItem('access_token')
        if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      },
    })
    hls.loadSource(url)
    hls.attachMedia(videoEl.value)
  } else if (videoEl.value.canPlayType('application/vnd.apple.mpegurl')) {
    videoEl.value.src = url
  }
}

watch(() => lesson.value?.id,        async (id)    => { if (id && lesson.value?.hls_ready)  await loadHls() })
watch(() => lesson.value?.hls_ready,  async (ready) => { if (ready && lesson.value?.hls_url) await loadHls() })
onUnmounted(() => { hls?.destroy(); hls = null })

// ── Navigation ────────────────────────────────────────────────────────────
function goLesson(id) {
  router.push(`/my-courses/${courseId.value}/lessons/${id}`)
}

// ── Text formatting ───────────────────────────────────────────────────────
function formatContent(text) {
  if (!text) return '<p class="text-muted">No content provided.</p>'
  return text.split('\n').map(line => {
    if (line.trim() === '') return '<br>'
    return `<p style="margin-bottom:10px">${line
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.*?)`/g, '<code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;font-family:monospace">$1</code>')
    }</p>`
  }).join('')
}

// ── Lesson completion ─────────────────────────────────────────────────────
async function markComplete() {
  if (!enrollment.value || !lesson.value) return
  if (completedIds.value.includes(lesson.value.id)) return
  await courses.markLessonComplete(enrollment.value.id, lesson.value.id)
  await courses.fetchEnrollments()
}

// ── Attachment helpers ────────────────────────────────────────────────────
const ATTACHMENT_ICONS = {
  pdf: '📄', doc: '📝', docx: '📝', ppt: '📊', pptx: '📊',
  xls: '📈', xlsx: '📈', zip: '🗜️', rar: '🗜️', txt: '📃',
  csv: '📋', mp3: '🎵', png: '🖼️', jpg: '🖼️', jpeg: '🖼️',
}
function fileIcon(ext) {
  return ATTACHMENT_ICONS[ext?.toLowerCase()] ?? '📎'
}
function formatBytes(bytes) {
  if (!bytes) return ''
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
  if (bytes >= 1048576)    return (bytes / 1048576).toFixed(1) + ' MB'
  if (bytes >= 1024)       return (bytes / 1024).toFixed(0) + ' KB'
  return bytes + ' B'
}

// ── Q&A ──────────────────────────────────────────────────────────────────
const newQuestion     = ref('')
const postingQuestion = ref(false)
const replyText       = reactive({})   // { [questionId]: string }

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function handlePostQuestion() {
  if (!newQuestion.value.trim()) return
  postingQuestion.value = true
  try {
    await qaStore.postQuestion(courseId.value, lessonId.value, newQuestion.value.trim())
    newQuestion.value = ''
  } catch {
    toast.add({ severity: 'error', summary: 'Failed to post question', life: 3000 })
  } finally {
    postingQuestion.value = false
  }
}

async function handleDeleteQuestion(questionId) {
  if (!confirm('Delete this question and all its answers?')) return
  try {
    await qaStore.deleteQuestion(courseId.value, lessonId.value, questionId)
  } catch {
    toast.add({ severity: 'error', summary: 'Failed to delete', life: 3000 })
  }
}

async function handleToggleResolved(q) {
  await qaStore.resolveQuestion(courseId.value, lessonId.value, q.id, !q.is_resolved)
}

async function handlePostAnswer(questionId) {
  const text = replyText[questionId]?.trim()
  if (!text) return
  try {
    await qaStore.postAnswer(courseId.value, lessonId.value, questionId, text)
    replyText[questionId] = ''
  } catch {
    toast.add({ severity: 'error', summary: 'Failed to post reply', life: 3000 })
  }
}

async function handleDeleteAnswer(questionId, answerId) {
  await qaStore.deleteAnswer(courseId.value, lessonId.value, questionId, answerId)
}

watch(lessonId, async (id) => {
  if (id) {
    qaStore.clearQuestions()
    await Promise.all([
      markComplete(),
      qaStore.fetchQuestions(courseId.value, id),
    ])
  }
})

onMounted(async () => {
  await courses.fetchCourse(courseId.value)
  await courses.fetchEnrollments()
  await markComplete()
  if (lesson.value?.hls_ready && lesson.value?.hls_url) await loadHls()
  await qaStore.fetchQuestions(courseId.value, lessonId.value)
})
</script>

<style scoped>
/* ── Lesson viewer ── */
.lesson-viewer { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; padding: 16px; }
.lesson-text   { line-height: 1.8; color: var(--lf-black); font-size: 15px; }

.video-wrap  { margin-top: 4px; background: #000; border-radius: 6px; overflow: hidden; aspect-ratio: 16/9; }
.video-wrap video { width: 100%; height: 100%; }
.video-embed { margin-top: 4px; background: var(--lf-black); border-radius: 6px; overflow: hidden; aspect-ratio: 16/9; }
.video-embed iframe { width: 100%; height: 100%; border: none; }
.video-processing {
  margin-top: 4px; background: var(--lf-gray-100); border: 1.5px dashed var(--lf-gray-200);
  border-radius: 6px; padding: 40px; text-align: center; aspect-ratio: 16/9;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}

.lesson-nav { display: flex; justify-content: space-between; align-items: center; margin-top: 28px; padding-top: 20px; border-top: 1.5px solid var(--lf-gray-200); }

/* ── Sidebar ── */
.lesson-list { border: 1.5px solid var(--lf-gray-200); border-radius: 6px; overflow: hidden; }
.lesson-item { padding: 14px 18px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--lf-gray-200); cursor: pointer; transition: background .15s; }
.lesson-item:last-child { border-bottom: none; }
.lesson-item:hover      { background: var(--lf-gray-100); }
.lesson-item.active     { background: var(--lf-orange-light); border-left: 3px solid var(--lf-orange); }
.lesson-num        { width: 28px; height: 28px; border-radius: 50%; background: var(--lf-gray-200); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; color: var(--lf-gray-600); }
.lesson-item-info  { flex: 1; }
.lesson-item-title { font-size: 14px; font-weight: 500; }
.lesson-item-type  { font-size: 12px; color: var(--lf-gray-400); }

/* ── Q&A ── */
.qa-section  { margin-top: 36px; padding-top: 28px; border-top: 2px solid var(--lf-gray-200); }
.qa-header   { margin-bottom: 16px; }
.qa-count    {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; background: var(--lf-orange); color: #fff;
  border-radius: 50%; font-size: 12px; font-weight: 700;
  margin-left: 8px; font-family: var(--lf-font-body);
}
.qa-compose  { background: var(--lf-gray-100); border-radius: 8px; padding: 14px; margin-bottom: 20px; }
.qa-textarea {
  width: 100%; padding: 10px 12px; border: 2px solid var(--lf-gray-200);
  border-radius: 6px; font-family: var(--lf-font-body); font-size: 14px;
  resize: vertical; outline: none; background: var(--lf-white); transition: border-color .15s;
}
.qa-textarea:focus { border-color: var(--lf-orange); }
.qa-textarea.sm    { font-size: 13px; }
.qa-empty    { text-align: center; padding: 28px 0; }
.qa-list     { display: flex; flex-direction: column; gap: 14px; }

.qa-question { border: 1.5px solid var(--lf-gray-200); border-radius: 8px; overflow: hidden; }
.qa-question.resolved { border-color: #25a244; }
.qa-question-header { display: flex; align-items: center; gap: 10px; padding: 14px 16px; background: var(--lf-gray-100); }
.qa-question-body   { padding: 14px 16px; font-size: 14px; line-height: 1.7; white-space: pre-wrap; }

.qa-answers  { border-top: 1px solid var(--lf-gray-200); }
.qa-answer   { padding: 12px 16px; border-bottom: 1px solid var(--lf-gray-200); }
.qa-answer:last-child { border-bottom: none; }
.qa-answer.teacher-answer { background: #fffdf8; border-left: 3px solid var(--lf-orange); }
.qa-answer-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.qa-answer-body   { font-size: 14px; line-height: 1.6; white-space: pre-wrap; color: var(--lf-gray-600); padding-left: 36px; }

.qa-reply-compose { padding: 12px 16px; background: var(--lf-gray-100); }

.qa-avatar {
  width: 32px; height: 32px; border-radius: 50%; background: var(--lf-orange);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.qa-avatar.sm { width: 26px; height: 26px; font-size: 11px; }

/* ── Buttons ── */
.btn { display: inline-flex; align-items: center; gap: 4px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s; white-space: nowrap; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary   { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-secondary { background: var(--lf-black); color: #fff; }
.btn-ghost     { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-danger    { background: #e53e3e; color: #fff; }
.btn-danger:hover { background: #c53030; }
.btn-sm { padding: 6px 12px; font-size: 12px; }

/* ── Attachments block ── */
.attachments-block {
  margin-top: 24px; padding-top: 20px;
  border-top: 1.5px solid var(--lf-gray-200);
}
.attachments-title {
  font-size: 15px; font-weight: 700; margin-bottom: 12px;
  color: var(--lf-black);
}
.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}
.attachment-card {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px;
  background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  text-decoration: none; color: inherit;
  transition: border-color .15s, background .15s;
}
.attachment-card:hover {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
}
.attachment-card-icon { font-size: 22px; flex-shrink: 0; }
.attachment-card-info { flex: 1; overflow: hidden; }
.attachment-card-name {
  font-size: 13px; font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.attachment-card-meta { font-size: 11px; color: var(--lf-gray-400); margin-top: 2px; }
.attachment-card-dl   {
  font-size: 16px; color: var(--lf-orange);
  flex-shrink: 0; opacity: 0; transition: opacity .15s;
}
.attachment-card:hover .attachment-card-dl { opacity: 1; }
</style>