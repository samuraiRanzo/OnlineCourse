<template>
  <div>
    <AppTopbar>
      <template #actions>
        <div style="display:flex;gap:8px;align-items:center">
          <button class="btn btn-ghost btn-sm" @click="$router.push('/courses')">← Back</button>
          <!-- Course publish/unpublish toggle -->
          <div v-if="course" class="course-status-pill" :class="course.status">
            {{ course.status === 'published' ? '✓ Published' : '✎ Draft' }}
          </div>
          <button
            v-if="course"
            class="btn btn-sm"
            :class="course.status === 'published' ? 'btn-ghost' : 'btn-primary'"
            :disabled="togglingCourse"
            @click="handleToggleCourseStatus"
          >
            {{ togglingCourse ? '…' : course.status === 'published' ? 'Unpublish' : '🚀 Publish Course' }}
          </button>
          <button class="btn btn-danger btn-sm" @click="handleDelete">Delete</button>
        </div>
      </template>
    </AppTopbar>

    <div class="page-content" v-if="course">
      <!-- Tabs -->
      <div class="tabs">
        <div v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
          {{ tab.label }}
        </div>
      </div>

      <!-- LESSONS TAB -->
      <div v-if="activeTab === 'lessons'">
        <div class="section-header">
          <div class="section-title">
            Lessons ({{ course.lessons?.length ?? 0 }})
            <span class="text-muted text-sm" style="font-weight:400;margin-left:8px">
              {{ publishedLessonCount }}/{{ course.lessons?.length ?? 0 }} published
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:10px">
            <!-- Save order button — only visible when order has changed -->
            <button
              v-if="orderChanged"
              class="btn btn-secondary btn-sm"
              :disabled="reordering"
              @click="saveOrder"
            >
              {{ reordering ? 'Saving…' : '💾 Save Order' }}
            </button>
            <button class="btn btn-primary btn-sm" @click="showAddLesson = true">+ Add Lesson</button>
          </div>
        </div>

        <EmptyState v-if="!localLessons.length" icon="📝" title="No lessons yet" message="Add your first lesson." />

        <div v-else>
          <p class="text-muted text-sm" style="margin-bottom:10px">
            ☰ Drag rows to reorder — click <strong>Save Order</strong> when done.
          </p>
          <div class="lesson-list">
            <div
              v-for="(l, i) in localLessons"
              :key="l.id"
              class="lesson-item"
              :class="{
                'drag-over':  dragOverId === l.id,
                'dragging':   draggingId === l.id,
              }"
              draggable="true"
              @dragstart="onDragStart($event, l.id)"
              @dragover.prevent="onDragOver($event, l.id)"
              @dragleave="onDragLeave"
              @drop.prevent="onDrop($event, l.id)"
              @dragend="onDragEnd"
            >
              <!-- Drag handle -->
              <div class="drag-handle" title="Drag to reorder">☰</div>

              <div class="lesson-num">{{ i + 1 }}</div>

              <div class="lesson-item-info">
                <div class="lesson-item-title">{{ l.title }}</div>
                <div class="lesson-item-type" style="display:flex;align-items:center;gap:6px">
                  {{ l.type === 'video' ? '🎬 Video' : '📄 Text' }}
                  <span v-if="l.type === 'video' && l.video_file && !l.hls_ready"
                        class="badge badge-orange" style="font-size:10px">⏳ Processing</span>
                  <span v-else-if="l.type === 'video' && l.hls_ready"
                        class="badge badge-green" style="font-size:10px">✓ Ready</span>
                  <span v-else-if="l.type === 'video' && l.video_url"
                        class="badge badge-gray" style="font-size:10px">YouTube</span>
                </div>
              </div>

              <div style="display:flex;gap:6px;align-items:center">
                <!-- Status toggle -->
                <button
                  class="lesson-status-btn"
                  :class="l.status"
                  :disabled="togglingLesson === l.id"
                  @click="handleToggleLessonStatus(l)"
                  :title="l.status === 'published' ? 'Click to unpublish' : 'Click to publish'"
                >
                  {{ togglingLesson === l.id ? '…' : l.status === 'published' ? '✓ Live' : '✎ Draft' }}
                </button>
                <button class="btn btn-ghost btn-sm" @click="openEditLesson(l)">Edit</button>
                <button class="btn btn-danger btn-sm" @click="handleDeleteLesson(l.id)">Del</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- EXAM BUILDER TAB -->
      <div v-if="activeTab === 'exam'">
        <div class="section-header">
          <div class="section-title">Exam Builder</div>
          <button class="btn btn-primary btn-sm" @click="saveExam">💾 Save Exam</button>
        </div>
        <div class="lf-card" style="margin-bottom:20px">
          <FormGroup label="Exam Title">
            <input v-model="examDraft.title" class="form-control" />
          </FormGroup>
          <FormGroup label="Max Retakes">
            <select v-model.number="examDraft.max_retakes" class="form-control">
              <option :value="0">Unlimited</option>
              <option :value="1">1 attempt only (no retakes)</option>
              <option :value="2">2 attempts</option>
              <option :value="3">3 attempts</option>
              <option :value="5">5 attempts</option>
            </select>
            <p class="text-muted text-sm" style="margin-top:4px">
              {{ examDraft.max_retakes === 0 ? 'Students can retake as many times as they want.' : `Students get ${examDraft.max_retakes} attempt(s) total.` }}
            </p>
          </FormGroup>
        </div>
        <div v-for="(q, qi) in examDraft.questions" :key="qi" class="question-builder">
          <div style="display:flex;justify-content:space-between;margin-bottom:12px">
            <strong>Q{{ qi + 1 }} — {{ q.type === 'mcq' ? 'Multiple Choice' : 'Open Answer' }}</strong>
            <button class="btn btn-danger btn-sm" @click="removeQuestion(qi)">Remove</button>
          </div>
          <FormGroup label="Question Text">
            <input v-model="q.text" class="form-control" />
          </FormGroup>
          <div v-if="q.type === 'mcq'">
            <label class="form-label">Options (select correct)</label>
            <div v-for="(opt, oi) in q.options" :key="oi" style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
              <input type="radio" :name="`correct_${qi}`" :checked="q.correct_index === oi" @change="q.correct_index = oi" />
              <input v-model="q.options[oi]" class="form-control" :placeholder="`Option ${oi + 1}`" />
              <button v-if="q.options.length > 2" class="btn btn-ghost btn-sm" @click="q.options.splice(oi, 1)">✕</button>
            </div>
            <button v-if="q.options.length < 6" class="btn btn-ghost btn-sm" @click="q.options.push('')">+ Add Option</button>
          </div>
          <p v-else class="text-muted text-sm">Students type a free-form answer — reviewed manually.</p>
        </div>
        <div style="display:flex;gap:10px;margin-top:8px">
          <button class="btn btn-secondary btn-sm" @click="addQuestion('mcq')">+ Multiple Choice</button>
          <button class="btn btn-outline btn-sm"   @click="addQuestion('open')">+ Open Answer</button>
        </div>
      </div>

      <!-- SESSIONS TAB -->
      <div v-if="activeTab === 'sessions'">
        <div class="section-header">
          <div class="section-title">Sessions ({{ sessions.length }})</div>
          <button class="btn btn-primary btn-sm" @click="showAddSession = true">+ New Session</button>
        </div>
        <EmptyState v-if="!sessions.length" icon="📋" title="No sessions yet" message="Create a session to start tracking attendance." />
        <div v-else>
          <div v-for="s in sessions" :key="s.id" class="session-item">
            <div class="session-date display">{{ formatDate(s.date) }}</div>
            <div class="session-info">
              <div class="session-label">{{ s.label }}</div>
              <div class="session-sub text-muted text-sm">{{ s.attendee_count }} attended · Code: <span class="session-code">{{ s.code }}</span></div>
            </div>
            <button class="btn btn-danger btn-sm" @click="handleDeleteSession(s.id)">Delete</button>
          </div>
        </div>
      </div>

      <!-- ANNOUNCEMENTS TAB -->
      <div v-if="activeTab === 'announcements'">
        <div class="section-header">
          <div class="section-title">Announcements</div>
          <button class="btn btn-primary btn-sm" @click="showAddNotice = true">+ New Notice</button>
        </div>
        <EmptyState v-if="!announcements.length" icon="📣" title="No announcements" message="Post a notice to enrolled students." />
        <div v-for="n in announcements" :key="n.id" class="notice-card" :class="{ pinned: n.pinned }">
          <div class="notice-card-header">
            <span>{{ n.pinned ? '📌' : '📣' }}</span>
            <div style="flex:1">
              <div style="font-weight:600">{{ n.title }}</div>
              <div class="text-muted text-sm">{{ formatDate(n.created_at) }}{{ n.pinned ? ' · Pinned' : '' }}</div>
            </div>
            <div style="display:flex;gap:6px">
              <button class="btn btn-ghost btn-sm" @click="togglePin(n)">{{ n.pinned ? 'Unpin' : 'Pin' }}</button>
              <button class="btn btn-ghost btn-sm" @click="openEditNotice(n)">Edit</button>
              <button class="btn btn-danger btn-sm" @click="handleDeleteNotice(n.id)">Del</button>
            </div>
          </div>
          <div class="notice-card-body text-muted">{{ n.body }}</div>
        </div>
      </div>
    </div>

    <!-- Add / Edit Lesson Modal -->
    <BaseModal v-model="showAddLesson" :title="editLesson ? 'Edit Lesson' : 'Add Lesson'" width="600px">

      <FormGroup label="Title">
        <input v-model="lessonForm.title" class="form-control" placeholder="Lesson title" />
      </FormGroup>

      <FormGroup label="Type">
        <select v-model="lessonForm.type" class="form-control">
          <option value="text">📄 Text</option>
          <option value="video">🎬 Video</option>
        </select>
      </FormGroup>

      <!-- Video source selector -->
      <FormGroup v-if="lessonForm.type === 'video'" label="Video Source">
        <div style="display:flex;gap:0;border:2px solid var(--lf-gray-200);border-radius:var(--lf-radius);overflow:hidden">
          <button
            type="button"
            :style="lessonForm.videoSource === 'upload'
              ? 'flex:1;padding:9px;font-size:13px;font-weight:600;background:var(--lf-black);color:#fff;border:none;cursor:pointer'
              : 'flex:1;padding:9px;font-size:13px;font-weight:600;background:transparent;color:var(--lf-gray-600);border:none;cursor:pointer'"
            @click="lessonForm.videoSource = 'upload'"
          >⬆ Upload File</button>
          <button
            type="button"
            :style="lessonForm.videoSource === 'youtube'
              ? 'flex:1;padding:9px;font-size:13px;font-weight:600;background:var(--lf-black);color:#fff;border:none;cursor:pointer;border-left:2px solid var(--lf-gray-200)'
              : 'flex:1;padding:9px;font-size:13px;font-weight:600;background:transparent;color:var(--lf-gray-600);border:none;cursor:pointer;border-left:2px solid var(--lf-gray-200)'"
            @click="lessonForm.videoSource = 'youtube'"
          >▶ YouTube URL</button>
        </div>
      </FormGroup>

      <!-- Upload file input -->
      <template v-if="lessonForm.type === 'video' && lessonForm.videoSource === 'upload'">
        <FormGroup label="Video File">
          <!-- Drop zone -->
          <div
            class="drop-zone"
            :class="{ 'drop-active': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="onFileDrop"
            @click="$refs.fileInput.click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept="video/*"
              style="display:none"
              @change="onFileSelect"
            />
            <template v-if="!lessonForm.video_file">
              <div style="font-size:32px;margin-bottom:8px">🎬</div>
              <div style="font-weight:600;font-size:14px">Click to choose or drag &amp; drop</div>
              <div class="text-muted text-sm" style="margin-top:4px">MP4, MOV, AVI, MKV — up to 5 GB</div>
            </template>
            <template v-else>
              <div style="font-size:28px;margin-bottom:6px">✅</div>
              <div style="font-weight:600;font-size:14px">{{ lessonForm.video_file.name }}</div>
              <div class="text-muted text-sm" style="margin-top:4px">{{ formatFileSize(lessonForm.video_file.size) }}</div>
              <button
                type="button"
                class="btn btn-ghost btn-sm"
                style="margin-top:10px"
                @click.stop="lessonForm.video_file = null"
              >✕ Remove</button>
            </template>
          </div>
        </FormGroup>

        <!-- Upload progress bar — shown while uploading -->
        <div v-if="uploadProgress > 0 && uploadProgress < 100" style="margin-bottom:16px">
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:13px">
            <span style="font-weight:600">Uploading…</span>
            <span class="text-muted">{{ uploadProgress }}%</span>
          </div>
          <div class="progress-bar" style="height:8px">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }" />
          </div>
        </div>

        <!-- Transcoding info note -->
        <div style="background:var(--lf-orange-light);border:1.5px solid var(--lf-orange);border-radius:6px;padding:12px;margin-bottom:16px;font-size:13px;color:var(--lf-orange-dark)">
          ℹ️ After uploading, the video will be processed in the background (usually 1–5 min per GB).
          The lesson will show a "Processing" state until ready.
        </div>
      </template>

      <!-- YouTube URL input -->
      <FormGroup
        v-if="lessonForm.type === 'video' && lessonForm.videoSource === 'youtube'"
        label="YouTube Embed URL"
      >
        <input
          v-model="lessonForm.video_url"
          class="form-control"
          placeholder="https://www.youtube.com/embed/VIDEO_ID"
        />
        <p class="text-muted text-sm" style="margin-top:4px">
          On YouTube: Share → Embed → copy the src URL from the iframe code.
        </p>
      </FormGroup>

      <FormGroup label="Content / Description">
        <textarea v-model="lessonForm.content" class="form-control" rows="4" placeholder="Lesson notes or description…" />
      </FormGroup>

      <!-- ── Attachments (only shown when editing an existing lesson) ── -->
      <div v-if="editLesson" class="attachments-section">
        <div class="attachments-header">
          <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--lf-gray-600)">
            📎 Attachments
          </span>
          <label class="attach-upload-btn">
            <input
              type="file"
              multiple
              style="display:none"
              @change="handleAttachFiles"
            />
            + Add Files
          </label>
        </div>

        <!-- Uploading progress -->
        <div v-if="attachUploading" class="attach-uploading">
          <div class="attach-spinner" /> Uploading…
        </div>

        <!-- File list -->
        <div v-if="editLesson.attachments?.length" class="attach-list">
          <div
            v-for="a in editLesson.attachments"
            :key="a.id"
            class="attach-item"
          >
            <span class="attach-icon">{{ fileIcon(a.extension) }}</span>
            <div class="attach-info">
              <div class="attach-name">{{ a.name }}</div>
              <div class="attach-size text-muted text-sm">{{ formatBytes(a.file_size) }}</div>
            </div>
            <a
              :href="a.stream_url"
              target="_blank"
              rel="noopener noreferrer"
              class="btn btn-ghost btn-sm"
              style="text-decoration:none"
              title="Open file"
            >↗</a>
            <button
              class="btn btn-danger btn-sm"
              @click="handleDeleteAttachment(a.id)"
            >✕</button>
          </div>
        </div>

        <p v-else-if="!attachUploading" class="text-muted text-sm" style="margin-top:8px;padding:10px;background:var(--lf-gray-100);border-radius:6px;text-align:center">
          No attachments yet — click <strong>+ Add Files</strong> to upload PDFs, slides, docs…
        </p>
      </div>

      <template #footer>
        <button class="btn btn-ghost" @click="closeAddLesson">Cancel</button>
        <button
          class="btn btn-primary"
          :disabled="saving || (uploadProgress > 0 && uploadProgress < 100)"
          @click="handleSaveLesson"
        >
          <span v-if="saving && uploadProgress > 0 && uploadProgress < 100">Uploading {{ uploadProgress }}%…</span>
          <span v-else-if="saving">Saving…</span>
          <span v-else>{{ editLesson ? 'Save Changes' : 'Add Lesson' }}</span>
        </button>
      </template>
    </BaseModal>

    <!-- Add Session Modal -->
    <BaseModal v-model="showAddSession" title="Create Attendance Session">
      <FormGroup label="Session Label"><input v-model="sessionForm.label" class="form-control" placeholder="Week 3 — Monday" /></FormGroup>
      <FormGroup label="Date"><input v-model="sessionForm.date" type="date" class="form-control" /></FormGroup>
      <template #footer>
        <button class="btn btn-ghost" @click="showAddSession = false">Cancel</button>
        <button class="btn btn-primary" @click="handleCreateSession">Create &amp; Generate Code</button>
      </template>
    </BaseModal>

    <!-- Add/Edit Announcement Modal -->
    <BaseModal v-model="showAddNotice" :title="editNotice ? 'Edit Announcement' : 'New Announcement'">
      <FormGroup label="Title"><input v-model="noticeForm.title" class="form-control" /></FormGroup>
      <FormGroup label="Message"><textarea v-model="noticeForm.body" class="form-control" rows="5" /></FormGroup>
      <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
        <input type="checkbox" id="pin-check" v-model="noticeForm.pinned" />
        <label for="pin-check" style="font-size:14px;cursor:pointer">📌 Pin this announcement</label>
      </div>
      <template #footer>
        <button class="btn btn-ghost" @click="showAddNotice = false">Cancel</button>
        <button class="btn btn-primary" @click="handleSaveNotice">{{ editNotice ? 'Save' : 'Post Notice' }}</button>
      </template>
    </BaseModal>

    <!-- New session code display modal -->
    <BaseModal v-model="showCode" title="Session Created — Share this Code">
      <div class="code-box">
        <div class="code-label">Today's Attendance Code</div>
        <div class="code-val">{{ newSessionCode }}</div>
        <div class="text-muted text-sm" style="margin-top:8px">Students enter this code on their Check-In page.</div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showCode = false">Done</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter }    from 'vue-router'
import { useToast }               from 'primevue/usetoast'
import AppTopbar                  from '@/components/layout/AppTopbar.vue'
import BaseModal                  from '@/components/ui/BaseModal.vue'
import FormGroup                  from '@/components/ui/FormGroup.vue'
import EmptyState                 from '@/components/ui/EmptyState.vue'
import { useCoursesStore }        from '@/stores/courses'
import { useAttendanceStore }     from '@/stores/attendance'
import { useAnnouncementsStore }  from '@/stores/announcements'
import { useExamsStore }          from '@/stores/exams'

const route     = useRoute()
const router    = useRouter()
const toast     = useToast()
const courses   = useCoursesStore()
const attStore  = useAttendanceStore()
const annStore  = useAnnouncementsStore()
const exStore   = useExamsStore()

const course    = computed(() => courses.current)
const sessions  = computed(() => attStore.sessions)
const announcements = computed(() => annStore.announcements)

const publishedLessonCount = computed(() =>
  course.value?.lessons?.filter(l => l.status === 'published').length ?? 0
)

const togglingCourse = ref(false)
const togglingLesson = ref(null)

async function handleToggleCourseStatus() {
  if (!course.value) return
  togglingCourse.value = true
  try {
    if (course.value.status === 'published') {
      await courses.unpublishCourse(route.params.id)
      toast.add({ severity: 'info', summary: 'Course moved to draft — students can no longer see it', life: 4000 })
    } else {
      await courses.publishCourse(route.params.id)
      toast.add({ severity: 'success', summary: 'Course is now live for enrolled students', life: 4000 })
    }
  } catch {
    toast.add({ severity: 'error', summary: 'Failed to update course status', life: 3000 })
  } finally {
    togglingCourse.value = false
  }
}

async function handleToggleLessonStatus(lesson) {
  togglingLesson.value = lesson.id
  try {
    if (lesson.status === 'published') {
      await courses.unpublishLesson(route.params.id, lesson.id)
      toast.add({ severity: 'info', summary: `"${lesson.title}" is now a draft`, life: 3000 })
    } else {
      await courses.publishLesson(route.params.id, lesson.id)
      toast.add({ severity: 'success', summary: `"${lesson.title}" is now live`, life: 3000 })
    }
  } catch {
    toast.add({ severity: 'error', summary: 'Failed to update lesson status', life: 3000 })
  } finally {
    togglingLesson.value = null
  }
}

const activeTab = ref('lessons')
const tabs = [
  { key: 'lessons',       label: 'Lessons' },
  { key: 'exam',          label: 'Exam Builder' },
  { key: 'sessions',      label: 'Sessions & Attendance' },
  { key: 'announcements', label: 'Announcements' },
]

// ── Lesson ───────────────────────────────────────────────────
const showAddLesson  = ref(false)
const editLesson     = ref(null)
const saving         = ref(false)
const isDragging     = ref(false)
const fileInput      = ref(null)
const uploadProgress = computed(() => courses.uploadProgress)

// ── Drag-to-reorder state ─────────────────────────────────────
// localLessons is a local copy we mutate during drag so the
// list updates visually before the API call is made.
const localLessons = ref([])
const draggingId   = ref(null)   // id of the row being dragged
const dragOverId   = ref(null)   // id of the row currently hovered over
const reordering   = ref(false)

// Track whether the order has changed from what the server has
const orderChanged = computed(() => {
  if (!course.value?.lessons) return false
  return localLessons.value.some((l, i) => l.id !== course.value.lessons[i]?.id)
})

// Keep localLessons in sync when the course is (re)loaded
watch(
  () => course.value?.lessons,
  (lessons) => {
    if (lessons) localLessons.value = [...lessons]
  },
  { immediate: true }
)

function onDragStart(e, id) {
  draggingId.value = id
  // Required for Firefox — must set data even if unused
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', id)
}

function onDragOver(e, id) {
  if (draggingId.value === id) return
  dragOverId.value = id

  // Reorder localLessons on the fly so the gap animates as you drag
  const from = localLessons.value.findIndex(l => l.id === draggingId.value)
  const to   = localLessons.value.findIndex(l => l.id === id)
  if (from === -1 || to === -1) return
  const reordered = [...localLessons.value]
  const [moved]   = reordered.splice(from, 1)
  reordered.splice(to, 0, moved)
  localLessons.value = reordered
}

function onDragLeave() {
  dragOverId.value = null
}

function onDrop(e, id) {
  dragOverId.value = null
  // The list is already reordered visually — nothing extra needed here
}

function onDragEnd() {
  draggingId.value = null
  dragOverId.value = null
}

async function saveOrder() {
  reordering.value = true
  try {
    const orderedIds = localLessons.value.map(l => l.id)
    await courses.reorderLessons(route.params.id, orderedIds)
    toast.add({ severity: 'success', summary: 'Order saved', life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Failed to save order', life: 3000 })
    // Revert to server order on failure
    localLessons.value = [...(course.value?.lessons ?? [])]
  } finally {
    reordering.value = false
  }
}

const lessonForm = reactive({
  title:       '',
  type:        'text',
  content:     '',
  video_url:   '',
  videoSource: 'upload',  // 'upload' | 'youtube'
  video_file:  null,      // File object when uploading
})

function resetLessonForm() {
  Object.assign(lessonForm, {
    title: '', type: 'text', content: '',
    video_url: '', videoSource: 'upload', video_file: null,
  })
}

function closeAddLesson() {
  showAddLesson.value = false
  editLesson.value    = null
  resetLessonForm()
}

function openEditLesson(l) {
  editLesson.value = l
  Object.assign(lessonForm, {
    title:       l.title,
    type:        l.type,
    content:     l.content ?? '',
    video_url:   l.video_url ?? '',
    videoSource: l.hls_path ? 'upload' : (l.video_url ? 'youtube' : 'upload'),
    video_file:  null,
  })
  showAddLesson.value = true
}

function onFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) lessonForm.video_file = file
}

function onFileDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file && file.type.startsWith('video/')) {
    lessonForm.video_file = file
  } else {
    toast.add({ severity: 'warn', summary: 'Please drop a video file', life: 3000 })
  }
}

function formatFileSize(bytes) {
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
  if (bytes >= 1048576)    return (bytes / 1048576).toFixed(1) + ' MB'
  return (bytes / 1024).toFixed(0) + ' KB'
}

async function handleSaveLesson() {
  if (!lessonForm.title.trim()) {
    toast.add({ severity: 'warn', summary: 'Title is required', life: 3000 })
    return
  }
  saving.value = true
  const id = route.params.id

  // Build payload — include video_file only when a new file is selected
  const payload = {
    title:     lessonForm.title,
    type:      lessonForm.type,
    content:   lessonForm.content,
    video_url: lessonForm.videoSource === 'youtube' ? lessonForm.video_url : '',
  }
  if (lessonForm.type === 'video' && lessonForm.videoSource === 'upload' && lessonForm.video_file) {
    payload.video_file = lessonForm.video_file
  }

  try {
    if (editLesson.value) {
      await courses.updateLesson(id, editLesson.value.id, payload)
      toast.add({ severity: 'success', summary: 'Lesson updated', life: 3000 })
    } else {
      await courses.createLesson(id, payload)
      toast.add({
        severity: 'success',
        summary:  payload.video_file ? 'Lesson saved — video processing…' : 'Lesson added',
        detail:   payload.video_file ? 'The video will be ready in a few minutes.' : '',
        life:     5000,
      })
    }
    closeAddLesson()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Failed to save lesson', life: 4000 })
  } finally {
    saving.value = false
  }
}

async function handleDeleteLesson(lessonId) {
  if (!confirm('Delete this lesson?')) return
  await courses.deleteLesson(route.params.id, lessonId)
  toast.add({ severity: 'info', summary: 'Lesson deleted', life: 3000 })
}

// ── Attachments ──────────────────────────────────────────────
const attachUploading = ref(false)

const ATTACHMENT_ICONS = {
  pdf:  '📄', doc: '📝', docx: '📝',
  ppt:  '📊', pptx: '📊', xls: '📈', xlsx: '📈',
  zip:  '🗜️', rar: '🗜️', mp3: '🎵', mp4: '🎬',
  png:  '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️',
  txt:  '📃', csv: '📋',
}

function fileIcon(ext) {
  return ATTACHMENT_ICONS[ext?.toLowerCase()] ?? '📎'
}

function formatBytes(bytes) {
  if (!bytes) return '—'
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
  if (bytes >= 1048576)    return (bytes / 1048576).toFixed(1) + ' MB'
  if (bytes >= 1024)       return (bytes / 1024).toFixed(0) + ' KB'
  return bytes + ' B'
}

async function handleAttachFiles(e) {
  const files = Array.from(e.target.files ?? [])
  if (!files.length || !editLesson.value) return
  attachUploading.value = true
  try {
    for (const file of files) {
      console.log(file)
      await courses.uploadAttachment(route.params.id, editLesson.value.id, file,file.name)
    }
    // Sync editLesson ref from updated store
    editLesson.value = courses.current?.lessons?.find(l => l.id === editLesson.value.id) ?? editLesson.value
    toast.add({ severity: 'success', summary: `${files.length} file(s) uploaded`, life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Upload failed', life: 3000 })
  } finally {
    attachUploading.value = false
    e.target.value = ''   // reset input so same file can be re-selected
  }
}

async function handleDeleteAttachment(attachmentId) {
  if (!editLesson.value) return
  await courses.deleteAttachment(route.params.id, editLesson.value.id, attachmentId)
  editLesson.value = courses.current?.lessons?.find(l => l.id === editLesson.value.id) ?? editLesson.value
}

// ── Exam ─────────────────────────────────────────────────────
const examDraft = reactive({ title: '', max_retakes: 0, questions: [] })

function addQuestion(type) {
  examDraft.questions.push(
    type === 'mcq'
      ? { type: 'mcq', text: '', options: ['', '', '', ''], correct_index: 0 }
      : { type: 'open', text: '' }
  )
}
function removeQuestion(qi) { examDraft.questions.splice(qi, 1) }

async function saveExam() {
  await exStore.saveExam(route.params.id, { title: examDraft.title, questions: examDraft.questions })
  toast.add({ severity: 'success', summary: 'Exam saved', life: 3000 })
}

// ── Session ──────────────────────────────────────────────────
const showAddSession = ref(false)
const showCode       = ref(false)
const newSessionCode = ref('')
const sessionForm    = reactive({ label: '', date: new Date().toISOString().split('T')[0] })

async function handleCreateSession() {
  const s = await attStore.createSession({ course: route.params.id, ...sessionForm })
  newSessionCode.value = s.code
  showAddSession.value = false
  showCode.value       = true
  Object.assign(sessionForm, { label: '', date: new Date().toISOString().split('T')[0] })
}

async function handleDeleteSession(id) {
  if (!confirm('Delete session?')) return
  await attStore.deleteSession(id)
}

// ── Announcements ─────────────────────────────────────────────
const showAddNotice = ref(false)
const editNotice    = ref(null)
const noticeForm    = reactive({ title: '', body: '', pinned: false })

function openEditNotice(n) {
  editNotice.value = n
  Object.assign(noticeForm, { title: n.title, body: n.body, pinned: n.pinned })
  showAddNotice.value = true
}

async function handleSaveNotice() {
  if (editNotice.value) {
    await annStore.updateAnnouncement(editNotice.value.id, { ...noticeForm })
  } else {
    await annStore.createAnnouncement({ course: route.params.id, ...noticeForm })
  }
  showAddNotice.value = false
  editNotice.value    = null
  Object.assign(noticeForm, { title: '', body: '', pinned: false })
}

async function handleDeleteNotice(id) {
  if (!confirm('Delete this announcement?')) return
  await annStore.deleteAnnouncement(id)
}

async function togglePin(n) {
  await annStore.updateAnnouncement(n.id, { pinned: !n.pinned })
}

// ── Misc ─────────────────────────────────────────────────────
async function handleDelete() {
  if (!confirm('Delete this course?')) return
  await courses.deleteCourse(route.params.id)
  router.push('/courses')
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(async () => {
  const id = route.params.id
  await courses.fetchCourse(id)
  await Promise.all([
    attStore.fetchSessions(id),
    annStore.fetchAnnouncements(id),
    exStore.fetchExamByCourse(id).then(exam => {
      if (exam) Object.assign(examDraft, {
        title:       exam.title,
        max_retakes: exam.max_retakes ?? 0,
        questions:   exam.questions.map(q => ({ ...q })),
      })
      else examDraft.title = courses.current?.title + ' Exam'
    }),
  ])
})
</script>

<style scoped>
.tabs { display: flex; border-bottom: 2px solid var(--lf-gray-200); margin-bottom: 24px; }
.tab  { padding: 10px 20px; font-size: 14px; font-weight: 600; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; color: var(--lf-gray-600); transition: all .15s; }
.tab:hover { color: var(--lf-black); }
.tab.active { color: var(--lf-orange); border-bottom-color: var(--lf-orange); }

/* Course status pill in topbar */
.course-status-pill {
  display: inline-flex; align-items: center; padding: 4px 12px;
  border-radius: 20px; font-size: 12px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .4px;
}
.course-status-pill.draft     { background: var(--lf-gray-200); color: var(--lf-gray-600); }
.course-status-pill.published { background: #e6f7ee; color: #25a244; }

/* Per-lesson status toggle button */
.lesson-status-btn {
  padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700;
  cursor: pointer; border: 1.5px solid; transition: all .15s; white-space: nowrap;
  text-transform: uppercase; letter-spacing: .3px;
}
.lesson-status-btn.draft     { background: var(--lf-gray-100); border-color: var(--lf-gray-200); color: var(--lf-gray-600); }
.lesson-status-btn.draft:hover:not(:disabled) { background: var(--lf-orange-light); border-color: var(--lf-orange); color: var(--lf-orange); }
.lesson-status-btn.published { background: #e6f7ee; border-color: #25a244; color: #25a244; }
.lesson-status-btn.published:hover:not(:disabled) { background: #fff5f5; border-color: #e53e3e; color: #e53e3e; }
.lesson-status-btn:disabled  { opacity: .55; cursor: not-allowed; }
.lesson-list { border: 1.5px solid var(--lf-gray-200); border-radius: 6px; overflow: hidden; }
.lesson-item { padding: 14px 18px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--lf-gray-200); }
.lesson-item:last-child { border-bottom: none; }
.lesson-num  { width: 28px; height: 28px; border-radius: 50%; background: var(--lf-gray-200); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; color: var(--lf-gray-600); }
.lesson-item-info { flex: 1; }
.lesson-item-title { font-size: 14px; font-weight: 500; }
.lesson-item-type  { font-size: 12px; color: var(--lf-gray-400); }
.question-builder  { border: 1.5px solid var(--lf-gray-200); border-radius: 8px; padding: 20px; margin-bottom: 16px; background: var(--lf-gray-100); }
.session-item  { padding: 16px 20px; border: 1.5px solid var(--lf-gray-200); border-radius: 8px; margin-bottom: 12px; background: var(--lf-white); display: flex; align-items: center; gap: 16px; }
.session-date  { font-size: 20px; min-width: 90px; }
.session-info  { flex: 1; }
.session-label { font-size: 15px; font-weight: 600; }
.session-code  { font-family: monospace; font-size: 16px; font-weight: 700; letter-spacing: 3px; color: var(--lf-orange); background: var(--lf-orange-light); padding: 2px 8px; border-radius: 4px; }
.notice-card   { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; overflow: hidden; margin-bottom: 14px; }
.notice-card.pinned { border-color: var(--lf-orange); }
.notice-card-header { padding: 14px 18px; display: flex; align-items: center; gap: 10px; }
.notice-card-body   { padding: 0 18px 14px; font-size: 14px; line-height: 1.7; white-space: pre-wrap; }
.code-box   { background: var(--lf-black); border-radius: 8px; padding: 28px; text-align: center; border: 2px solid var(--lf-orange); }
.code-label { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #aaa; margin-bottom: 10px; }
.code-val   { font-family: var(--lf-font-display); font-size: 56px; color: var(--lf-orange); letter-spacing: 10px; }
.btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; white-space: nowrap; }
.btn:disabled { opacity: .55; }
.btn-primary  { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-secondary { background: var(--lf-black); color: #fff; }
.btn-outline  { background: transparent; color: var(--lf-black); border: 2px solid var(--lf-black); }
.btn-outline:hover { background: var(--lf-black); color: #fff; }
.btn-ghost    { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover  { border-color: var(--lf-black); color: var(--lf-black); }
.btn-danger   { background: #e53e3e; color: #fff; }
.btn-danger:hover { background: #c53030; }
.btn-sm { padding: 6px 14px; font-size: 12px; }
.form-control { width: 100%; padding: 10px 14px; border: 2px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; outline: none; }
.form-control:focus { border-color: var(--lf-orange); }
.form-label { display: block; font-size: 12px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-600); margin-bottom: 6px; }

/* ── Drop zone ── */
.drop-zone {
  border: 2px dashed var(--lf-gray-200); border-radius: 8px;
  padding: 28px 20px; text-align: center; cursor: pointer;
  transition: border-color .2s, background .2s;
  background: var(--lf-gray-100);
}
.drop-zone:hover   { border-color: var(--lf-orange); background: var(--lf-orange-light); }
.drop-zone.drop-active { border-color: var(--lf-orange); background: var(--lf-orange-light); }

/* ── Drag-to-reorder ── */
.drag-handle {
  cursor: grab; color: var(--lf-gray-400); font-size: 16px;
  padding: 0 6px; user-select: none; flex-shrink: 0;
  transition: color .15s;
}
.lesson-item:hover .drag-handle { color: var(--lf-gray-600); }
.lesson-item.dragging { opacity: .4; }
.lesson-item.drag-over { border-top: 2px solid var(--lf-orange); background: var(--lf-orange-light); }

/* ── Attachments panel ── */
.attachments-section {
  margin-top: 20px; padding-top: 16px;
  border-top: 1.5px solid var(--lf-gray-200);
}
.attachments-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.attach-upload-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 14px; border-radius: var(--lf-radius);
  background: var(--lf-black); color: #fff;
  font-size: 12px; font-weight: 600; cursor: pointer;
  transition: background .15s; white-space: nowrap;
}
.attach-upload-btn:hover { background: #333; }
.attach-uploading {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--lf-gray-600); padding: 8px 0;
}
.attach-spinner {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid var(--lf-gray-200);
  border-top-color: var(--lf-orange);
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.attach-list { display: flex; flex-direction: column; gap: 6px; }
.attach-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200); border-radius: 6px;
}
.attach-icon { font-size: 20px; flex-shrink: 0; }
.attach-info { flex: 1; overflow: hidden; }
.attach-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.attach-size { font-size: 11px; }
</style>