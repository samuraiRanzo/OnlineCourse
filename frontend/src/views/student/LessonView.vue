<template>
  <div class="page-content" v-if="lesson">

    <!--
      Layout:
        Desktop (>900px) — 2-column grid: main viewer + sticky sidebar
        Mobile  (≤900px) — single column, sidebar hidden,
                           replaced by floating "Contents" pill + bottom-sheet drawer
    -->
    <div class="lesson-layout">

      <!-- ── Main viewer ── -->
      <div class="lesson-viewer">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <span :class="['badge',lesson.type==='video'?'badge-black':'badge-orange']">{{
              lesson.type === 'video' ? '🎬 Video' : '📄 Text'
            }}</span>
          <span class="text-muted text-sm">Lesson {{ lessonIndex + 1 }} of {{ course?.lessons?.length }}</span>
        </div>
        <h2 class="display" style="font-size:32px;letter-spacing:.5px;margin-bottom:16px">{{ lesson.title }}</h2>

        <!-- Video -->
        <div v-if="lesson.type==='video'">
          <div v-if="lesson.hls_ready&&lesson.hls_url" class="video-wrap">
            <video ref="videoEl" controls style="width:100%;border-radius:6px;background:#000;display:block"/>
          </div>
          <div v-else-if="lesson.hls_path&&!lesson.hls_ready" class="video-processing">
            <div style="font-size:36px;margin-bottom:8px">⏳</div>
            <div style="font-weight:600;font-size:16px">Video is being processed</div>
            <p class="text-muted text-sm" style="margin-top:6px">Check back in a few minutes.</p>
          </div>
          <div v-else-if="lesson.video_url" class="video-embed">
            <iframe :src="lesson.video_url" allowfullscreen/>
          </div>
          <div v-else class="video-processing">
            <div style="font-size:36px;margin-bottom:8px">🎬</div>
            <p class="text-muted text-sm">No video uploaded yet.</p></div>
          <p v-if="lesson.content" class="lesson-text" style="margin-top:16px">{{ lesson.content }}</p>
        </div>
        <div v-else class="lesson-text" v-html="formatContent(lesson.content)"/>

        <!-- Nav -->
        <div class="lesson-nav">
          <button v-if="prevLesson" class="btn btn-ghost" @click="goLesson(prevLesson.id)">← {{
              prevLesson.title
            }}
          </button>
          <div v-else/>
          <button v-if="nextLesson" class="btn btn-primary" @click="goLesson(nextLesson.id)">Next: {{
              nextLesson.title
            }} →
          </button>
          <button v-else-if="course?.exam&&allDone" class="btn btn-primary"
                  @click="$router.push(`/my-courses/${courseId}/exam`)">Take Exam →
          </button>
          <span v-else class="badge badge-green">✓ Course Complete</span>
        </div>

        <!-- ── Attachments ── -->
        <div v-if="lesson.attachments?.length" class="attachments-block">
          <div class="attachments-title">📎 Lesson Resources</div>
          <div class="attachments-grid">
            <a v-for="a in lesson.attachments" :key="a.id" :href="a.stream_url" target="_blank"
               rel="noopener noreferrer" class="attachment-card">
              <span class="attachment-card-icon">{{ fileIcon(a.extension) }}</span>
              <div class="attachment-card-info">
                <div class="attachment-card-name">{{ a.name }}</div>
                <div class="attachment-card-meta">{{ a.extension?.toUpperCase() }} · {{
                    formatBytes(a.file_size)
                  }}
                </div>
              </div>
              <span class="attachment-card-dl">⬇</span>
            </a>
          </div>
        </div>

        <!-- ── Assignments (students only) ── -->
        <div v-if="auth.isStudent && lessonAssignments.length" class="assignments-section">
          <div class="assignments-title">📋 Assignments</div>
          <div v-for="a in lessonAssignments" :key="a.id" class="assignment-item">
            <div class="assignment-item-header">
              <div style="flex:1;min-width:0">
                <div style="font-size:15px;font-weight:600">{{ a.title }}</div>
                <div class="text-muted text-sm" style="margin-top:2px">
                  Max score: {{ a.max_score }}
                  <span v-if="a.due_date"> · Due {{ formatDateTime(a.due_date) }}</span>
                </div>
              </div>
              <span v-if="a.my_submission?.score !== null && a.my_submission?.score !== undefined"
                    class="badge badge-green">{{ a.my_submission.score }}/{{ a.max_score }}</span>
              <span v-else-if="a.my_submission" class="badge badge-orange">Submitted</span>
              <span v-else class="badge badge-gray">Not submitted</span>
            </div>
            <p v-if="a.description" class="text-muted text-sm"
               style="margin:8px 0 12px;white-space:pre-wrap;line-height:1.6">{{ a.description }}</p>
            <div v-if="a.my_submission?.score !== null && a.my_submission?.score !== undefined"
                 class="submission-grade-block">
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <span class="display" style="font-size:28px"
                      :style="a.my_submission.score>=(a.max_score*0.6)?'color:#25a244':'color:#e53e3e'">{{
                    a.my_submission.score
                  }}/{{ a.max_score }}</span>
                <span class="badge badge-green">Graded ✓</span>
              </div>
              <div v-if="a.my_submission.feedback" class="submission-feedback"><strong>Teacher feedback:</strong>
                {{ a.my_submission.feedback }}
              </div>
            </div>
            <div v-else-if="a.my_submission && resubmitting !== a.id" class="my-submission-preview">
              <div class="text-muted text-sm" style="margin-bottom:8px">✓ Submitted
                {{ formatDate(a.my_submission.updated_at) }} · Awaiting grade
              </div>
              <div v-if="a.my_submission.text_answer" class="submission-text-preview">
                {{ a.my_submission.text_answer.slice(0, 200) }}{{ a.my_submission.text_answer.length > 200 ? '…' : '' }}
              </div>
              <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap">
                <a v-if="a.my_submission.file_url" :href="a.my_submission.file_url" target="_blank"
                   class="btn btn-ghost btn-sm" style="text-decoration:none">⬇ View my file</a>
                <button class="btn btn-ghost btn-sm" @click="resubmitting=a.id">↩ Resubmit</button>
              </div>
            </div>
            <div v-if="!a.my_submission || resubmitting===a.id" class="submit-form">
              <textarea v-model="submitText[a.id]" class="form-control" rows="4"
                        placeholder="Type your answer here (optional if uploading a file)…"
                        style="margin-bottom:8px;resize:vertical;line-height:1.6"/>
              <div class="submit-form-row">
                <label class="attach-btn">
                  <input type="file" style="display:none" @change="e=>submitFile[a.id]=e.target.files?.[0]"/>
                  <span>{{ submitFile[a.id] ? submitFile[a.id].name : '📎 Attach file' }}</span>
                </label>
                <div style="display:flex;gap:6px;align-items:center">
                  <button v-if="resubmitting===a.id" class="btn btn-ghost btn-sm" @click="resubmitting=null">Cancel
                  </button>
                  <button class="btn btn-primary btn-sm"
                          :disabled="submittingId===a.id||(!submitText[a.id]?.trim()&&!submitFile[a.id])"
                          @click="handleSubmit(a)">
                    {{ submittingId === a.id ? 'Submitting…' : a.my_submission ? 'Resubmit' : 'Submit' }}
                  </button>
                </div>
              </div>
              <p v-if="submitFile[a.id]" class="text-muted text-sm" style="margin-top:6px">📎 {{
                  submitFile[a.id].name
                }}</p>
            </div>
          </div>
        </div>

        <!-- ── Personal Notes (students only) ── -->
        <div v-if="auth.isStudent" class="notes-section">
          <div class="notes-header" @click="notesOpen=!notesOpen">
            <div class="display" style="font-size:20px;letter-spacing:.3px">📝 My Notes</div>
            <div style="display:flex;align-items:center;gap:10px">
              <span v-if="noteSaveStatus" class="notes-status"
                    :class="{'notes-status-saving':noteSaveStatus==='Saving…','notes-status-saved':noteSaveStatus==='Saved ✓','notes-status-unsaved':noteSaveStatus==='Unsaved'}">{{
                  noteSaveStatus
                }}</span>
              <span class="notes-chevron" :class="{open:notesOpen}">▼</span>
            </div>
          </div>
          <div v-if="notesOpen" class="notes-body">
            <textarea v-model="noteBody" class="notes-textarea"
                      placeholder="Write private notes for this lesson… only you can see these." rows="6"
                      @input="scheduleNoteSave"/>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
              <span class="text-muted text-sm">Notes are private — only visible to you.</span>
              <button v-if="noteBody.trim()" class="btn btn-ghost btn-sm" @click="handleSaveNoteNow"
                      :disabled="noteSaveStatus==='Saving…'">{{ noteSaveStatus === 'Saving…' ? 'Saving…' : 'Save now' }}
              </button>
            </div>
          </div>
        </div>

        <!-- ── Q&A ── -->
        <div class="qa-section">
          <div class="qa-header">
            <div class="display" style="font-size:22px;letter-spacing:.3px">Questions<span
                v-if="qaStore.questions.length" class="qa-count">{{ qaStore.questions.length }}</span></div>
          </div>
          <div v-if="auth.isStudent" class="qa-compose">
            <textarea v-model="newQuestion" class="qa-textarea" placeholder="Ask a question about this lesson…"
                      rows="3"/>
            <div style="display:flex;justify-content:flex-end;margin-top:8px">
              <button class="btn btn-primary btn-sm" :disabled="!newQuestion.trim()||postingQuestion"
                      @click="handlePostQuestion">{{ postingQuestion ? 'Posting…' : 'Post Question' }}
              </button>
            </div>
          </div>
          <div v-if="qaStore.loading" class="text-muted text-sm" style="padding:16px 0">Loading questions…</div>
          <div v-else-if="!qaStore.questions.length" class="qa-empty"><span style="font-size:28px">💬</span>
            <p class="text-muted text-sm" style="margin-top:8px">No questions yet. Be the first to ask!</p></div>
          <div v-else class="qa-list">
            <div v-for="q in qaStore.questions" :key="q.id" class="qa-question" :class="{resolved:q.is_resolved}">
              <div class="qa-question-header">
                <div class="qa-avatar">{{ q.author_name?.charAt(0).toUpperCase() }}</div>
                <div style="flex:1">
                  <div style="font-size:14px;font-weight:600">{{ q.author_name }}</div>
                  <div class="text-muted text-sm">{{ formatDate(q.created_at) }}</div>
                </div>
                <span v-if="q.is_resolved" class="badge badge-green" style="font-size:10px">✓ Resolved</span>
                <div style="display:flex;gap:6px;flex-shrink:0">
                  <button v-if="auth.isAdmin" class="btn btn-ghost btn-sm" @click="handleToggleResolved(q)">
                    {{ q.is_resolved ? 'Unresolve' : 'Mark Resolved' }}
                  </button>
                  <button v-if="auth.isAdmin||q.author===auth.user?.id" class="btn btn-danger btn-sm"
                          @click="handleDeleteQuestion(q.id)">Delete
                  </button>
                </div>
              </div>
              <div class="qa-question-body">{{ q.body }}</div>
              <div class="qa-answers">
                <div v-for="a in q.answers" :key="a.id" class="qa-answer" :class="{'teacher-answer':a.is_teacher}">
                  <div class="qa-answer-header">
                    <div class="qa-avatar sm" :style="a.is_teacher?'background:var(--lf-black)':''">
                      {{ a.author_name?.charAt(0).toUpperCase() }}
                    </div>
                    <div style="flex:1">
                      <div style="font-size:13px;font-weight:600">{{ a.author_name }}<span v-if="a.is_teacher"
                                                                                           class="badge badge-black"
                                                                                           style="font-size:9px;margin-left:6px">Teacher</span>
                      </div>
                      <div class="text-muted text-sm">{{ formatDate(a.created_at) }}</div>
                    </div>
                    <button v-if="auth.isAdmin||a.author===auth.user?.id" class="btn btn-ghost btn-sm"
                            @click="handleDeleteAnswer(q.id,a.id)">Delete
                    </button>
                  </div>
                  <div class="qa-answer-body">{{ a.body }}</div>
                </div>
                <div class="qa-reply-compose">
                  <textarea v-model="replyText[q.id]" class="qa-textarea sm"
                            :placeholder="auth.isAdmin?'Write your answer…':'Write a reply…'" rows="2"/>
                  <button class="btn btn-secondary btn-sm" style="margin-top:6px" :disabled="!replyText[q.id]?.trim()"
                          @click="handlePostAnswer(q.id)">{{ auth.isAdmin ? '✓ Answer' : '↩ Reply' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Spacer so floating button never covers content on mobile -->
        <div class="mobile-bottom-spacer"/>
      </div>
      <!-- end main viewer -->

      <!-- ── Desktop sidebar (hidden ≤900px) ── -->
      <div class="desktop-sidebar">
        <div class="lf-card" style="padding:0;overflow:hidden;position:sticky;top:90px">
          <div style="padding:16px 18px;border-bottom:1.5px solid var(--lf-gray-200)">
            <strong style="font-size:14px">Course Contents</strong>
          </div>
          <div class="lesson-list" style="border:none;border-radius:0">
            <div v-for="(l,i) in course?.lessons" :key="l.id" class="lesson-item" :class="{active:l.id===lessonId}"
                 @click="goLesson(l.id)">
              <div class="lesson-num" :style="completedIds.includes(l.id)?'background:var(--lf-orange);color:white':''">
                {{ completedIds.includes(l.id) ? '✓' : i + 1 }}
              </div>
              <div class="lesson-item-info">
                <div class="lesson-item-title">{{ l.title }}</div>
                <div class="lesson-item-type">{{ l.type === 'video' ? '🎬 Video' : '📄 Text' }}</div>
              </div>
            </div>
            <div v-if="course?.exam" class="lesson-item" style="cursor:pointer"
                 @click="allDone&&$router.push(`/my-courses/${courseId}/exam`)">
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
    <!-- end lesson-layout -->

    <!-- ═══════════════════════════════════════════════════════════════════════
         MOBILE ONLY — floating Contents button + bottom-sheet drawer
         Both are hidden via CSS on desktop (>900px), shown on mobile (≤900px).
         No Teleport — position:fixed handles stacking without escaping the tree.
         ═══════════════════════════════════════════════════════════════════════ -->

    <!-- Floating pill button -->
    <button class="mobile-fab" @click="sheetOpen = true" aria-label="Open course contents">
      📚 Contents
      <span class="mobile-fab-badge">{{ completedIds.length }}/{{ course?.lessons?.length ?? 0 }}</span>
    </button>

    <!-- Backdrop — click to close -->
    <transition name="fade">
      <div v-if="sheetOpen" class="sheet-backdrop" @click="sheetOpen = false"/>
    </transition>

    <!-- Bottom-sheet drawer -->
    <transition name="slide-up">
      <div v-if="sheetOpen" class="bottom-sheet" role="dialog" aria-modal="true" aria-label="Course contents">

        <!-- Drag handle / close tap area -->
        <div class="sheet-handle-row" @click="sheetOpen = false">
          <div class="sheet-handle-bar"/>
        </div>

        <!-- Sheet header -->
        <div class="sheet-header">
          <div>
            <strong style="font-size:16px">Course Contents</strong>
            <div class="text-muted text-sm" style="margin-top:2px">
              {{ completedIds.length }} of {{ course?.lessons?.length ?? 0 }} lessons done
            </div>
          </div>
          <button class="sheet-close-btn" @click="sheetOpen = false" aria-label="Close">✕</button>
        </div>

        <!-- Overall progress bar -->
        <div style="padding:0 18px 14px">
          <div class="sheet-progress-track">
            <div class="sheet-progress-fill" :style="{ width: (enrollment?.lesson_completion_pct ?? 0) + '%' }"/>
          </div>
          <div style="display:flex;justify-content:flex-end;margin-top:4px">
            <span class="text-muted text-sm">{{ enrollment?.lesson_completion_pct ?? 0 }}%</span>
          </div>
        </div>

        <!-- Scrollable lesson list -->
        <div class="sheet-list">
          <div
              v-for="(l, i) in course?.lessons"
              :key="l.id"
              class="sheet-lesson-item"
              :class="{ active: l.id === lessonId }"
              @click="goLesson(l.id); sheetOpen = false"
          >
            <div class="lesson-num"
                 :style="completedIds.includes(l.id) ? 'background:var(--lf-orange);color:white' : ''">
              {{ completedIds.includes(l.id) ? '✓' : i + 1 }}
            </div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ l.title }}</div>
              <div class="lesson-item-type">{{ l.type === 'video' ? '🎬 Video' : '📄 Text' }}</div>
            </div>
            <span v-if="l.id === lessonId" class="badge badge-orange" style="font-size:10px;flex-shrink:0">Now</span>
          </div>

          <!-- Exam row -->
          <div
              v-if="course?.exam"
              class="sheet-lesson-item"
              :class="{ 'item-locked': !allDone }"
              @click="allDone && ($router.push(`/my-courses/${courseId}/exam`), sheetOpen = false)"
          >
            <div class="lesson-num" style="background:var(--lf-orange);color:white">✍</div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ course.exam?.title ?? 'Exam' }}</div>
              <div class="lesson-item-type">{{ allDone ? 'Ready to take →' : 'Complete all lessons first' }}</div>
            </div>
            <span v-if="!allDone" style="font-size:18px;flex-shrink:0">🔒</span>
          </div>
        </div>

      </div>
    </transition>

  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted, onUnmounted, watch, nextTick} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import {useCoursesStore} from '@/stores/courses'
import {useQaStore} from '@/stores/qa'
import {useNotesStore} from '@/stores/notes'
import {useAssignmentsStore} from '@/stores/assignments'
import {useToast} from 'primevue/usetoast'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const courses = useCoursesStore()
const qaStore = useQaStore()
const notesStore = useNotesStore()
const assignmentsStore = useAssignmentsStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId)
const lessonId = computed(() => route.params.lessonId)

const course = computed(() => courses.current)
const enrollment = computed(() => courses.enrollments.find(e => e.course === courseId.value))
const completedIds = computed(() => enrollment.value?.completed_lesson_ids ?? [])
const lessonIndex = computed(() => course.value?.lessons?.findIndex(l => l.id === lessonId.value) ?? 0)
const lesson = computed(() => course.value?.lessons?.[lessonIndex.value])
const prevLesson = computed(() => lessonIndex.value > 0 ? course.value?.lessons?.[lessonIndex.value - 1] : null)
const nextLesson = computed(() => lessonIndex.value < (course.value?.lessons?.length ?? 0) - 1 ? course.value?.lessons?.[lessonIndex.value + 1] : null)
const allDone = computed(() => course.value?.lessons?.every(l => completedIds.value.includes(l.id)) ?? false)

// ── Mobile bottom-sheet state ─────────────────────────────────────────────────
const sheetOpen = ref(false)

// Close sheet on Escape key
function onKeydown(e) {
  if (e.key === 'Escape') sheetOpen.value = false
}

// Auto-close when navigating to a different lesson
watch(lessonId, () => {
  sheetOpen.value = false
})

// ── Assignments ───────────────────────────────────────────────────────────────
const lessonAssignments = computed(() => assignmentsStore.getByLesson(lessonId.value))
const submitText = reactive({})
const submitFile = reactive({})
const submittingId = ref(null)
const resubmitting = ref(null)

async function handleSubmit(assignment) {
  const text = submitText[assignment.id]
  const file = submitFile[assignment.id]
  if (!text?.trim() && !file) return
  submittingId.value = assignment.id
  try {
    await assignmentsStore.submit(lessonId.value, assignment.id, text, file)
    submitText[assignment.id] = ''
    submitFile[assignment.id] = null
    resubmitting.value = null
    toast.add({severity: 'success', summary: 'Assignment submitted', life: 3000})
  } catch (e) {
    toast.add({severity: 'error', summary: e.response?.data?.detail ?? 'Submission failed.', life: 4000})
  } finally {
    submittingId.value = null
  }
}

// ── hls.js ────────────────────────────────────────────────────────────────────
const videoEl = ref(null)
let hls = null

async function loadHls() {
  await nextTick()
  if (!videoEl.value || !lesson.value?.hls_url) return
  if (hls) {
    hls.destroy();
    hls = null
  }
  const {default: Hls} = await import('hls.js')
  if (Hls.isSupported()) {
    hls = new Hls({
      xhrSetup(xhr) {
        const t = localStorage.getItem('access_token');
        if (t) xhr.setRequestHeader('Authorization', `Bearer ${t}`)
      }
    })
    hls.loadSource(lesson.value.hls_url)
    hls.attachMedia(videoEl.value)
  } else if (videoEl.value.canPlayType('application/vnd.apple.mpegurl')) {
    videoEl.value.src = lesson.value.hls_url
  }
}

watch(() => lesson.value?.id, async (id) => {
  if (id && lesson.value?.hls_ready) await loadHls()
})
watch(() => lesson.value?.hls_ready, async (ready) => {
  if (ready && lesson.value?.hls_url) await loadHls()
})

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  hls?.destroy()
  hls = null
  clearTimeout(noteSaveTimer)
  document.removeEventListener('keydown', onKeydown)
})

function goLesson(id) {
  router.push(`/my-courses/${courseId.value}/lessons/${id}`)
}

function formatContent(text) {
  if (!text) return '<p class="text-muted">No content provided.</p>'
  return text.split('\n').map(line => {
    if (!line.trim()) return '<br>'
    return `<p style="margin-bottom:10px">${line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/`(.*?)`/g, '<code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;font-family:monospace">$1</code>')}</p>`
  }).join('')
}

async function markComplete() {
  if (!enrollment.value || !lesson.value || completedIds.value.includes(lesson.value.id)) return
  await courses.markLessonComplete(enrollment.value.id, lesson.value.id)
  await courses.fetchEnrollments()
}

const ATTACHMENT_ICONS = {
  pdf: '📄',
  doc: '📝',
  docx: '📝',
  ppt: '📊',
  pptx: '📊',
  xls: '📈',
  xlsx: '📈',
  zip: '🗜️',
  txt: '📃',
  csv: '📋',
  mp3: '🎵',
  png: '🖼️',
  jpg: '🖼️',
  jpeg: '🖼️'
}

function fileIcon(ext) {
  return ATTACHMENT_ICONS[ext?.toLowerCase()] ?? '📎'
}

function formatBytes(b) {
  if (!b) return '';
  if (b >= 1073741824) return (b / 1073741824).toFixed(1) + ' GB';
  if (b >= 1048576) return (b / 1048576).toFixed(1) + ' MB';
  if (b >= 1024) return (b / 1024).toFixed(0) + ' KB';
  return b + ' B'
}

// ── Notes ─────────────────────────────────────────────────────────────────────
const notesOpen = ref(true), noteBody = ref(''), noteSaveStatus = ref('')
let noteSaveTimer = null

function scheduleNoteSave() {
  noteSaveStatus.value = 'Unsaved';
  clearTimeout(noteSaveTimer)
  noteSaveTimer = setTimeout(async () => await persistNote(), 1000)
}

async function persistNote() {
  clearTimeout(noteSaveTimer);
  noteSaveTimer = null;
  noteSaveStatus.value = 'Saving…'
  try {
    await notesStore.saveNote(courseId.value, lessonId.value, noteBody.value)
    noteSaveStatus.value = 'Saved ✓'
    setTimeout(() => {
      if (noteSaveStatus.value === 'Saved ✓') noteSaveStatus.value = ''
    }, 2500)
  } catch {
    noteSaveStatus.value = '';
    toast.add({severity: 'error', summary: 'Could not save note', life: 3000})
  }
}

async function handleSaveNoteNow() {
  await persistNote()
}

async function loadNote(lessonId_) {
  if (!auth.isStudent) return
  const note = await notesStore.fetchNote(courseId.value, lessonId_)
  noteBody.value = note?.body ?? '';
  noteSaveStatus.value = ''
}

// ── Q&A ───────────────────────────────────────────────────────────────────────
const newQuestion = ref(''), postingQuestion = ref(false)
const replyText = reactive({})

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDateTime(d) {
  return new Date(d).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function handlePostQuestion() {
  if (!newQuestion.value.trim()) return;
  postingQuestion.value = true
  try {
    await qaStore.postQuestion(courseId.value, lessonId.value, newQuestion.value.trim());
    newQuestion.value = ''
  } catch {
    toast.add({severity: 'error', summary: 'Failed to post question', life: 3000})
  } finally {
    postingQuestion.value = false
  }
}

async function handleDeleteQuestion(qId) {
  if (!confirm('Delete this question?')) return;
  await qaStore.deleteQuestion(courseId.value, lessonId.value, qId)
}

async function handleToggleResolved(q) {
  await qaStore.resolveQuestion(courseId.value, lessonId.value, q.id, !q.is_resolved)
}

async function handlePostAnswer(qId) {
  const t = replyText[qId]?.trim();
  if (!t) return;
  await qaStore.postAnswer(courseId.value, lessonId.value, qId, t);
  replyText[qId] = ''
}

async function handleDeleteAnswer(qId, aId) {
  await qaStore.deleteAnswer(courseId.value, lessonId.value, qId, aId)
}

// ── Lesson navigation watcher ─────────────────────────────────────────────────
watch(lessonId, async (id) => {
  if (!id) return
  clearTimeout(noteSaveTimer);
  noteSaveTimer = null;
  noteSaveStatus.value = ''
  resubmitting.value = null
  await Promise.all([
    loadNote(id),
    markComplete(),
    qaStore.clearQuestions(),
    qaStore.fetchQuestions(courseId.value, id),
    auth.isStudent ? assignmentsStore.fetchByLesson(id) : Promise.resolve(),
  ])
})

onMounted(async () => {
  await courses.fetchCourse(courseId.value)
  await courses.fetchEnrollments()
  await markComplete()
  if (lesson.value?.hls_ready && lesson.value?.hls_url) await loadHls()
  await Promise.all([
    qaStore.fetchQuestions(courseId.value, lessonId.value),
    loadNote(lessonId.value),
    auth.isStudent ? assignmentsStore.fetchByLesson(lessonId.value) : Promise.resolve(),
  ])
})
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.lesson-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.desktop-sidebar {
  display: block;
}

/* hidden in media query */

/* ── Main viewer ── */
.lesson-viewer {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  padding: 32px;
}

.lesson-text {
  line-height: 1.8;
  color: var(--lf-black);
  font-size: 15px;
}

.video-wrap {
  margin-top: 4px;
  background: #000;
  border-radius: 6px;
  overflow: hidden;
  aspect-ratio: 16/9;
}

.video-wrap video {
  width: 100%;
  height: 100%;
}

.video-embed {
  margin-top: 4px;
  background: var(--lf-black);
  border-radius: 6px;
  overflow: hidden;
  aspect-ratio: 16/9;
}

.video-embed iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.video-processing {
  margin-top: 4px;
  background: var(--lf-gray-100);
  border: 1.5px dashed var(--lf-gray-200);
  border-radius: 6px;
  padding: 40px;
  text-align: center;
  aspect-ratio: 16/9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.lesson-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1.5px solid var(--lf-gray-200);
  gap: 8px;
  flex-wrap: wrap;
}

/* ── Shared lesson-list items (sidebar + sheet) ── */
.lesson-list {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
  overflow: hidden;
}

.lesson-item {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--lf-gray-200);
  cursor: pointer;
  transition: background .15s;
}

.lesson-item:last-child {
  border-bottom: none;
}

.lesson-item:hover {
  background: var(--lf-gray-100);
}

.lesson-item.active {
  background: var(--lf-orange-light);
  border-left: 3px solid var(--lf-orange);
}

.lesson-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--lf-gray-200);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  color: var(--lf-gray-600);
}

.lesson-item-info {
  flex: 1;
  min-width: 0;
}

.lesson-item-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lesson-item-type {
  font-size: 12px;
  color: var(--lf-gray-400);
}

/* ── Attachments ── */
.attachments-block {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1.5px solid var(--lf-gray-200);
}

.attachments-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.attachment-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  text-decoration: none;
  color: inherit;
  transition: border-color .15s, background .15s;
}

.attachment-card:hover {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
}

.attachment-card-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.attachment-card-info {
  flex: 1;
  overflow: hidden;
}

.attachment-card-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-card-meta {
  font-size: 11px;
  color: var(--lf-gray-400);
  margin-top: 2px;
}

.attachment-card-dl {
  font-size: 16px;
  color: var(--lf-orange);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity .15s;
}

.attachment-card:hover .attachment-card-dl {
  opacity: 1;
}

/* ── Assignments ── */
.assignments-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1.5px solid var(--lf-gray-200);
}

.assignments-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 16px;
}

.assignment-item {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  padding: 16px 18px;
  margin-bottom: 14px;
}

.assignment-item-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 4px;
}

.submission-grade-block {
  background: #e6f7ee;
  border: 1.5px solid #25a244;
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 12px;
}

.submission-feedback {
  margin-top: 8px;
  font-size: 14px;
  color: var(--lf-gray-600);
  font-style: italic;
}

.my-submission-preview {
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.submission-text-preview {
  font-size: 13px;
  color: var(--lf-gray-600);
  font-style: italic;
  margin-top: 4px;
}

.submit-form {
  margin-top: 8px;
}

.submit-form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.attach-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: var(--lf-radius);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  color: var(--lf-gray-600);
  transition: all .15s;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attach-btn:hover {
  border-color: var(--lf-black);
  color: var(--lf-black);
}

/* ── Notes ── */
.notes-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1.5px solid var(--lf-gray-200);
}

.notes-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
}

.notes-header:hover {
  opacity: .8;
}

.notes-chevron {
  color: var(--lf-gray-400);
  font-size: 12px;
  transition: transform .2s;
}

.notes-chevron.open {
  transform: rotate(180deg);
}

.notes-body {
  margin-top: 12px;
}

.notes-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 2px solid var(--lf-gray-200);
  border-radius: 8px;
  font-family: var(--lf-font-body);
  font-size: 14px;
  line-height: 1.7;
  min-height: 130px;
  resize: vertical;
  outline: none;
  background: var(--lf-gray-100);
  transition: border-color .15s, background .15s;
  color: var(--lf-black);
}

.notes-textarea:focus {
  border-color: var(--lf-orange);
  background: var(--lf-white);
}

.notes-status {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .5px;
}

.notes-status-unsaved {
  color: var(--lf-orange);
}

.notes-status-saving {
  color: var(--lf-gray-400);
}

.notes-status-saved {
  color: #25a244;
}

/* ── Q&A ── */
.qa-section {
  margin-top: 36px;
  padding-top: 28px;
  border-top: 2px solid var(--lf-gray-200);
}

.qa-header {
  margin-bottom: 16px;
}

.qa-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--lf-orange);
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  margin-left: 8px;
  font-family: var(--lf-font-body);
}

.qa-compose {
  background: var(--lf-gray-100);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 20px;
}

.qa-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid var(--lf-gray-200);
  border-radius: 6px;
  font-family: var(--lf-font-body);
  font-size: 14px;
  resize: vertical;
  outline: none;
  background: var(--lf-white);
  transition: border-color .15s;
}

.qa-textarea:focus {
  border-color: var(--lf-orange);
}

.qa-textarea.sm {
  font-size: 13px;
}

.qa-empty {
  text-align: center;
  padding: 28px 0;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.qa-question {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  overflow: hidden;
}

.qa-question.resolved {
  border-color: #25a244;
}

.qa-question-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--lf-gray-100);
  flex-wrap: wrap;
}

.qa-question-body {
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.qa-answers {
  border-top: 1px solid var(--lf-gray-200);
}

.qa-answer {
  padding: 12px 16px;
  border-bottom: 1px solid var(--lf-gray-200);
}

.qa-answer:last-child {
  border-bottom: none;
}

.qa-answer.teacher-answer {
  background: #fffdf8;
  border-left: 3px solid var(--lf-orange);
}

.qa-answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.qa-answer-body {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--lf-gray-600);
  padding-left: 36px;
}

.qa-reply-compose {
  padding: 12px 16px;
  background: var(--lf-gray-100);
}

.qa-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--lf-orange);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.qa-avatar.sm {
  width: 26px;
  height: 26px;
  font-size: 11px;
}

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all .18s;
  white-space: nowrap;
}

.btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--lf-orange);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--lf-orange-dark);
}

.btn-secondary {
  background: var(--lf-black);
  color: #fff;
}

.btn-ghost {
  background: transparent;
  color: var(--lf-gray-600);
  border: 1px solid var(--lf-gray-200);
}

.btn-ghost:hover:not(:disabled) {
  border-color: var(--lf-black);
  color: var(--lf-black);
}

.btn-danger {
  background: #e53e3e;
  color: #fff;
}

.btn-danger:hover:not(:disabled) {
  background: #c53030;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.form-control {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 14px;
  outline: none;
}

.form-control:focus {
  border-color: var(--lf-orange);
}

/* ═══════════════════════════════════════════════════════════════════════════════
   MOBILE — floating FAB + bottom-sheet drawer
   Everything below is hidden on desktop (>900px), visible on mobile (≤900px).
   ═══════════════════════════════════════════════════════════════════════════════ */

/* Spacer prevents FAB from covering last section */
.mobile-bottom-spacer {
  height: 0;
}

/* ── Floating Contents button ── */
.mobile-fab {
  display: none; /* hidden on desktop, shown in media query */
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 110;
  align-items: center;
  gap: 10px;
  padding: 11px 22px;
  background: var(--lf-black);
  color: #fff;
  border: none;
  border-radius: 999px;
  font-family: var(--lf-font-body);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, .35);
  white-space: nowrap;
  transition: transform .15s, box-shadow .15s;
}

.mobile-fab:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, .4);
}

.mobile-fab-badge {
  background: var(--lf-orange);
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 12px;
}

/* ── Backdrop ── */
.sheet-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .5);
  z-index: 120;
}

/* ── Bottom sheet ── */
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 130;
  background: var(--lf-white);
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -8px 40px rgba(0, 0, 0, .15);
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.sheet-handle-row {
  display: flex;
  justify-content: center;
  padding: 12px 0 4px;
  cursor: pointer;
  flex-shrink: 0;
}

.sheet-handle-bar {
  width: 40px;
  height: 4px;
  background: var(--lf-gray-200);
  border-radius: 2px;
}

.sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 4px 18px 14px;
  border-bottom: 1.5px solid var(--lf-gray-200);
  flex-shrink: 0;
}

.sheet-close-btn {
  background: var(--lf-gray-100);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--lf-gray-600);
  flex-shrink: 0;
  margin-top: 2px;
}

.sheet-close-btn:hover {
  background: var(--lf-gray-200);
}

.sheet-progress-track {
  height: 6px;
  background: var(--lf-gray-200);
  border-radius: 3px;
  overflow: hidden;
}

.sheet-progress-fill {
  height: 100%;
  background: var(--lf-orange);
  border-radius: 3px;
  transition: width .4s ease;
}

/* Scrollable lesson list inside sheet */
.sheet-list {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  flex: 1;
}

.sheet-lesson-item {
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--lf-gray-200);
  cursor: pointer;
  transition: background .15s;
}

.sheet-lesson-item:last-child {
  border-bottom: none;
}

.sheet-lesson-item:hover {
  background: var(--lf-gray-100);
}

.sheet-lesson-item.active {
  background: var(--lf-orange-light);
  border-left: 3px solid var(--lf-orange);
}

.sheet-lesson-item.item-locked {
  opacity: .55;
  cursor: not-allowed;
}

/* ── Vue transitions ── */
.fade-enter-active, .fade-leave-active {
  transition: opacity .25s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active {
  transition: transform .3s cubic-bezier(.4, 0, .2, 1);
}

.slide-up-leave-active {
  transition: transform .25s cubic-bezier(.4, 0, .2, 1);
}

.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(100%);
}

/* ── Responsive breakpoint ── */
@media (max-width: 900px) {
  /* Collapse to single column */
  .lesson-layout {
    grid-template-columns: 1fr;
  }

  /* Hide desktop sidebar */
  .desktop-sidebar {
    display: none;
  }

  /* Show FAB */
  .mobile-fab {
    display: flex;
  }

  /* Add space so FAB doesn't overlap last section */
  .mobile-bottom-spacer {
    height: 72px;
  }

  /* Tighter padding on small screens */
  .lesson-viewer {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .lesson-viewer {
    padding: 16px;
  }

  .mobile-fab {
    bottom: 16px;
    font-size: 13px;
    padding: 9px 18px;
  }
}
</style>