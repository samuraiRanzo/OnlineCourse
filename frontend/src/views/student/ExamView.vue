<template>
  <div class="page-content">

    <!-- ── ATTEMPT HISTORY sidebar strip (shown when at least 1 attempt exists) ── -->
    <div v-if="allAttempts.length" class="attempt-bar">
      <span class="text-muted text-sm" style="font-weight:600;margin-right:8px">Attempts:</span>
      <button
        v-for="r in allAttempts" :key="r.id"
        class="attempt-pill"
        :class="{
          active:  reviewingId === r.id,
          passed:  r.score >= 60,
          failed:  r.score < 60,
        }"
        @click="reviewingId = r.id"
      >
        #{{ r.attempt }} — {{ r.score }}%
      </button>
      <button
        v-if="reviewingId && canTakeExam"
        class="attempt-pill active"
        style="margin-left:auto"
        @click="reviewingId = null"
      >
        ✏️ Take new attempt
      </button>
    </div>

    <!-- ── REVIEW a past attempt ── -->
    <div v-if="reviewingResult" class="exam-wrap">
      <div class="exam-result" :style="reviewingResult.score >= 60 ? 'border-color:#25a244' : 'border-color:#e53e3e'">
        <div style="font-size:44px">{{ reviewingResult.score >= 60 ? '🎉' : '📚' }}</div>
        <div class="result-score display" :style="reviewingResult.score >= 60 ? 'color:#25a244' : 'color:#e53e3e'">
          {{ reviewingResult.score }}%
        </div>
        <div class="result-label text-muted">
          Attempt #{{ reviewingResult.attempt }} ·
          {{ reviewingResult.correct }}/{{ reviewingResult.total_mcq }} correct ·
          {{ formatDate(reviewingResult.submitted_at) }}
        </div>
        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:12px">
          <span :class="['badge', reviewingResult.score >= 60 ? 'badge-green' : 'badge-red']">
            {{ reviewingResult.score >= 60 ? 'Passed' : 'Failed' }}
          </span>
          <span v-if="hasCert" class="badge badge-green">🎓 Certificate earned</span>
        </div>

        <!-- Retake or cert CTA -->
        <div style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
          <button v-if="hasCert" class="cert-badge" @click="openCert">
            🎓 View Certificate
          </button>
          <button
            v-if="canTakeExam"
            class="btn btn-primary"
            @click="reviewingId = null"
          >
            ✏️ Take Attempt #{{ nextAttemptNumber }}
          </button>
          <div v-else-if="!canTakeExam && exam" class="badge badge-gray" style="padding:10px 16px">
            Max {{ exam.max_retakes }} attempt(s) reached
          </div>
          <button class="btn btn-secondary" @click="$router.push(`/my-courses/${courseId}`)">
            ← Back to Course
          </button>
        </div>
      </div>

      <!-- Question review -->
      <div style="margin-top:28px">
        <div class="section-title" style="margin-bottom:16px">Answer Review</div>
        <div v-for="(q, qi) in exam?.questions" :key="q.id" class="question-card">
          <div class="question-num">Q{{ qi + 1 }} — {{ q.type === 'mcq' ? 'Multiple Choice' : 'Open Answer' }}</div>
          <div class="question-text">{{ q.text }}</div>

          <div v-if="q.type === 'mcq'" class="option-list">
            <div
              v-for="(opt, oi) in q.options" :key="oi"
              class="option-item"
              :class="{
                correct: oi === q.correct_index,
                wrong:   oi === reviewingResult.answers?.[qi] && oi !== q.correct_index,
              }"
              style="cursor:default"
            >
              <div class="option-radio"
                   :style="oi === reviewingResult.answers?.[qi]
                     ? 'border-color:var(--lf-orange);background:var(--lf-orange)'
                     : ''"
              />
              <span>{{ opt }}</span>
              <span v-if="oi === q.correct_index" style="margin-left:auto;color:#25a244;font-size:13px;font-weight:600">✓ Correct</span>
              <span v-else-if="oi === reviewingResult.answers?.[qi]" style="margin-left:auto;color:#e53e3e;font-size:13px;font-weight:600">✗ Wrong</span>
            </div>
          </div>

          <div v-else style="background:var(--lf-gray-100);border-radius:6px;padding:12px;font-size:14px">
            <strong>Your answer:</strong><br>
            <span style="color:var(--lf-gray-600);font-style:italic">
              {{ reviewingResult.answers?.[qi] || 'No answer provided' }}
            </span>
            <div style="margin-top:8px">
              <span
                v-if="reviewingResult.open_grades?.[qi]"
                :class="['badge', reviewingResult.open_grades[qi] === 'Fail' ? 'badge-red' : 'badge-green']"
              >{{ reviewingResult.open_grades[qi] }}</span>
              <span v-else class="badge badge-gray">Awaiting review by teacher</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── TAKE EXAM (no reviewing, can attempt) ── -->
    <div v-else-if="canTakeExam && exam" class="exam-wrap">
      <div class="exam-header">
        <div>
          <div class="exam-title display">{{ exam.title }}</div>
          <div class="exam-meta text-muted">
            {{ exam.questions?.length }} questions · {{ course?.title }}
            <span v-if="allAttempts.length"> · Attempt #{{ nextAttemptNumber }}</span>
          </div>
        </div>
        <div class="exam-progress">
          <div class="exam-progress-val display">{{ answeredCount }}/{{ exam.questions?.length }}</div>
          <div class="exam-progress-label text-muted">answered</div>
        </div>
      </div>

      <!-- Retake warning banner -->
      <div
        v-if="allAttempts.length"
        style="background:var(--lf-orange-light);border:1.5px solid var(--lf-orange);border-radius:8px;padding:14px 18px;margin-bottom:20px;font-size:14px"
      >
        📋 You are retaking this exam. This will be attempt #{{ nextAttemptNumber }}
        <span v-if="exam.max_retakes > 0"> of {{ exam.max_retakes }} allowed</span>.
        Your previous scores are saved in the history above.
      </div>

      <div v-for="(q, qi) in exam.questions" :key="q.id" class="question-card">
        <div class="question-num">Question {{ qi + 1 }} of {{ exam.questions.length }}</div>
        <div class="question-text">{{ q.text }}</div>

        <div v-if="q.type === 'mcq'" class="option-list">
          <div
            v-for="(opt, oi) in q.options" :key="oi"
            class="option-item"
            :class="{ selected: answers[qi] === oi }"
            @click="answers[qi] = oi"
          >
            <div class="option-radio" />
            <span>{{ opt }}</span>
          </div>
        </div>

        <textarea
          v-else
          class="open-answer"
          placeholder="Type your answer here…"
          :value="answers[qi] ?? ''"
          @input="answers[qi] = $event.target.value"
        />
      </div>

      <div style="text-align:center;padding:20px 0">
        <button
          class="btn btn-primary btn-lg"
          :disabled="submitting"
          @click="submitExam"
        >
          {{ submitting ? 'Submitting…' : `Submit Attempt #${nextAttemptNumber} →` }}
        </button>
        <p class="text-muted text-sm" style="margin-top:8px">
          Answer all multiple choice questions before submitting.
        </p>
      </div>
    </div>

    <!-- ── NO MORE RETAKES and no result selected ── -->
    <div v-else-if="!canTakeExam && allAttempts.length && !reviewingId" class="exam-wrap">
      <div class="exam-result">
        <div style="font-size:48px">🔒</div>
        <div class="display" style="font-size:28px;letter-spacing:.5px;margin-top:8px">No more attempts</div>
        <p class="text-muted" style="margin-top:8px">
          You have used all {{ exam?.max_retakes }} allowed attempt(s) for this exam.
        </p>
        <div style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
          <button v-if="hasCert" class="cert-badge" @click="openCert">🎓 View Certificate</button>
          <button class="btn btn-secondary" @click="$router.push(`/my-courses/${courseId}`)">← Back to Course</button>
        </div>
      </div>
    </div>

    <!-- ── NO EXAM ── -->
    <div v-else-if="!exam && !loading" class="empty-state">
      <span class="empty-icon">📝</span>
      <h3>No exam for this course</h3>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter }    from 'vue-router'
import { useToast }               from 'primevue/usetoast'
import { useAuthStore }           from '@/stores/auth'
import { useCoursesStore }        from '@/stores/courses'
import { useExamsStore }          from '@/stores/exams'
import { useCertificatesStore }   from '@/stores/certificates'

const route   = useRoute()
const router  = useRouter()
const toast   = useToast()
const auth    = useAuthStore()
const courses = useCoursesStore()
const exams   = useExamsStore()
const certs   = useCertificatesStore()

const courseId  = computed(() => route.params.courseId)
const course    = computed(() => courses.current)
const exam      = ref(null)
const loading   = ref(true)
const submitting = ref(false)
const answers   = reactive({})

// Which past attempt the student is reviewing (null = take new exam)
const reviewingId = ref(null)

// All attempts for this course, newest first
const allAttempts = computed(() =>
  exams.getResultsByCourse(courseId.value)
)

const reviewingResult = computed(() =>
  reviewingId.value
    ? allAttempts.value.find(r => r.id === reviewingId.value) ?? null
    : null
)

const nextAttemptNumber = computed(() => allAttempts.value.length + 1)

const canTakeExam = computed(() => {
  if (!exam.value) return false
  const max  = exam.value.max_retakes
  const used = allAttempts.value.length
  if (max === 0) return true        // unlimited
  return used < max
})

const hasCert = computed(() =>
  certs.certificates.some(c => c.course === courseId.value)
)

const answeredCount = computed(() =>
  exam.value?.questions?.filter((q, i) =>
    q.type === 'open'
      ? (answers[i] ?? '').trim() !== ''
      : answers[i] !== undefined
  ).length ?? 0
)

async function submitExam() {
  // Block if all MCQ unanswered
  const mcqIndexes = (exam.value?.questions ?? [])
    .map((q, i) => ({ q, i }))
    .filter(({ q }) => q.type === 'mcq')
  const unanswered = mcqIndexes.filter(({ i }) => answers[i] === undefined)
  if (unanswered.length) {
    toast.add({ severity: 'warn', summary: `Answer all ${unanswered.length} remaining multiple choice question(s)`, life: 3000 })
    return
  }

  submitting.value = true
  try {
    const result = await exams.submitExam(exam.value.id, { ...answers })
    await certs.fetchCertificates()
    // Automatically open the review for the attempt just submitted
    reviewingId.value = result.id
    // Clear answers for a potential future retake
    Object.keys(answers).forEach(k => delete answers[k])
    toast.add({ severity: 'success', summary: `Attempt #${result.attempt} submitted — Score: ${result.score}%`, life: 4000 })
  } catch (e) {
    const detail = e.response?.data?.detail ?? 'Submission failed.'
    toast.add({ severity: 'error', summary: detail, life: 5000 })
  } finally {
    submitting.value = false
  }
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function openCert() {
  const cert    = certs.certificates.find(c => c.course === courseId.value)
  const student = auth.user
  if (!cert || !student || !course.value) return
  const issued = new Date(cert.issued_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/>
  <title>Certificate</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet"/>
  <style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5}
  .cert{background:#fff;max-width:640px;width:100%;padding:56px;text-align:center;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.1);position:relative}
  .cert::before{content:'';position:absolute;top:0;left:0;right:0;height:6px;background:#FF6B00}
  .logo{font-family:'Bebas Neue',sans-serif;font-size:24pt;letter-spacing:3px;margin-bottom:24px}.logo span{color:#FF6B00}
  .name{font-family:'Bebas Neue',sans-serif;font-size:40pt;letter-spacing:3px;border-bottom:3px solid #FF6B00;padding-bottom:16px;margin-bottom:20px}
  .course{font-family:'Bebas Neue',sans-serif;font-size:20pt;color:#FF6B00;margin-bottom:20px}
  .meta{font-size:10pt;color:#aaa;text-transform:uppercase;letter-spacing:.8px}.meta span{color:#0a0a0a;font-weight:600}
  .no-print{margin-top:24px}@media print{.no-print{display:none}}</style></head>
  <body><div class="cert">
  <div class="logo">LEARN<span>FORGE</span></div>
  <p style="color:#aaa;font-size:10pt;margin-bottom:8px;text-transform:uppercase;letter-spacing:2px">This certificate is presented to</p>
  <div class="name">${student.name}</div>
  <p style="color:#555;margin-bottom:8px">for successfully completing</p>
  <div class="course">${course.value.title}</div>
  <div class="meta"><p>Issued: <span>${issued}</span></p><p style="margin-top:4px">Certificate ID: <span>${cert.cert_code}</span></p></div>
  <div class="no-print"><button onclick="window.print()" style="padding:10px 28px;background:#FF6B00;color:#fff;border:none;border-radius:4px;font-weight:600;cursor:pointer">🖨 Print / Save PDF</button></div>
  </div></body></html>`
  window.open(URL.createObjectURL(new Blob([html], { type: 'text/html' })), '_blank')
}

onMounted(async () => {
  await Promise.all([
    courses.fetchCourse(courseId.value),
    exams.fetchResults(),
    certs.fetchCertificates(),
  ])
  exam.value  = await exams.fetchExamByCourse(courseId.value)
  loading.value = false

  // Auto-open the latest attempt for review if the student has already taken it
  // but can still retake — lets them see their last score before deciding
  if (allAttempts.value.length && canTakeExam.value) {
    reviewingId.value = allAttempts.value[0].id
  } else if (allAttempts.value.length) {
    reviewingId.value = allAttempts.value[0].id
  }
})
</script>

<style scoped>
.attempt-bar {
  display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  background: var(--lf-white); border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px; padding: 12px 18px; margin-bottom: 20px;
}
.attempt-pill {
  padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;
  cursor: pointer; border: 1.5px solid var(--lf-gray-200);
  background: var(--lf-gray-100); color: var(--lf-gray-600); transition: all .15s;
}
.attempt-pill:hover  { border-color: var(--lf-black); color: var(--lf-black); }
.attempt-pill.active { border-color: var(--lf-black); background: var(--lf-black); color: #fff; }
.attempt-pill.passed { border-color: #25a244; color: #25a244; background: #e6f7ee; }
.attempt-pill.passed.active { background: #25a244; color: #fff; }
.attempt-pill.failed { border-color: #e53e3e; color: #e53e3e; background: #fff5f5; }
.attempt-pill.failed.active { background: #e53e3e; color: #fff; }

.exam-wrap    { max-width: 680px; }
.exam-header  {
  background: var(--lf-black); color: #fff; border-radius: 8px;
  padding: 28px; margin-bottom: 24px;
  display: flex; justify-content: space-between; align-items: center;
}
.exam-title    { font-size: 30px; letter-spacing: .5px; }
.exam-meta     { font-size: 13px; margin-top: 4px; color: #888; }
.exam-progress { text-align: right; }
.exam-progress-val   { font-size: 36px; color: var(--lf-orange); line-height: 1; }
.exam-progress-label { font-size: 12px; color: #888; }

.question-card { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; padding: 24px; margin-bottom: 16px; }
.question-num  { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .8px; color: var(--lf-orange); margin-bottom: 8px; }
.question-text { font-size: 16px; font-weight: 500; line-height: 1.5; margin-bottom: 18px; }
.option-list   { display: flex; flex-direction: column; gap: 10px; }
.option-item   { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 2px solid var(--lf-gray-200); border-radius: 6px; cursor: pointer; transition: all .15s; user-select: none; }
.option-item:hover   { border-color: var(--lf-orange); background: var(--lf-orange-light); }
.option-item.selected { border-color: var(--lf-orange); background: var(--lf-orange-light); }
.option-item.correct  { border-color: #25a244; background: #e6f7ee; cursor: default; }
.option-item.wrong    { border-color: #e53e3e; background: #fff5f5; cursor: default; }
.option-radio { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--lf-gray-200); flex-shrink: 0; }
.option-item.selected .option-radio { border-color: var(--lf-orange); background: var(--lf-orange); }
.open-answer  { width: 100%; padding: 12px 14px; border: 2px solid var(--lf-gray-200); border-radius: 6px; font-family: var(--lf-font-body); font-size: 14px; min-height: 100px; resize: vertical; outline: none; transition: border-color .15s; }
.open-answer:focus { border-color: var(--lf-orange); }

.exam-result  { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; padding: 40px; text-align: center; }
.result-score { font-size: 72px; line-height: 1; }
.result-label { font-size: 14px; margin-top: 6px; }

.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary   { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-secondary { background: var(--lf-black); color: #fff; }
.btn-lg { padding: 14px 32px; font-size: 16px; }
</style>
