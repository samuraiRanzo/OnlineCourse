<template>
  <div class="page-content" v-if="student">
    <div style="display:flex;gap:8px;margin-bottom:20px">
      <button class="btn btn-ghost btn-sm" @click="$router.push('/reports')">← All Reports</button>
      <button class="btn btn-primary btn-sm" @click="printReport">🖨️ Print Report</button>
    </div>

    <!-- Profile header -->
    <div class="lf-card" style="margin-bottom:24px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">
        <div style="display:flex;align-items:center;gap:16px">
          <div class="big-avatar">{{ student.name.charAt(0) }}</div>
          <div>
            <div class="display" style="font-size:28px;letter-spacing:.5px">{{ student.name }}</div>
            <div class="text-muted text-sm">{{ student.email }}</div>
            <span :class="['type-pill', `type-${student.student_type}`]"
                  style="margin-top:4px;display:inline-flex">
              {{ student.student_type === 'online' ? '💻 Online' : '🏫 On-site' }}
            </span>
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <div class="kpi">
            <div class="kpi-val">{{ enrollments.length }}</div>
            <div class="kpi-label">Courses</div>
          </div>
          <!-- totalAttempts replaces the deleted results.length -->
          <div class="kpi">
            <div class="kpi-val">{{ totalAttempts }}</div>
            <div class="kpi-label">Attempts</div>
          </div>
          <div class="kpi">
            <div class="kpi-val" :style="certs.length ? 'color:#25a244' : ''">
              {{ certs.length }}
            </div>
            <div class="kpi-label">Certs</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading state while per-course data fetches -->
    <div v-if="courseDataLoading"
         style="text-align:center;padding:48px;color:var(--lf-gray-400);font-size:14px">
      <div class="spinner" style="margin:0 auto 12px"/>
      Loading course data…
    </div>

    <!-- Per-course cards -->
    <div v-else v-for="e in enrichedEnrollments" :key="e.id" class="lf-card"
         style="margin-bottom:20px">
      <!-- Course heading -->
      <div style="display:flex;align-items:center;justify-content:space-between;
                  margin-bottom:16px;flex-wrap:wrap;gap:10px">
        <div>
          <div class="display" style="font-size:22px;letter-spacing:.4px">
            {{ e.course.title }}
          </div>
          <div v-if="e.risks.length" class="risk-flag">
            ⚠ {{ e.risks.join(' · ') }}
          </div>
        </div>
        <button v-if="e.cert" class="cert-badge" @click="openCert(e.cert, e.course)">
          🎓 View Certificate
        </button>
      </div>

      <div class="lf-col-2">

        <!-- ── LEFT: lessons or attendance ─────────────────────────────────── -->
        <div>
          <div class="report-section-title">
            {{ student.student_type === 'online' ? 'Lesson Progress' : 'Attendance' }}
          </div>

          <!-- Online: lesson completion -->
          <template v-if="student.student_type === 'online'">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="text-muted text-sm">Completed</span>
              <span class="text-sm font-600">
                {{ e.enrollment.completed_lesson_ids?.length ?? 0 }}/{{ e.course.lessons?.length ?? 0 }}
                ({{ e.enrollment.lesson_completion_pct ?? 0 }}%)
              </span>
            </div>
            <div class="progress-bar" style="height:8px">
              <div class="progress-fill"
                   :style="{ width: (e.enrollment.lesson_completion_pct ?? 0) + '%' }"/>
            </div>
            <div style="margin-top:12px">
              <div v-for="l in e.course.lessons" :key="l.id"
                   style="display:flex;align-items:center;gap:8px;padding:5px 0;
                          border-bottom:1px solid var(--lf-gray-200);font-size:13px">
                <span :style="e.enrollment.completed_lesson_ids?.includes(l.id)
                  ? 'color:#25a244' : 'color:var(--lf-gray-400)'">
                  {{ e.enrollment.completed_lesson_ids?.includes(l.id) ? '✓' : '○' }}
                </span>
                <span>{{ l.title }}</span>
                <span class="badge badge-gray" style="margin-left:auto">{{ l.type }}</span>
              </div>
            </div>
          </template>

          <!-- Onsite: attendance -->
          <template v-else>
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="text-muted text-sm">Sessions attended</span>
              <span :class="attClass(e.attStats.pct)" style="font-size:14px">
                {{ e.attStats.pct }}% ({{ e.attStats.attended }}/{{ e.attStats.total }})
              </span>
            </div>
            <div class="progress-bar" style="height:8px">
              <div class="progress-fill" :style="{ width: e.attStats.pct + '%' }"/>
            </div>
            <div style="font-size:12px;color:var(--lf-gray-600);margin-top:6px">
              Threshold: <strong>{{ e.course.attendance_threshold }}%</strong>
            </div>
          </template>
        </div>

        <!-- ── RIGHT: exam results ──────────────────────────────────────────── -->
        <div>
          <div class="report-section-title">Exam Results</div>

          <!-- No attempt yet -->
          <div v-if="!e.bestAttempt"
               style="background:var(--lf-gray-100);border-radius:6px;padding:16px;
                      text-align:center;color:var(--lf-gray-600);font-size:14px">
            Exam not taken yet.
          </div>

          <template v-else>
            <!--
              Score hero — uses ExamAttempt.score (% out of 100).
              Old: e.result.score from ExamResult model.
              New: e.bestAttempt.score from ExamAttempt model.
              passing_score comes from the exam config, not hardcoded 60.
            -->
            <div :style="`background:${e.bestAttempt.score >= e.passingScore
                ? '#e6f7ee' : '#fff5f5'};
                border-radius:6px;padding:16px;text-align:center;margin-bottom:12px`">
              <div class="display"
                   :style="`font-size:48px;color:${e.bestAttempt.score >= e.passingScore
                     ? '#25a244' : '#e53e3e'}`">
                {{ e.bestAttempt.score }}%
              </div>
              <div class="text-muted text-sm" style="margin-bottom:6px">
                Attempt {{ e.attemptCount }} of {{ e.maxRetakes === 0 ? '∞' : e.maxRetakes }}
                · {{ formatDate(e.bestAttempt.submitted_at) }}
                <span v-if="e.bestAttempt.auto_submitted"
                      class="badge badge-orange" style="font-size:10px;margin-left:4px">
                  Auto-submitted
                </span>
              </div>
              <span :class="['badge', e.bestAttempt.score >= e.passingScore
                ? 'badge-green' : 'badge-red']">
                {{ e.bestAttempt.score >= e.passingScore ? 'Passed' : 'Failed' }}
              </span>
            </div>

            <!--
              Final weighted grade (exam % + assignments %).
              Old system had no weighted grade — this is new.
            -->
            <div v-if="e.gradeData" class="final-grade-row">
              <div class="text-muted text-sm">
                Final Grade
                <span style="margin-left:4px">
                  (Exam {{ e.gradeData.exam_weight }}%
                  + Assignments {{ e.gradeData.assignment_weight }}%)
                </span>
              </div>
              <div class="display"
                   style="font-size:28px;margin-top:4px"
                   :style="e.gradeData.passed === true ? 'color:#25a244'
                     : e.gradeData.passed === false ? 'color:#e53e3e' : ''">
                {{
                  e.gradeData.final_grade !== null
                      ? e.gradeData.final_grade + '%' : '—'
                }}
              </div>
            </div>

            <!--
              MCQ breakdown (read-only).
              Old: e.result.correct / e.result.total (ExamResult fields).
              New: count from QuestionResponse objects on the best attempt.
            -->
            <div class="mcq-summary">
              <div class="mcq-summary-item">
                <span class="text-muted text-sm">MCQ correct</span>
                <strong>{{ mcqCorrect(e.bestAttempt) }}/{{ mcqTotal(e.bestAttempt) }}</strong>
              </div>
              <div class="mcq-summary-item">
                <span class="text-muted text-sm">Open questions</span>
                <strong>{{ openResponses(e.bestAttempt).length }}</strong>
              </div>
              <div class="mcq-summary-item">
                <span class="text-muted text-sm">Pending review</span>
                <strong :style="pendingCount(e.bestAttempt) > 0 ? 'color:var(--lf-orange)' : ''">
                  {{ pendingCount(e.bestAttempt) }}
                </strong>
              </div>
            </div>

            <!--
              Open answer review + grading.
              Old: used text grades (Pass/Good/Excellent/Fail) stored in
                   ExamResult.open_grades dict.
              New: numeric points_earned stored in QuestionResponse, graded via
                   PATCH /api/exams/responses/{id}/grade/
                   Teacher enters a score (0–max_points) + optional feedback.
            -->
            <div v-for="resp in openResponses(e.bestAttempt)" :key="resp.id"
                 class="open-review">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <span class="q-num-badge">Q{{ resp.question_index + 1 }}</span>
                <div style="font-size:14px;font-weight:600;flex:1">{{ resp.question_text }}</div>
                <span v-if="resp.points_earned !== null" class="badge badge-green">
                  {{ resp.points_earned }}/{{ resp.max_points }} pts
                </span>
                <span v-else class="badge badge-orange">Pending</span>
              </div>

              <!-- Student's answer -->
              <div class="open-answer-text">
                {{ resp.text_answer || '(No answer provided)' }}
              </div>

              <!-- Teacher feedback (shown if already graded) -->
              <div v-if="resp.teacher_feedback" class="teacher-feedback">
                <strong>Your feedback:</strong> {{ resp.teacher_feedback }}
              </div>

              <!-- Grade form -->
              <div class="grade-form">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                  <input
                      type="number"
                      v-model.number="gradeInputs[resp.id]"
                      :min="0"
                      :max="resp.max_points"
                      class="grade-input"
                      :placeholder="`0–${resp.max_points}`"
                  />
                  <span class="text-muted text-sm">/ {{ resp.max_points }} pts</span>
                  <textarea
                      v-model="feedbackInputs[resp.id]"
                      class="feedback-input"
                      rows="2"
                      placeholder="Feedback (optional)…"
                  />
                  <button
                      class="btn btn-primary btn-sm"
                      :disabled="gradeInputs[resp.id] === undefined
                      || gradeInputs[resp.id] === null
                      || gradeInputs[resp.id] === ''"
                      @click="handleGradeResponse(resp, e.bestAttempt)"
                  >
                    {{ resp.points_earned !== null ? 'Update' : 'Save Grade' }}
                  </button>
                </div>
              </div>
            </div>
            <!-- end open answers -->

          </template>
        </div>
        <!-- end right column -->

      </div>
    </div>
    <!-- end per-course cards -->
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {useToast} from 'primevue/usetoast'
import api from '@/api'
import {useStudentsStore} from '@/stores/students'
import {useCoursesStore} from '@/stores/courses'
import {useExamsStore} from '@/stores/exams'
import {useCertificatesStore} from '@/stores/certificates'
import {useAttendanceStore} from '@/stores/attendance'

const route = useRoute()
const toast = useToast()
const studentsStore = useStudentsStore()
const coursesStore = useCoursesStore()
const examsStore = useExamsStore()
const certsStore = useCertificatesStore()
const attStore = useAttendanceStore()

const studentId = computed(() => route.params.id)

const student = computed(() => studentsStore.students.find(s => s.id === studentId.value))
const enrollments = computed(() => coursesStore.enrollments.filter(e => e.student === studentId.value))
const certs = computed(() => certsStore.certificates.filter(c => c.student === studentId.value))
const sessions = computed(() => attStore.sessions)

// ── Per-course async data ──────────────────────────────────────────────────────
//
// Old architecture:
//   examsStore.results  → [ExamResult]  (model deleted)
//   result.answers      → dict of open answers
//   result.open_grades  → dict of text grades
//   gradeOpenAnswer()   → PATCH with text "Pass/Fail" etc.
//
// New architecture:
//   courseData[courseId].attempts  → [ExamAttempt] from /exams/{id}/all-attempts/
//   attempt.responses              → [QuestionResponse]  (per-question answers + scores)
//   gradeResponse()                → PATCH /exams/responses/{id}/grade/ with numeric points
//   courseData[courseId].gradeData → from /courses/{id}/final-grade/?student_id=
//
const courseData = ref({})   // { [courseId]: { exam, attempts, gradeData } }
const courseDataLoading = ref(false)

// Total exam attempts across all courses (replaces results.length in header)
const totalAttempts = computed(() =>
    Object.values(courseData.value).reduce(
        (sum, d) => sum + (d.attempts?.length ?? 0), 0
    )
)

// ── Grade/feedback inputs for open question grading ───────────────────────────
const gradeInputs = reactive({})   // { [responseId]: number }
const feedbackInputs = reactive({})   // { [responseId]: string }

// ── Load all per-course data on mount ─────────────────────────────────────────

async function loadCourseData() {
  if (!enrollments.value.length) return
  courseDataLoading.value = true

  try {
    await Promise.all(
        enrollments.value.map(async (enr) => {
          const cid = enr.course
          const entry = {exam: null, attempts: [], gradeData: null}

          // 1. Get exam for this course
          try {
            const {data} = await api.get('/exams/', {params: {course: cid}})
            const list = data.results ?? data
            entry.exam = list[0] ?? null
          } catch { /* no exam */
          }

          // 2. If exam exists, get this student's attempts from all-attempts
          if (entry.exam?.id) {
            try {
              const {data} = await api.get(`/exams/${entry.exam.id}/all-attempts/`)
              const all = data.results ?? data
              // all-attempts returns every student — filter for this one
              entry.attempts = all.filter(a => String(a.student) === String(studentId.value))
            } catch { /* no attempts */
            }

            // Pre-populate grade inputs from existing responses
            for (const attempt of entry.attempts) {
              for (const resp of (attempt.responses ?? [])) {
                if (gradeInputs[resp.id] === undefined) {
                  gradeInputs[resp.id] = resp.points_earned ?? ''
                  feedbackInputs[resp.id] = resp.teacher_feedback ?? ''
                }
              }
            }
          }

          // 3. Get final weighted grade for this student in this course
          try {
            const {data} = await api.get(
                `/courses/${cid}/final-grade/`,
                {params: {student_id: studentId.value}}
            )
            entry.gradeData = data
          } catch { /* no grade data yet */
          }

          courseData.value[cid] = entry
        })
    )
  } finally {
    courseDataLoading.value = false
  }
}

// ── Computed enriched enrollments ─────────────────────────────────────────────

const enrichedEnrollments = computed(() => {
  if (!student.value) return []

  return enrollments.value.map(enr => {
    const course = coursesStore.courses.find(c => c.id === enr.course)
    if (!course) return null

    const cd = courseData.value[enr.course] ?? {}
    const exam = cd.exam ?? null
    const attempts = cd.attempts ?? []
    const gradeData = cd.gradeData ?? null
    const passingScore = gradeData?.passing_score ?? exam?.passing_score ?? 60
    const maxRetakes = exam?.max_retakes ?? 0

    // Best attempt = highest score among submitted attempts
    const bestAttempt = attempts.length
        ? attempts.reduce((best, a) =>
            (a.score ?? 0) > (best.score ?? 0) ? a : best, attempts[0])
        : null

    const cert = certs.value.find(c => c.course === enr.course) ?? null

    // Attendance stats
    const cs = sessions.value.filter(s => s.course === enr.course)
    const attended = cs.filter(s => s.attendee_ids?.includes(studentId.value)).length
    const attStats = {
      attended,
      total: cs.length,
      pct: cs.length ? Math.round((attended / cs.length) * 100) : 0,
    }

    // Risk flags
    const risks = []
    if (bestAttempt && bestAttempt.score < passingScore) {
      risks.push('Failed exam')
    }
    if (gradeData?.final_grade !== null && gradeData?.final_grade !== undefined) {
      if (gradeData.final_grade < passingScore) risks.push('Below passing grade')
    }
    if (
        student.value.student_type === 'onsite' &&
        attStats.total > 0 &&
        attStats.pct < (course.attendance_threshold ?? 75)
    ) {
      risks.push(`Attendance below ${course.attendance_threshold ?? 75}%`)
    }

    return {
      id: enr.id,
      enrollment: enr,
      course,
      exam,
      attempts,
      bestAttempt,
      attemptCount: attempts.length,
      maxRetakes,
      gradeData,
      passingScore,
      cert,
      attStats,
      risks,
    }
  }).filter(Boolean)
})

// ── Question response helpers ─────────────────────────────────────────────────

/**
 * Open question responses from an attempt — these need teacher grading.
 * Old: openQuestions(e) returned questions from examMap[courseId].questions
 *      filtered by type === 'open', then displayed e.result.answers[q.order].
 * New: responses are stored directly on the attempt as QuestionResponse objects.
 */
function openResponses(attempt) {
  if (!attempt?.responses) return []
  return attempt.responses.filter(r => r.question_type === 'open')
}

function mcqCorrect(attempt) {
  if (!attempt?.responses) return 0
  return attempt.responses.filter(r => r.question_type === 'mcq' && r.is_correct).length
}

function mcqTotal(attempt) {
  if (!attempt?.responses) return 0
  return attempt.responses.filter(r => r.question_type === 'mcq').length
}

function pendingCount(attempt) {
  if (!attempt?.responses) return 0
  return attempt.responses.filter(
      r => r.question_type === 'open' && r.points_earned === null
  ).length
}

// ── Grading ───────────────────────────────────────────────────────────────────

/**
 * Grade an open question response with numeric points.
 * Old: examsStore.gradeOpenAnswer(resultId, qi, 'Pass'|'Fail'|'Good'|'Excellent')
 *      stored a text label in ExamResult.open_grades dict.
 * New: examsStore.gradeResponse(responseId, pointsEarned, teacherFeedback)
 *      PATCH /api/exams/responses/{id}/grade/  { points_earned, teacher_feedback }
 *      which also recomputes the attempt's overall score on the backend.
 */
async function handleGradeResponse(resp, attempt) {
  const pts = gradeInputs[resp.id]
  if (pts === '' || pts === null || pts === undefined) {
    toast.add({severity: 'warn', summary: 'Enter a score first', life: 3000})
    return
  }
  if (pts < 0 || pts > resp.max_points) {
    toast.add({severity: 'warn', summary: `Score must be 0–${resp.max_points}`, life: 3000})
    return
  }
  try {
    const updated = await examsStore.gradeResponse(
        resp.id,
        Number(pts),
        feedbackInputs[resp.id] ?? '',
    )
    // Update the response in the local attempt object
    if (attempt?.responses) {
      const idx = attempt.responses.findIndex(r => r.id === resp.id)
      if (idx > -1) attempt.responses[idx] = updated
    }
    toast.add({severity: 'success', summary: 'Grade saved', life: 2500})
  } catch {
    toast.add({severity: 'error', summary: 'Failed to save grade', life: 3000})
  }
}

// ── Attendance helper ─────────────────────────────────────────────────────────

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

// ── Utils ─────────────────────────────────────────────────────────────────────

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

function openCert(cert, course) {
  if (!student.value) return
  const issued = new Date(cert.issued_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Certificate</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet"/>
  <style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5}
  .cert{background:#fff;border-radius:8px;padding:48px;max-width:600px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.1)}
  .logo{font-family:'Bebas Neue',sans-serif;font-size:24pt;letter-spacing:3px}.logo span{color:#FF6B00}
  .name{font-family:'Bebas Neue',sans-serif;font-size:36pt;letter-spacing:3px;border-bottom:3px solid #FF6B00;padding-bottom:16px;margin:16px 0}
  .course{font-family:'Bebas Neue',sans-serif;font-size:20pt;color:#FF6B00;margin-bottom:20px}
  .meta{font-size:11pt;color:#aaa;text-transform:uppercase;letter-spacing:.8px}
  .no-print{margin-top:24px}@media print{.no-print{display:none}}</style></head>
  <body><div class="cert"><div class="logo">LEARN<span>FORGE</span></div>
  <p style="color:#aaa;font-size:10pt;margin:8px 0">This certificate is presented to</p>
  <div class="name">${student.value.name}</div>
  <p style="color:#555;margin-bottom:8px">for successfully completing</p>
  <div class="course">${course.title}</div>
  <div class="meta"><p>Issued: ${issued}</p><p>Certificate ID: ${cert.cert_code}</p></div>
  <div class="no-print"><button onclick="window.print()" style="padding:10px 24px;background:#FF6B00;color:#fff;border:none;border-radius:4px;font-weight:600;cursor:pointer">🖨 Print</button></div>
  </div></body></html>`
  window.open(URL.createObjectURL(new Blob([html], {type: 'text/html'})), '_blank')
}

function printReport() {
  window.print()
}

// ── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  const id = studentId.value
  await Promise.all([
    studentsStore.fetchStudents(),
    coursesStore.fetchCourses(),
    coursesStore.fetchEnrollments({student: id}),
    certsStore.fetchCertificates({student: id}),
    attStore.fetchSessions(),
  ])
  // Load per-course exam attempts + grades after enrollments are populated
  await loadCourseData()
})
</script>

<style scoped>
.big-avatar {
  width: 52px;
  height: 52px;
  background: var(--lf-orange);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #fff;
  font-size: 22px;
  flex-shrink: 0;
}

.kpi {
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
  min-width: 80px;
}

.kpi-val {
  font-family: var(--lf-font-display);
  font-size: 32px;
}

.kpi-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--lf-gray-400);
}

.report-section-title {
  font-family: var(--lf-font-display);
  font-size: 20px;
  letter-spacing: .5px;
  margin-bottom: 12px;
}

/* Final grade row */
.final-grade-row {
  background: var(--lf-gray-100);
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 14px;
  display: flex;
  flex-direction: column;
}

/* MCQ summary */
.mcq-summary {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.mcq-summary-item {
  flex: 1;
  min-width: 80px;
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mcq-summary-item strong {
  font-size: 16px;
}

/* Open question review */
.open-review {
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 14px;
  margin-top: 12px;
  border-left: 3px solid var(--lf-orange);
}

.q-num-badge {
  background: var(--lf-black);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.open-answer-text {
  background: var(--lf-white);
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--lf-gray-600);
  font-style: italic;
  margin-bottom: 10px;
  white-space: pre-wrap;
}

.teacher-feedback {
  background: #e6f7ee;
  border: 1.5px solid #25a244;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--lf-gray-600);
  margin-bottom: 10px;
}

.grade-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.grade-input {
  width: 72px;
  padding: 6px 8px;
  border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 13px;
  outline: none;
}

.grade-input:focus {
  border-color: var(--lf-orange);
}

.feedback-input {
  flex: 1;
  min-width: 160px;
  padding: 6px 10px;
  border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 13px;
  outline: none;
  resize: vertical;
}

.feedback-input:focus {
  border-color: var(--lf-orange);
}

.risk-flag {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  padding: 7px 10px;
  background: #fff5f5;
  border: 1.5px solid #feb2b2;
  border-radius: 6px;
  font-size: 12px;
  color: #c53030;
  font-weight: 600;
}

.att-good {
  color: #25a244;
  font-weight: 600;
}

.att-warn {
  color: var(--lf-orange);
  font-weight: 600;
}

.att-bad {
  color: #e53e3e;
  font-weight: 600;
}

.spinner {
  width: 28px;
  height: 28px;
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

.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: none;
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
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

.btn-ghost {
  background: transparent;
  color: var(--lf-gray-600);
  border: 1px solid var(--lf-gray-200);
}

.btn-ghost:hover {
  border-color: var(--lf-black);
  color: var(--lf-black);
}

.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
}

.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--lf-gray-600);
}

@media print {
  .btn {
    display: none;
  }

  .grade-form {
    display: none;
  }
}
</style>