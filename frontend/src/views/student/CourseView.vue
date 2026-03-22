<template>
  <div class="page-content" v-if="course">
    <div style="margin-bottom:16px">
      <button class="btn btn-ghost btn-sm" @click="$router.push('/my-courses')">← My Courses</button>
    </div>

    <div class="lf-content-sidebar">

      <!-- ── Main content ───────────────────────────────────────────────── -->
      <div>
        <div class="lf-card" style="margin-bottom:20px">
          <div class="card-title">{{ course.title }}</div>
          <p class="text-muted" style="margin-top:8px;font-size:14px">{{ course.description }}</p>

          <!-- Online: lesson progress bar -->
          <div v-if="!auth.isOnsite" style="margin-top:16px">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="text-sm text-muted">Overall Progress</span>
              <span class="text-sm font-600">
                {{ enrollment?.lesson_completion_pct ?? 0 }}%
                ({{ completedCount }}/{{ course.lessons?.length ?? 0 }})
              </span>
            </div>
            <div class="progress-bar" style="height:8px">
              <div class="progress-fill"
                   :style="{ width: (enrollment?.lesson_completion_pct ?? 0) + '%' }"/>
            </div>
          </div>

          <!-- Onsite: attendance bar -->
          <div v-else
               style="margin-top:16px;padding:16px;background:var(--lf-gray-100);border-radius:6px">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:13px;font-weight:600">Attendance</span>
              <span :class="attClass(attStats.pct)" style="font-size:14px">
                {{ attStats.pct }}% · {{ attStats.attended }}/{{ attStats.total }} sessions
              </span>
            </div>
            <div class="progress-bar" style="height:8px">
              <div class="progress-fill" :style="{ width: attStats.pct + '%' }"/>
            </div>
            <div style="margin-top:6px;font-size:12px;color:var(--lf-gray-600)">
              Required threshold: <strong>{{ course.attendance_threshold }}%</strong>
              <span v-if="attStats.pct >= course.attendance_threshold"
                    class="badge badge-green" style="margin-left:6px">On track ✓</span>
              <span v-else-if="attStats.total > 0"
                    class="badge badge-red" style="margin-left:6px">Below threshold</span>
            </div>
          </div>
        </div>

        <!-- Lesson list -->
        <div class="section-title" style="margin-bottom:12px">Lessons</div>
        <div class="lesson-list">
          <div
              v-for="(l, i) in course.lessons"
              :key="l.id"
              class="lesson-item"
              @click="$router.push(`/my-courses/${courseId}/lessons/${l.id}`)"
          >
            <div class="lesson-num"
                 :style="completedIds.includes(l.id)
                   ? 'background:var(--lf-orange);color:white' : ''">
              {{ completedIds.includes(l.id) ? '✓' : i + 1 }}
            </div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ l.title }}</div>
              <div class="lesson-item-type">
                {{ l.type === 'video' ? '🎬 Video Lesson' : '📄 Text Lesson' }}
              </div>
            </div>
            <span style="color:var(--lf-gray-400);font-size:18px">›</span>
          </div>
        </div>
      </div>

      <!-- ── Sidebar ─────────────────────────────────────────────────────── -->
      <div class="course-sidebar-card lf-sticky-card">
        <div class="course-sidebar-thumb">{{ course.icon || '📚' }}</div>
        <div class="course-sidebar-info">
          <h3 class="display" style="font-size:22px;letter-spacing:.4px">{{ course.title }}</h3>

          <div style="margin-top:12px;display:flex;flex-direction:column;gap:8px">
            <!-- Student type -->
            <div style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Type</span>
              <span :class="['type-pill', `type-${auth.user?.student_type}`]">
                {{ auth.isOnsite ? '🏫 On-site' : '💻 Online' }}
              </span>
            </div>

            <!-- Lesson count -->
            <div style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Lessons</span>
              <strong>{{ course.lessons?.length ?? 0 }}</strong>
            </div>

            <!-- Attendance or lesson progress -->
            <div v-if="auth.isOnsite"
                 style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Attendance</span>
              <strong :class="attClass(attStats.pct)">{{ attStats.pct }}%</strong>
            </div>
            <div v-else style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Progress</span>
              <strong>{{ enrollment?.lesson_completion_pct ?? 0 }}%</strong>
            </div>

            <!-- Exam status -->
            <div style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Exam</span>
              <strong>{{ course.exam ? 'Yes' : 'No' }}</strong>
            </div>

            <!--
              Exam score — replaces old examResult.score (ExamResult model deleted).
              Now uses bestAttempt.score from ExamAttempt, loaded via
              GET /api/exams/{id}/my-attempts/ after the exam is fetched.
            -->
            <div v-if="bestAttempt"
                 style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Best Score</span>
              <strong :style="bestAttempt.score >= passingScore
                ? 'color:#25a244' : 'color:#e53e3e'">
                {{ bestAttempt.score }}%
              </strong>
            </div>

            <!--
              Final weighted grade (exam % + assignments %) — new in this session.
              Loaded via GET /api/courses/{id}/final-grade/
            -->
            <div v-if="gradeData?.final_grade !== null && gradeData?.final_grade !== undefined"
                 style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Final Grade</span>
              <strong :style="gradeData.passed === true
                ? 'color:#25a244' : gradeData.passed === false ? 'color:#e53e3e' : ''">
                {{ gradeData.final_grade }}%
              </strong>
            </div>

            <!-- Retakes remaining -->
            <div v-if="myAttemptsInfo?.retakes_remaining !== null
                       && myAttemptsInfo?.retakes_remaining !== undefined"
                 style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Retakes left</span>
              <strong>{{ myAttemptsInfo.retakes_remaining ?? '∞' }}</strong>
            </div>
          </div>

          <!-- CTA buttons -->
          <div style="margin-top:16px;display:flex;flex-direction:column;gap:8px">

            <!-- Start / continue lessons -->
            <button
                v-if="course.lessons?.length"
                class="btn btn-primary"
                style="width:100%"
                @click="startLesson"
            >
              {{ completedCount > 0 ? 'Continue Learning →' : 'Start Course →' }}
            </button>

            <!--
              Take exam — visible when all lessons done and student hasn't passed yet.
              Old: !examResult (ExamResult object from deleted model).
              New: !bestAttempt?.passed (ExamAttempt property).
            -->
            <button
                v-if="course.exam && allLessonsDone && !bestAttempt?.passed"
                class="btn btn-secondary"
                style="width:100%"
                @click="$router.push(`/my-courses/${courseId}/exam`)"
            >
              {{ bestAttempt ? 'Retake Exam →' : 'Take Exam →' }}
            </button>

            <!--
              Score badge — replaces old examResult score div.
              Shows when student has at least one submitted attempt.
            -->
            <div
                v-if="bestAttempt"
                class="badge"
                :class="bestAttempt.passed ? 'badge-green' : 'badge-orange'"
                style="text-align:center;padding:10px;display:block"
            >
              {{ bestAttempt.passed ? '✓ Passed' : '✗ Not passed yet' }}
              · {{ bestAttempt.score }}%
            </div>

            <!-- Certificate -->
            <button
                v-if="hasCert"
                class="cert-badge"
                style="justify-content:center"
                @click="openCert"
            >
              🎓 View Certificate
            </button>

            <!-- Onsite check-in -->
            <button
                v-if="auth.isOnsite"
                class="btn btn-outline"
                style="width:100%"
                @click="$router.push('/check-in')"
            >
              📋 Check In to Session
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import {useCoursesStore} from '@/stores/courses'
import {useExamsStore} from '@/stores/exams'
import {useCertificatesStore} from '@/stores/certificates'
import {useAttendanceStore} from '@/stores/attendance'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const courses = useCoursesStore()
const exams = useExamsStore()
const certs = useCertificatesStore()
const attStore = useAttendanceStore()

// ── Route param ───────────────────────────────────────────────────────────────
// Router defines :courseId — old code mixed .id and .courseId, now unified.
const courseId = computed(() => route.params.courseId)

// ── Base data ─────────────────────────────────────────────────────────────────
const course = computed(() => courses.current)
const enrollment = computed(() =>
    courses.enrollments.find(e => e.course === courseId.value)
)
const completedIds = computed(() => enrollment.value?.completed_lesson_ids ?? [])
const completedCount = computed(() => completedIds.value.length)
const allLessonsDone = computed(() =>
    (course.value?.lessons?.length ?? 0) > 0 &&
    course.value.lessons.every(l => completedIds.value.includes(l.id))
)
const hasCert = computed(() =>
    certs.certificates.some(c => c.course === courseId.value)
)

// ── Attendance ────────────────────────────────────────────────────────────────
const attStats = computed(() => {
  const sessions = attStore.sessions.filter(s => s.course === courseId.value)
  const total = sessions.length
  if (!total || !auth.user) return {attended: 0, total: 0, pct: 0}
  const attended = sessions.filter(s => s.attendee_ids?.includes(auth.user.id)).length
  return {attended, total, pct: Math.round((attended / total) * 100)}
})

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

// ── Exam data (new architecture) ──────────────────────────────────────────────
//
// Old: exams.results (ExamResult model — deleted)
//      examResult = exams.results.find(r => r.course_id === id)
//      examResult.score, examResult.correct, examResult.total
//
// New:
//   1. Fetch exam via GET /api/exams/?course={id}  → exams.exam
//   2. Fetch attempts via GET /api/exams/{id}/my-attempts/ → myAttemptsData
//   3. Fetch weighted grade via GET /api/courses/{id}/final-grade/ → finalGrade
//
// bestAttempt = highest-score submitted attempt from myAttemptsData.attempts

const myAttemptsInfo = computed(() => exams.myAttemptsData)
const gradeData = computed(() => exams.finalGrade)

const bestAttempt = computed(() => {
  const attempts = myAttemptsInfo.value?.attempts ?? []
  if (!attempts.length) return null
  return attempts.reduce(
      (best, a) => (a.score ?? 0) > (best.score ?? 0) ? a : best,
      attempts[0]
  )
})

const passingScore = computed(() =>
    myAttemptsInfo.value?.passing_score ?? exams.exam?.passing_score ?? 60
)

// ── Actions ───────────────────────────────────────────────────────────────────

function startLesson() {
  // Resume first incomplete lesson, or start from beginning
  const lessons = course.value?.lessons ?? []
  const next = lessons.find(l => !completedIds.value.includes(l.id)) ?? lessons[0]
  if (next) router.push(`/my-courses/${courseId.value}/lessons/${next.id}`)
}

function openCert() {
  const cert = certs.certificates.find(c => c.course === courseId.value)
  const student = auth.user
  if (!cert || !student || !course.value) return
  const issued = new Date(cert.issued_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
  const track = auth.isOnsite ? 'On-site Programme' : 'Online Programme'
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Certificate</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet"/>
  <style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5}
  .cert{background:#fff;max-width:640px;width:100%;padding:56px;text-align:center;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.1);position:relative;overflow:hidden}
  .cert::before{content:'';position:absolute;top:0;left:0;right:0;height:6px;background:#FF6B00}
  .logo{font-family:'Bebas Neue',sans-serif;font-size:24pt;letter-spacing:3px;margin-bottom:24px}.logo span{color:#FF6B00}
  .sub{font-size:10pt;color:#aaa;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px}
  .name{font-family:'Bebas Neue',sans-serif;font-size:40pt;letter-spacing:3px;color:#0a0a0a;border-bottom:3px solid #FF6B00;padding-bottom:16px;margin-bottom:20px}
  .course{font-family:'Bebas Neue',sans-serif;font-size:20pt;color:#FF6B00;margin-bottom:24px}
  .track{display:inline-block;padding:4px 16px;border:1.5px solid #0a0a0a;border-radius:20px;font-size:9pt;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:24px}
  .meta{font-size:10pt;color:#aaa;text-transform:uppercase;letter-spacing:.8px}
  .meta span{color:#0a0a0a;font-weight:600}
  .no-print{margin-top:24px}@media print{.no-print{display:none}}</style></head>
  <body><div class="cert">
  <div class="logo">LEARN<span>FORGE</span></div>
  <div class="sub">This certificate is presented to</div>
  <div class="name">${student.name}</div>
  <div class="sub">for successfully completing</div>
  <div class="course">${course.value.title}</div>
  <div class="track">${track}</div>
  <div class="meta"><p>Issued: <span>${issued}</span></p>
  <p style="margin-top:4px">Certificate ID: <span>${cert.cert_code}</span></p></div>
  <div class="no-print" style="margin-top:28px">
  <button onclick="window.print()" style="padding:10px 28px;background:#FF6B00;color:#fff;border:none;border-radius:4px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;cursor:pointer">
    🖨 Print / Save PDF
  </button></div></div></body></html>`
  window.open(URL.createObjectURL(new Blob([html], {type: 'text/html'})), '_blank')
}

// ── Mount ─────────────────────────────────────────────────────────────────────

onMounted(async () => {
  const cid = courseId.value

  // Load base data in parallel
  await Promise.all([
    courses.fetchCourse(cid),
    courses.fetchEnrollments(),
    certs.fetchCertificates(),
    attStore.fetchSessions(cid),
  ])

  // Load exam + attempts if course has an exam
  // Old: exams.fetchResults() → GET /api/exams/results/?student=...
  // New: fetchExamByCourse()  → GET /api/exams/?course={id}
  //      fetchMyAttempts()    → GET /api/exams/{examId}/my-attempts/
  //      fetchFinalGrade()    → GET /api/courses/{id}/final-grade/
  if (course.value?.exam || courses.current?.exam) {
    try {
      const exam = await exams.fetchExamByCourse(cid)
      if (exam?.id) {
        await Promise.all([
          exams.fetchMyAttempts(exam.id),
          exams.fetchFinalGrade(cid),
        ])
      }
    } catch {
      // Course might have no exam — not an error
    }
  }
})
</script>

<style scoped>
.course-sidebar-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  overflow: hidden;
}

.course-sidebar-thumb {
  height: 160px;
  background: var(--lf-black);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--lf-font-display);
  font-size: 56px;
  color: var(--lf-orange);
}

.course-sidebar-info {
  padding: 20px;
}

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
}

.lesson-item-title {
  font-size: 14px;
  font-weight: 500;
}

.lesson-item-type {
  font-size: 12px;
  color: var(--lf-gray-400);
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

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all .18s;
}

.btn-primary {
  background: var(--lf-orange);
  color: #fff;
}

.btn-primary:hover {
  background: var(--lf-orange-dark);
}

.btn-secondary {
  background: var(--lf-black);
  color: #fff;
}

.btn-outline {
  background: transparent;
  color: var(--lf-black);
  border: 2px solid var(--lf-black);
}

.btn-outline:hover {
  background: var(--lf-black);
  color: #fff;
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
</style>