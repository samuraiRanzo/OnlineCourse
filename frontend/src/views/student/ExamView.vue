<template>
  <!-- Loading -->
  <div v-if="phase === 'loading'" class="exam-shell">
    <div class="exam-loading">
      <div class="spinner"/>
      <p class="text-muted text-sm" style="margin-top:14px">Preparing your exam…</p>
    </div>
  </div>

  <!-- Error -->
  <div v-else-if="phase === 'error'" class="exam-shell">
    <div class="exam-card" style="text-align:center;padding:48px">
      <div style="font-size:48px;margin-bottom:16px">⚠️</div>
      <h2 class="display" style="font-size:28px;margin-bottom:8px">{{ errorMsg }}</h2>
      <p class="text-muted text-sm" style="margin-bottom:24px">{{ errorDetail }}</p>
      <button class="btn btn-ghost" @click="$router.back()">← Go back</button>
    </div>
  </div>

  <!-- Lobby: student has attempts but can retake, or has never started -->
  <div v-else-if="phase === 'lobby'" class="exam-shell">
    <div class="exam-card exam-lobby">
      <div class="exam-lobby-icon">✍️</div>
      <h1 class="display" style="font-size:36px;letter-spacing:.6px;margin-bottom:6px">{{ exStore.exam?.title }}</h1>
      <p class="text-muted text-sm" style="margin-bottom:28px">{{ course?.title }}</p>

      <div class="exam-meta-grid">
        <div class="exam-meta-item">
          <div class="exam-meta-label">Questions</div>
          <div class="exam-meta-val display">{{ exStore.exam?.questions?.length ?? 0 }}</div>
        </div>
        <div class="exam-meta-item">
          <div class="exam-meta-label">Time Limit</div>
          <div class="exam-meta-val display">
            {{ exStore.exam?.time_limit_minutes ? exStore.exam.time_limit_minutes + ' min' : 'No limit' }}
          </div>
        </div>
        <div class="exam-meta-item">
          <div class="exam-meta-label">Passing Score</div>
          <div class="exam-meta-val display">{{ exStore.exam?.passing_score ?? 60 }}%</div>
        </div>
        <div class="exam-meta-item">
          <div class="exam-meta-label">Attempts Left</div>
          <div class="exam-meta-val display">
            {{ attemptsData?.retakes_remaining ?? (exStore.exam?.max_retakes === 0 ? '∞' : '—') }}
          </div>
        </div>
      </div>

      <!-- Previous result summary (if any) -->
      <div v-if="lastAttempt" class="last-attempt-summary" :class="lastAttempt.passed ? 'passed' : 'failed'">
        <div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">
          Last attempt result
        </div>
        <div class="display" style="font-size:36px">{{ lastAttempt.score }}%</div>
        <span class="badge" :class="lastAttempt.passed ? 'badge-green' : 'badge-red'">
          {{ lastAttempt.passed ? 'Passed ✓' : 'Not Passed' }}
        </span>
        <button class="btn btn-ghost btn-sm" style="margin-left:12px" @click="viewAttemptResults(lastAttempt)">
          View results
        </button>
      </div>

      <div class="exam-lobby-actions">
        <button v-if="canRetake" class="btn btn-primary btn-lg" @click="beginExam">
          {{ lastAttempt ? '↩ Retake Exam' : 'Start Exam →' }}
        </button>
        <p v-else class="text-muted text-sm">No more attempts available.</p>
        <button class="btn btn-ghost" @click="$router.push(`/my-courses/${courseId}`)">← Back to course</button>
      </div>
    </div>
  </div>

  <!-- Taking the exam -->
  <div v-else-if="phase === 'taking'" class="exam-shell taking">
    <!-- Sticky header with timer -->
    <div class="exam-topbar" :class="{ 'timer-warning': timerPercent < 25, 'timer-danger': timerPercent < 10 }">
      <div class="exam-topbar-title display">{{ exStore.exam?.title }}</div>
      <div class="exam-timer-wrap">
        <div v-if="hasTimeLimit" class="exam-timer">
          <svg class="timer-ring" viewBox="0 0 36 36">
            <circle class="timer-ring-bg" cx="18" cy="18" r="15.9"/>
            <circle
                class="timer-ring-fill"
                cx="18" cy="18" r="15.9"
                :stroke-dasharray="`${timerPercent} 100`"
                :class="{ warning: timerPercent < 25, danger: timerPercent < 10 }"
            />
          </svg>
          <span class="timer-text" :class="{ 'text-danger': timerPercent < 10 }">{{ formattedTime }}</span>
        </div>
        <div v-else class="timer-unlimited text-muted text-sm">No time limit</div>
      </div>
      <div class="exam-progress-label text-muted text-sm">
        {{ answeredCount }}/{{ totalQuestions }} answered
      </div>
    </div>

    <!-- Progress bar -->
    <div class="exam-progress-bar">
      <div class="exam-progress-fill" :style="{ width: progressPercent + '%' }"/>
    </div>

    <!-- Questions -->
    <div class="exam-questions">
      <div
          v-for="(q, qi) in exStore.exam?.questions"
          :key="qi"
          class="question-card"
          :class="{
          answered: isAnswered(qi),
          unanswered: !isAnswered(qi) && submitted === false
        }"
      >
        <div class="question-number">
          <span class="q-num-badge">Q{{ qi + 1 }}</span>
          <span class="q-type-tag">{{ q.type === 'mcq' ? 'Multiple Choice' : 'Open Answer' }}</span>
          <span class="q-points text-muted text-sm">{{ pointsPerQ.toFixed(1) }} pts</span>
        </div>
        <div class="question-text">{{ q.text }}</div>

        <!-- MCQ options -->
        <div v-if="q.type === 'mcq'" class="mcq-options">
          <label
              v-for="(opt, oi) in q.options"
              :key="oi"
              class="mcq-option"
              :class="{ selected: answers[qi]?.selected_index === oi }"
          >
            <input
                type="radio"
                :name="`q_${qi}`"
                :value="oi"
                :checked="answers[qi]?.selected_index === oi"
                @change="selectOption(qi, oi)"
            />
            <span class="mcq-option-letter">{{ 'ABCD'[oi] }}</span>
            <span class="mcq-option-text">{{ opt }}</span>
          </label>
        </div>

        <!-- Open answer -->
        <div v-else class="open-answer">
          <textarea
              v-model="openAnswers[qi]"
              class="open-textarea"
              :placeholder="`Type your answer for Q${qi + 1} here…`"
              rows="5"
              @input="markOpenAnswered(qi)"
          />
          <div class="text-muted text-sm" style="margin-top:4px;text-align:right">
            {{ openAnswers[qi]?.length ?? 0 }} chars
          </div>
        </div>
      </div>

      <!-- Submit section -->
      <div class="submit-section">
        <div v-if="unansweredCount > 0" class="unanswered-warning">
          ⚠️ {{ unansweredCount }} question{{ unansweredCount > 1 ? 's' : '' }} not answered.
          You can still submit — unanswered questions score 0.
        </div>
        <div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap">
          <button class="btn btn-ghost" @click="confirmLeave">Save & Exit</button>
          <button class="btn btn-primary btn-lg" :disabled="submitting" @click="handleSubmit(false)">
            {{ submitting ? 'Submitting…' : 'Submit Exam' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Results page -->
  <div v-else-if="phase === 'results'" class="exam-shell">
    <div class="exam-results-wrap">

      <!-- Score hero -->
      <div class="results-hero" :class="viewingAttempt?.passed ? 'hero-passed' : 'hero-failed'">
        <div class="results-score display">{{ viewingAttempt?.score ?? 0 }}%</div>
        <div class="results-status">
          {{ viewingAttempt?.passed ? '✓ Passed' : '✗ Not Passed' }}
        </div>
        <div v-if="viewingAttempt?.auto_submitted" class="auto-submit-notice">
          ⏱ Time expired — exam was auto-submitted
        </div>
        <div class="results-meta text-sm" style="margin-top:12px;opacity:.8">
          Passing score: {{ exStore.exam?.passing_score ?? 60 }}%
          <span v-if="attemptsData?.retakes_remaining !== null && attemptsData?.retakes_remaining !== undefined">
            · {{ attemptsData.retakes_remaining }} retake{{ attemptsData.retakes_remaining === 1 ? '' : 's' }} remaining
          </span>
        </div>
      </div>

      <!-- Open questions pending -->
      <div v-if="viewingAttempt?.open_questions_pending" class="pending-banner">
        ⏳ Some open-answer questions are awaiting teacher review.
        Your score may increase once graded.
      </div>

      <!-- Per-question breakdown -->
      <div class="results-questions">
        <h3 class="display" style="font-size:22px;margin-bottom:16px">Question Breakdown</h3>

        <div
            v-for="r in viewingAttempt?.responses"
            :key="r.id"
            class="result-q-card"
            :class="{
            'result-correct':   r.is_correct === true,
            'result-incorrect': r.is_correct === false,
            'result-pending':   r.is_correct === null
          }"
        >
          <div class="result-q-header">
            <span class="result-q-num">Q{{ r.question_index + 1 }}</span>
            <span class="result-q-type">{{ r.question_type === 'mcq' ? 'MCQ' : 'Open' }}</span>
            <span
                v-if="r.is_correct === true"
                class="result-q-verdict verdict-correct"
            >✓ Correct</span>
            <span
                v-else-if="r.is_correct === false"
                class="result-q-verdict verdict-incorrect"
            >✗ Incorrect</span>
            <span
                v-else
                class="result-q-verdict verdict-pending"
            >⏳ Pending review</span>
            <span class="result-q-pts">
              {{ r.points_earned !== null ? r.points_earned.toFixed(1) : '—' }} / {{ r.max_points.toFixed(1) }} pts
            </span>
          </div>

          <div class="result-q-text">{{ r.question_text }}</div>

          <!-- MCQ: show student's choice + correct answer -->
          <div v-if="r.question_type === 'mcq' && r.options" class="result-mcq-options">
            <div
                v-for="(opt, oi) in r.options"
                :key="oi"
                class="result-mcq-opt"
                :class="{
                'opt-correct':  oi === r.correct_index,
                'opt-wrong':    oi === r.selected_index && oi !== r.correct_index,
                'opt-selected': oi === r.selected_index,
              }"
            >
              <span class="opt-letter">{{ 'ABCD'[oi] }}</span>
              <span class="opt-text">{{ opt }}</span>
              <span v-if="oi === r.correct_index" class="opt-badge correct">✓ Correct</span>
              <span v-if="oi === r.selected_index && oi !== r.correct_index" class="opt-badge wrong">Your answer</span>
              <span v-if="oi === r.selected_index && oi === r.correct_index"
                    class="opt-badge correct">Your answer ✓</span>
            </div>
          </div>

          <!-- Open: student's written answer -->
          <div v-if="r.question_type === 'open'" class="result-open-answer">
            <div class="result-open-label text-muted text-sm">Your answer:</div>
            <div class="result-open-text">
              {{ r.text_answer || '(No answer provided)' }}
            </div>

            <!-- Teacher feedback -->
            <div v-if="r.teacher_feedback" class="result-feedback">
              <div class="result-feedback-label">💬 Teacher feedback:</div>
              <div class="result-feedback-text">{{ r.teacher_feedback }}</div>
            </div>
            <div v-else-if="r.points_earned === null" class="result-feedback-pending">
              Awaiting teacher review…
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="results-actions">
        <button v-if="canRetake" class="btn btn-primary" @click="retakeExam">↩ Retake Exam</button>
        <button class="btn btn-ghost" @click="$router.push(`/my-courses/${courseId}`)">← Back to Course</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted, onUnmounted, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useToast} from 'primevue/usetoast'
import {useAuthStore} from '@/stores/auth'
import {useCoursesStore} from '@/stores/courses'
import {useExamsStore} from '@/stores/exams'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const auth = useAuthStore()
const courses = useCoursesStore()
const exStore = useExamsStore()

const courseId = computed(() => route.params.courseId)
const examId = computed(() => route.params.examId ?? exStore.exam?.id)
const course = computed(() => courses.current)

// ── Phase state machine ───────────────────────────────────────────────────────
// 'loading' | 'error' | 'lobby' | 'taking' | 'results'
const phase = ref('loading')
const errorMsg = ref('')
const errorDetail = ref('')

// ── Timer ─────────────────────────────────────────────────────────────────────
const timeRemaining = ref(0)       // seconds
const totalTimeSeconds = ref(0)
const hasTimeLimit = computed(() => !!exStore.currentAttempt?.time_limit_snapshot)
const timerPercent = computed(() =>
    totalTimeSeconds.value ? (timeRemaining.value / totalTimeSeconds.value) * 100 : 100
)
const formattedTime = computed(() => {
  const m = Math.floor(timeRemaining.value / 60)
  const s = timeRemaining.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})
let timerInterval = null

function startTimer(attempt) {
  const snapshot = attempt.time_limit_snapshot
  if (!snapshot) return

  const startedAt = new Date(attempt.started_at)
  const now = new Date()
  const elapsedSecs = Math.floor((now - startedAt) / 1000)
  const totalSecs = snapshot * 60

  totalTimeSeconds.value = totalSecs
  timeRemaining.value = Math.max(0, totalSecs - elapsedSecs)

  if (timeRemaining.value <= 0) {
    handleSubmit(true)
    return
  }

  timerInterval = setInterval(() => {
    timeRemaining.value--
    if (timeRemaining.value <= 0) {
      clearInterval(timerInterval)
      timerInterval = null
      handleSubmit(true)   // auto-submit
    }
  }, 1000)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null
  }
}

// ── Attempts / results data ───────────────────────────────────────────────────
const attemptsData = ref(null)
const viewingAttempt = ref(null)

const lastAttempt = computed(() => {
  const list = attemptsData.value?.attempts ?? []
  return list.length ? list[0] : null
})

const canRetake = computed(() => {
  const rem = attemptsData.value?.retakes_remaining
  return rem === null || rem === undefined || rem > 0
})

// ── Answer state ──────────────────────────────────────────────────────────────
// answers[qi] = { question_index, selected_index? }
const answers = reactive({})
// openAnswers[qi] = string
const openAnswers = reactive({})
const submitting = ref(false)

const totalQuestions = computed(() => exStore.exam?.questions?.length ?? 0)
const pointsPerQ = computed(() => totalQuestions.value ? 100 / totalQuestions.value : 0)

function isAnswered(qi) {
  const q = exStore.exam?.questions?.[qi]
  if (!q) return false
  if (q.type === 'mcq') return answers[qi]?.selected_index !== undefined
  return (openAnswers[qi]?.trim()?.length ?? 0) > 0
}

const answeredCount = computed(() => {
  const qs = exStore.exam?.questions ?? []
  return qs.filter((_, i) => isAnswered(i)).length
})
const unansweredCount = computed(() => totalQuestions.value - answeredCount.value)
const progressPercent = computed(() =>
    totalQuestions.value ? (answeredCount.value / totalQuestions.value) * 100 : 0
)

function selectOption(qi, optionIndex) {
  answers[qi] = {question_index: qi, selected_index: optionIndex}
}

function markOpenAnswered(qi) {
  // just triggers reactivity — openAnswers[qi] is already v-modeled
}

// ── Build responses payload ───────────────────────────────────────────────────
function buildResponses() {
  const qs = exStore.exam?.questions ?? []
  return qs.map((q, qi) => {
    if (q.type === 'mcq') {
      return {question_index: qi, selected_index: answers[qi]?.selected_index ?? null}
    }
    return {question_index: qi, text_answer: openAnswers[qi] ?? ''}
  })
}

// ── Submit ────────────────────────────────────────────────────────────────────
async function handleSubmit(autoSubmitted = false) {
  if (submitting.value) return
  submitting.value = true
  stopTimer()

  try {
    const attempt = await exStore.submitAttempt(
        exStore.exam.id,
        exStore.currentAttempt.id,
        buildResponses(),
        autoSubmitted,
    )
    viewingAttempt.value = attempt
    // Refresh attempts list so retakes_remaining is current
    attemptsData.value = await exStore.fetchMyAttempts(exStore.exam.id)
    phase.value = 'results'
  } catch (e) {
    toast.add({severity: 'error', summary: e.response?.data?.detail ?? 'Submission failed.', life: 5000})
    submitting.value = false
    phase.value = 'taking'   // let them try again
  }
}

// ── Begin / retake exam ───────────────────────────────────────────────────────
async function beginExam() {
  phase.value = 'loading'
  // Load the student-safe version of the exam (strips correct_index)
  await exStore.fetchExamForStudent(exStore.exam.id)
  const attempt = await exStore.startAttempt(exStore.exam.id)
  startTimer(attempt)
  phase.value = 'taking'
}

async function retakeExam() {
  // Clear previous answers
  Object.keys(answers).forEach(k => delete answers[k])
  Object.keys(openAnswers).forEach(k => delete openAnswers[k])
  await beginExam()
}

function viewAttemptResults(attempt) {
  viewingAttempt.value = attempt
  phase.value = 'results'
}

function confirmLeave() {
  if (confirm('Your progress is saved. You can resume this attempt later.')) {
    stopTimer()
    router.push(`/my-courses/${courseId.value}`)
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    await courses.fetchCourse(courseId.value)

    const examObj = await exStore.fetchExamByCourse(courseId.value)
    if (!examObj) {
      errorMsg.value = 'No exam found'
      errorDetail.value = 'This course does not have an exam yet.'
      phase.value = 'error'
      return
    }

    // Load student's attempt history
    attemptsData.value = await exStore.fetchMyAttempts(examObj.id)

    // Check if there's an in-progress attempt to resume
    const inProgress = attemptsData.value?.attempts?.find?.(a => !a.is_submitted)
    // (The backend /my-attempts/ only returns submitted; /start/ handles in-progress resume)
    // So we just go to lobby. The /start/ endpoint returns in-progress if it exists.

    phase.value = 'lobby'
  } catch (e) {
    const detail = e.response?.data?.detail ?? e.message ?? ''
    errorMsg.value = 'Could not load exam'
    errorDetail.value = detail
    phase.value = 'error'
  }
})

onUnmounted(() => stopTimer())
</script>

<style scoped>
/* ── Shell ── */
.exam-shell {
  min-height: 100vh;
  background: var(--lf-gray-100);
}

.exam-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid var(--lf-gray-200);
  border-top-color: var(--lf-orange);
  animation: spin .7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Lobby ── */
.exam-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 12px;
  max-width: 620px;
  margin: 48px auto;
  padding: 40px;
}

.exam-lobby {
  text-align: center;
}

.exam-lobby-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.exam-meta-grid {
  display: grid;
  grid-template-columns:repeat(4, 1fr);
  gap: 12px;
  margin: 28px 0;
}

.exam-meta-item {
  background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  padding: 14px 10px;
}

.exam-meta-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .7px;
  color: var(--lf-gray-400);
  margin-bottom: 6px;
}

.exam-meta-val {
  font-size: 22px;
}

@media (max-width: 520px) {
  .exam-meta-grid {
    grid-template-columns:repeat(2, 1fr);
  }
}

.last-attempt-summary {
  padding: 16px 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.last-attempt-summary.passed {
  background: #e6f7ee;
  border: 1.5px solid #25a244;
}

.last-attempt-summary.failed {
  background: #fff5f5;
  border: 1.5px solid #e53e3e;
}

.exam-lobby-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 28px;
}

/* ── Topbar (during exam) ── */
.exam-topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--lf-white);
  border-bottom: 1.5px solid var(--lf-gray-200);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: background .3s;
}

.exam-topbar.timer-warning {
  background: #fffdf2;
  border-bottom-color: var(--lf-orange);
}

.exam-topbar.timer-danger {
  background: #fff5f5;
  border-bottom-color: #e53e3e;
  animation: pulse-bg 1s ease-in-out infinite;
}

@keyframes pulse-bg {
  0%, 100% {
    background: #fff5f5;
  }
  50% {
    background: #ffe8e8;
  }
}

.exam-topbar-title {
  flex: 1;
  font-size: 18px;
}

.exam-timer-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.exam-timer {
  display: flex;
  align-items: center;
  gap: 6px;
}

.timer-ring {
  width: 36px;
  height: 36px;
  transform: rotate(-90deg);
}

.timer-ring-bg {
  fill: none;
  stroke: var(--lf-gray-200);
  stroke-width: 3;
}

.timer-ring-fill {
  fill: none;
  stroke: var(--lf-orange);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray .8s linear;
}

.timer-ring-fill.warning {
  stroke: var(--lf-orange);
}

.timer-ring-fill.danger {
  stroke: #e53e3e;
}

.timer-text {
  font-family: var(--lf-font-display);
  font-size: 20px;
  letter-spacing: .5px;
  min-width: 52px;
}

.timer-text.text-danger {
  color: #e53e3e;
}

.timer-unlimited {
  font-size: 13px;
}

.exam-progress-label {
  font-size: 12px;
  flex-shrink: 0;
}

.exam-progress-bar {
  height: 4px;
  background: var(--lf-gray-200);
}

.exam-progress-fill {
  height: 100%;
  background: var(--lf-orange);
  transition: width .3s ease;
}

/* ── Questions ── */
.exam-questions {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.question-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 10px;
  padding: 24px;
  transition: border-color .2s;
}

.question-card.answered {
  border-color: #25a244;
}

.question-number {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.q-num-badge {
  background: var(--lf-black);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
}

.q-type-tag {
  font-size: 11px;
  color: var(--lf-gray-400);
  text-transform: uppercase;
  letter-spacing: .5px;
}

.q-points {
  margin-left: auto;
}

.question-text {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.6;
  margin-bottom: 16px;
}

/* MCQ */
.mcq-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mcq-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 2px solid var(--lf-gray-200);
  border-radius: 8px;
  cursor: pointer;
  transition: all .15s;
}

.mcq-option:hover {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
}

.mcq-option.selected {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
}

.mcq-option input[type="radio"] {
  display: none;
}

.mcq-option-letter {
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
  transition: all .15s;
}

.mcq-option.selected .mcq-option-letter {
  background: var(--lf-orange);
  color: #fff;
}

.mcq-option-text {
  font-size: 14px;
}

/* Open */
.open-answer {
}

.open-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 2px solid var(--lf-gray-200);
  border-radius: 8px;
  font-family: var(--lf-font-body);
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color .15s;
}

.open-textarea:focus {
  border-color: var(--lf-orange);
}

/* Submit section */
.submit-section {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 10px;
  padding: 24px;
  text-align: center;
}

.unanswered-warning {
  background: #fff8e6;
  border: 1.5px solid var(--lf-orange);
  border-radius: 6px;
  padding: 10px 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--lf-orange-dark);
}

/* ── Results ── */
.exam-results-wrap {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
}

.results-hero {
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  margin-bottom: 20px;
}

.results-hero.hero-passed {
  background: linear-gradient(135deg, #e6f7ee, #d4f4e4);
  border: 2px solid #25a244;
}

.results-hero.hero-failed {
  background: linear-gradient(135deg, #fff5f5, #ffe0e0);
  border: 2px solid #e53e3e;
}

.results-score {
  font-size: 72px;
  letter-spacing: 2px;
}

.results-status {
  font-size: 22px;
  font-weight: 700;
  margin-top: 6px;
}

.auto-submit-notice {
  margin-top: 10px;
  font-size: 13px;
  opacity: .7;
  background: rgba(255, 255, 255, .5);
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
}

.pending-banner {
  background: #fff8e6;
  border: 1.5px solid var(--lf-orange);
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 20px;
  font-size: 14px;
  color: var(--lf-orange-dark);
}

.results-questions {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 28px;
}

.result-q-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 10px;
  overflow: hidden;
}

.result-correct {
  border-left: 4px solid #25a244;
}

.result-incorrect {
  border-left: 4px solid #e53e3e;
}

.result-pending {
  border-left: 4px solid var(--lf-orange);
}

.result-q-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  background: var(--lf-gray-100);
  flex-wrap: wrap;
}

.result-q-num {
  font-weight: 700;
  font-size: 13px;
}

.result-q-type {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .5px;
  color: var(--lf-gray-400);
}

.result-q-verdict {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 20px;
}

.verdict-correct {
  background: #e6f7ee;
  color: #25a244;
}

.verdict-incorrect {
  background: #fff5f5;
  color: #e53e3e;
}

.verdict-pending {
  background: #fff8e6;
  color: var(--lf-orange-dark);
}

.result-q-pts {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--lf-gray-600);
}

.result-q-text {
  padding: 14px 18px;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.6;
}

/* MCQ results */
.result-mcq-options {
  padding: 0 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-mcq-opt {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
  font-size: 14px;
}

.result-mcq-opt.opt-correct {
  border-color: #25a244;
  background: #e6f7ee;
}

.result-mcq-opt.opt-wrong {
  border-color: #e53e3e;
  background: #fff5f5;
}

.opt-letter {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--lf-gray-200);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.opt-correct .opt-letter {
  background: #25a244;
  color: #fff;
}

.opt-wrong .opt-letter {
  background: #e53e3e;
  color: #fff;
}

.opt-text {
  flex: 1;
}

.opt-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.opt-badge.correct {
  background: #25a244;
  color: #fff;
}

.opt-badge.wrong {
  background: #e53e3e;
  color: #fff;
}

/* Open results */
.result-open-answer {
  padding: 0 18px 14px;
}

.result-open-label {
  margin-bottom: 4px;
}

.result-open-text {
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  min-height: 48px;
  color: var(--lf-gray-600);
  font-style: italic;
}

.result-feedback {
  margin-top: 10px;
  background: #e6f7ee;
  border: 1.5px solid #25a244;
  border-radius: 6px;
  padding: 12px;
}

.result-feedback-label {
  font-size: 12px;
  font-weight: 700;
  color: #25a244;
  margin-bottom: 4px;
}

.result-feedback-text {
  font-size: 14px;
  line-height: 1.6;
}

.result-feedback-pending {
  margin-top: 10px;
  font-size: 13px;
  color: var(--lf-orange);
  font-style: italic;
}

.results-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  padding-bottom: 32px;
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
  transition: all .15s;
  white-space: nowrap;
  text-decoration: none;
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

.btn-ghost {
  background: transparent;
  color: var(--lf-gray-600);
  border: 1.5px solid var(--lf-gray-200);
}

.btn-ghost:hover:not(:disabled) {
  border-color: var(--lf-black);
  color: var(--lf-black);
}

.btn-lg {
  padding: 14px 32px;
  font-size: 16px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

.badge-green {
  background: #e6f7ee;
  color: #25a244;
}

.badge-red {
  background: #fff5f5;
  color: #e53e3e;
}

.text-muted {
  color: var(--lf-gray-400);
}

.text-sm {
  font-size: 13px;
}
</style>
