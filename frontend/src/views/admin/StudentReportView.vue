<template>
  <div class="page-content" v-if="student">
    <div style="display:flex;gap:8px;margin-bottom:20px">
      <button class="btn btn-ghost btn-sm" @click="$router.push('/reports')">← All Reports</button>
      <button class="btn btn-primary btn-sm" @click="printReport">🖨️ Print Report</button>
    </div>

    <!-- Profile -->
    <div class="lf-card" style="margin-bottom:24px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">
        <div style="display:flex;align-items:center;gap:16px">
          <div class="big-avatar">{{ student.name.charAt(0) }}</div>
          <div>
            <div class="display" style="font-size:28px;letter-spacing:.5px">{{ student.name }}</div>
            <div class="text-muted text-sm">{{ student.email }}</div>
            <span :class="['type-pill', `type-${student.student_type}`]" style="margin-top:4px;display:inline-flex">
              {{ student.student_type === 'online' ? '💻 Online' : '🏫 On-site' }}
            </span>
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <div class="kpi"><div class="kpi-val">{{ enrollments.length }}</div><div class="kpi-label">Courses</div></div>
          <div class="kpi"><div class="kpi-val">{{ results.length }}</div><div class="kpi-label">Exams</div></div>
          <div class="kpi"><div class="kpi-val" :style="certs.length ? 'color:#25a244':''">{{ certs.length }}</div><div class="kpi-label">Certs</div></div>
        </div>
      </div>
    </div>

    <!-- Per-course -->
    <div v-for="e in enrichedEnrollments" :key="e.id" class="lf-card" style="margin-bottom:20px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px">
        <div>
          <div class="display" style="font-size:22px;letter-spacing:.4px">{{ e.course.title }}</div>
          <div v-if="e.risks.length" class="risk-flag">⚠ {{ e.risks.join(' · ') }}</div>
        </div>
        <button v-if="e.cert" class="cert-badge" @click="openCert(e.cert, e.course)">🎓 View Certificate</button>
      </div>

      <div class="lf-col-2">
        <!-- Left: lessons or attendance -->
        <div>
          <div class="report-section-title">{{ student.student_type === 'online' ? 'Lesson Progress' : 'Attendance' }}</div>
          <template v-if="student.student_type === 'online'">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="text-muted text-sm">Completed</span>
              <span class="text-sm font-600">{{ e.enrollment.completed_lesson_ids?.length ?? 0 }}/{{ e.course.lessons?.length ?? 0 }} ({{ e.enrollment.lesson_completion_pct ?? 0 }}%)</span>
            </div>
            <div class="progress-bar" style="height:8px"><div class="progress-fill" :style="{ width: (e.enrollment.lesson_completion_pct ?? 0) + '%' }" /></div>
            <div style="margin-top:12px">
              <div v-for="(l, i) in e.course.lessons" :key="l.id" style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--lf-gray-200);font-size:13px">
                <span :style="e.enrollment.completed_lesson_ids?.includes(l.id) ? 'color:#25a244' : 'color:var(--lf-gray-400)'">{{ e.enrollment.completed_lesson_ids?.includes(l.id) ? '✓' : '○' }}</span>
                <span>{{ l.title }}</span>
                <span class="badge badge-gray" style="margin-left:auto">{{ l.type }}</span>
              </div>
            </div>
          </template>
          <template v-else>
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="text-muted text-sm">Sessions attended</span>
              <span :class="attClass(e.attStats.pct)" style="font-size:14px">{{ e.attStats.pct }}% ({{ e.attStats.attended }}/{{ e.attStats.total }})</span>
            </div>
            <div class="progress-bar" style="height:8px"><div class="progress-fill" :style="{ width: e.attStats.pct + '%' }" /></div>
            <div style="font-size:12px;color:var(--lf-gray-600);margin-top:6px">Threshold: <strong>{{ e.course.attendance_threshold }}%</strong></div>
          </template>
        </div>

        <!-- Right: exam -->
        <div>
          <div class="report-section-title">Exam Results</div>
          <div v-if="!e.result" style="background:var(--lf-gray-100);border-radius:6px;padding:16px;text-align:center;color:var(--lf-gray-600);font-size:14px">
            Exam not taken yet.
          </div>
          <template v-else>
            <div :style="`background:${e.result.score >= 60 ? '#e6f7ee' : '#fff5f5'};border-radius:6px;padding:16px;text-align:center;margin-bottom:12px`">
              <div class="display" :style="`font-size:48px;color:${e.result.score >= 60 ? '#25a244' : '#e53e3e'}`">{{ e.result.score }}%</div>
              <div class="text-muted text-sm">{{ e.result.correct }}/{{ e.result.total }} MCQ · {{ formatDate(e.result.submitted_at) }}</div>
              <span :class="['badge', e.result.score >= 60 ? 'badge-green' : 'badge-red']">{{ e.result.score >= 60 ? 'Passed' : 'Failed' }}</span>
            </div>
            <!-- Open answers -->
            <div v-for="(q, qi) in openQuestions(e)" :key="qi" class="open-review">
              <div style="font-size:14px;font-weight:600;margin-bottom:6px">{{ q.text }}</div>
              <div style="font-size:14px;color:var(--lf-gray-600);font-style:italic;margin-bottom:8px">{{ e.result.answers?.[q.order] || 'No answer' }}</div>
              <div style="display:flex;align-items:center;gap:8px">
                <label class="form-label" style="margin:0">Grade:</label>
                <select class="grade-select" :value="e.result.open_grades?.[q.order] ?? ''" @change="gradeOpen(e.result.id, q.order, $event.target.value)">
                  <option value="">— Not graded —</option>
                  <option value="Pass">✓ Pass</option>
                  <option value="Good">★ Good</option>
                  <option value="Excellent">🏆 Excellent</option>
                  <option value="Fail">✗ Fail</option>
                </select>
                <span v-if="e.result.open_grades?.[q.order]" :class="['badge', e.result.open_grades[q.order] === 'Fail' ? 'badge-red' : 'badge-green']">{{ e.result.open_grades[q.order] }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute }                 from 'vue-router'
import { useToast }                 from 'primevue/usetoast'
import { useStudentsStore }         from '@/stores/students'
import { useCoursesStore }          from '@/stores/courses'
import { useExamsStore }            from '@/stores/exams'
import { useCertificatesStore }     from '@/stores/certificates'
import { useAttendanceStore }       from '@/stores/attendance'

const route         = useRoute()
const toast         = useToast()
const studentsStore = useStudentsStore()
const coursesStore  = useCoursesStore()
const examsStore    = useExamsStore()
const certsStore    = useCertificatesStore()
const attStore      = useAttendanceStore()

const student     = computed(() => studentsStore.students.find(s => s.id === route.params.id))
const enrollments = computed(() => coursesStore.enrollments.filter(e => e.student === route.params.id))
const results     = computed(() => examsStore.results.filter(r => r.student === route.params.id))
const certs       = computed(() => certsStore.certificates.filter(c => c.student === route.params.id))
const sessions    = computed(() => attStore.sessions)

// FIX M2: store full exam objects (with questions) keyed by course ID
const examMap = ref({})

const enrichedEnrollments = computed(() => {
  if (!student.value) return []
  return enrollments.value.map(e => {
    const course  = coursesStore.courses.find(c => c.id === e.course)
    if (!course) return null
    const result  = results.value.find(r => r.course_id === e.course)
    const cert    = certs.value.find(c => c.course === e.course)
    const cs      = sessions.value.filter(s => s.course === e.course)
    const attended = cs.filter(s => s.attendee_ids?.includes(student.value.id)).length
    const attStats = { attended, total: cs.length, pct: cs.length ? Math.round((attended / cs.length) * 100) : 0 }
    const risks    = []
    if (result && result.score < 60) risks.push('Failed exam')
    if (student.value.student_type === 'onsite' && attStats.pct < course.attendance_threshold && attStats.total > 0) risks.push(`Attendance below ${course.attendance_threshold}%`)
    return { enrollment: e, course, result, cert, attStats, risks }
  }).filter(Boolean)
})

// FIX M2: return the actual open questions from the fetched exam
function openQuestions(e) {
  if (!e.result || !e.course) return []
  const exam = examMap.value[e.course.id]
  if (!exam?.questions) return []
  return exam.questions.filter(q => q.type === 'open')
}

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function gradeOpen(resultId, qi, grade) {
  await examsStore.gradeOpenAnswer(resultId, qi, grade)
  toast.add({ severity: 'success', summary: grade ? `Graded: ${grade}` : 'Grade cleared', life: 2000 })
}

function openCert(cert, course) {
  if (!student.value) return
  const issued = new Date(cert.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  const html   = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Certificate</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet"/>
  <style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5}
  .cert{background:#fff;border-radius:8px;padding:48px;max-width:600px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.1)}
  .logo{font-family:'Bebas Neue',sans-serif;font-size:24pt;letter-spacing:3px}.logo span{color:#FF6B00}
  .name{font-family:'Bebas Neue',sans-serif;font-size:36pt;letter-spacing:3px;border-bottom:3px solid #FF6B00;padding-bottom:16px;margin:16px 0}
  .course{font-family:'Bebas Neue',sans-serif;font-size:20pt;color:#FF6B00;margin-bottom:20px}
  .meta{font-size:11pt;color:#aaa;text-transform:uppercase;letter-spacing:.8px}
  .no-print{margin-top:24px} @media print{.no-print{display:none}}</style></head>
  <body><div class="cert"><div class="logo">LEARN<span>FORGE</span></div>
  <p style="color:#aaa;font-size:10pt;margin:8px 0">This certificate is presented to</p>
  <div class="name">${student.value.name}</div>
  <p style="color:#555;margin-bottom:8px">for successfully completing</p>
  <div class="course">${course.title}</div>
  <div class="meta"><p>Issued: ${issued}</p><p>Certificate ID: ${cert.cert_code}</p></div>
  <div class="no-print"><button onclick="window.print()" style="padding:10px 24px;background:#FF6B00;color:#fff;border:none;border-radius:4px;font-weight:600;cursor:pointer">🖨 Print</button></div>
  </div></body></html>`
  window.open(URL.createObjectURL(new Blob([html], { type: 'text/html' })), '_blank')
}

function printReport() {
  window.print()
}

onMounted(async () => {
  const id = route.params.id
  await Promise.all([
    studentsStore.fetchStudents(),
    coursesStore.fetchCourses(),
    coursesStore.fetchEnrollments({ student: id }),
    examsStore.fetchResults({ student: id }),
    certsStore.fetchCertificates({ student: id }),
    attStore.fetchSessions(),
  ])
  // FIX M2: fetch the full exam (with questions) for each enrolled course
  for (const e of coursesStore.enrollments.filter(en => en.student === id)) {
    try {
      const exam = await examsStore.fetchExamByCourse(e.course)
      if (exam) {
        const full = await examsStore.fetchExam(exam.id)
        examMap.value[e.course] = full
      }
    } catch (_) { /* course has no exam */ }
  }
})
</script>

<style scoped>
.big-avatar { width: 52px; height: 52px; background: var(--lf-orange); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 22px; flex-shrink: 0; }
.kpi { background: var(--lf-gray-100); border-radius: 6px; padding: 12px; text-align: center; min-width: 80px; }
.kpi-val   { font-family: var(--lf-font-display); font-size: 32px; }
.kpi-label { font-size: 10px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-400); }
.report-section-title { font-family: var(--lf-font-display); font-size: 20px; letter-spacing: .5px; margin-bottom: 12px; }
.open-review { background: var(--lf-gray-100); border-radius: 6px; padding: 14px; margin-top: 10px; border-left: 3px solid var(--lf-orange); }
.risk-flag { display: flex; align-items: center; gap: 6px; margin-top: 6px; padding: 7px 10px; background: #fff5f5; border: 1.5px solid #feb2b2; border-radius: 6px; font-size: 12px; color: #c53030; font-weight: 600; }
.grade-select { padding: 4px 10px; border: 1.5px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 13px; font-weight: 600; outline: none; background: var(--lf-white); cursor: pointer; }
.grade-select:focus { border-color: var(--lf-orange); }
.btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-ghost   { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-sm { padding: 6px 14px; font-size: 12px; }
.form-label { display: block; font-size: 12px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-600); }
</style>