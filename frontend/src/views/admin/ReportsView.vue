<template>
  <div class="page-content">
    <div class="stats-grid">
      <div class="stat-card accent"><div class="stat-label">Students</div><div class="stat-value">{{ students.length }}</div></div>
      <div class="stat-card" :class="{ accent: atRisk.length }">
        <div class="stat-label">At Risk</div>
        <div class="stat-value" :style="!atRisk.length ? 'color:var(--lf-gray-400)' : ''">{{ atRisk.length }}</div>
        <div class="stat-sub">Need attention</div>
      </div>
      <div class="stat-card"><div class="stat-label">Certificates</div><div class="stat-value">{{ certs.length }}</div></div>
    </div>

    <div class="courses-grid">
      <div
        v-for="s in sortedStudents" :key="s.id"
        class="report-card"
        :class="{ 'at-risk': riskFlags(s).length }"
        @click="$router.push(`/reports/${s.id}`)"
      >
        <div class="report-card-strip" :style="riskFlags(s).length ? 'background:#e53e3e' : ''" />
        <div class="report-card-body">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div style="font-family:var(--lf-font-display);font-size:20px;letter-spacing:.3px">{{ s.name }}</div>
              <div class="text-muted text-sm">{{ s.email }}</div>
            </div>
            <span :class="['type-pill', `type-${s.student_type}`]">{{ s.student_type === 'online' ? '💻' : '🏫' }} {{ s.student_type }}</span>
          </div>
          <div class="kpi-row">
            <div class="kpi"><div class="kpi-val">{{ studentEnrollments(s.id).length }}</div><div class="kpi-label">Courses</div></div>
            <div class="kpi">
              <div class="kpi-val" :style="avgScore(s.id) !== null && avgScore(s.id) < 60 ? 'color:#e53e3e':''">{{ avgScore(s.id) !== null ? avgScore(s.id) + '%' : '—' }}</div>
              <div class="kpi-label">Avg Score</div>
            </div>
            <div class="kpi">
              <div class="kpi-val" :style="s.student_type === 'onsite' && avgAtt(s.id) < 75 ? 'color:#e53e3e' : 'color:#25a244'">
                {{ s.student_type === 'onsite' ? avgAtt(s.id) + '%' : lessonPct(s.id) + '%' }}
              </div>
              <div class="kpi-label">{{ s.student_type === 'onsite' ? 'Attendance' : 'Lessons' }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-val" :style="studentCerts(s.id).length ? 'color:#25a244':''">{{ studentCerts(s.id).length ? '✓' : '—' }}</div>
              <div class="kpi-label">Cert</div>
            </div>
          </div>
          <div v-if="riskFlags(s).length" class="risk-flag">⚠ {{ riskFlags(s).join(' · ') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useStudentsStore }    from '@/stores/students'
import { useCoursesStore }     from '@/stores/courses'
import { useExamsStore }       from '@/stores/exams'
import { useCertificatesStore } from '@/stores/certificates'
import { useAttendanceStore }  from '@/stores/attendance'

const studentsStore = useStudentsStore()
const coursesStore  = useCoursesStore()
const examsStore    = useExamsStore()
const certsStore    = useCertificatesStore()
const attStore      = useAttendanceStore()

const students    = computed(() => studentsStore.students)
const enrollments = computed(() => coursesStore.enrollments)
const results     = computed(() => examsStore.results)
const certs       = computed(() => certsStore.certificates)
const sessions    = computed(() => attStore.sessions)

function studentEnrollments(id) { return enrollments.value.filter(e => e.student === id) }
function studentCerts(id)       { return certs.value.filter(c => c.student === id) }
function studentResults(id)     { return results.value.filter(r => r.student === id) }

function avgScore(id) {
  const rs = studentResults(id)
  if (!rs.length) return null
  return Math.round(rs.reduce((s, r) => s + r.score, 0) / rs.length)
}

function avgAtt(id) {
  const enrs = studentEnrollments(id)
  if (!enrs.length) return 0
  const pcts = enrs.map(e => {
    const cs = sessions.value.filter(s => s.course === e.course)
    if (!cs.length) return 0
    const attended = cs.filter(s => s.attendee_ids?.includes(id)).length
    return Math.round((attended / cs.length) * 100)
  })
  return Math.round(pcts.reduce((a, v) => a + v, 0) / pcts.length)
}

function lessonPct(id) {
  const enrs = studentEnrollments(id)
  if (!enrs.length) return 0
  const pcts = enrs.map(e => e.lesson_completion_pct ?? 0)
  return Math.round(pcts.reduce((a, v) => a + v, 0) / pcts.length)
}

function riskFlags(s) {
  const flags = []
  const sc = avgScore(s.id)
  if (sc !== null && sc < 60) flags.push('Low exam score')
  if (s.student_type === 'onsite') {
    const att = avgAtt(s.id)
    if (att > 0 && att < 75) flags.push(`Attendance ${att}% < 75%`)
  }
  return flags
}

const atRisk       = computed(() => students.value.filter(s => riskFlags(s).length))
const sortedStudents = computed(() =>
  [...students.value].sort((a, b) => riskFlags(b).length - riskFlags(a).length || a.name.localeCompare(b.name))
)

onMounted(() => Promise.all([
  studentsStore.fetchStudents(),
  coursesStore.fetchCourses(),
  coursesStore.fetchEnrollments(),
  examsStore.fetchResults(),
  certsStore.fetchCertificates(),
  attStore.fetchSessions(),
]))
</script>

<style scoped>
.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 20px; }
.report-card { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; overflow: hidden; cursor: pointer; transition: box-shadow .2s, transform .15s; }
.report-card:hover { box-shadow: var(--lf-shadow-lg); transform: translateY(-2px); }
.report-card-strip { height: 6px; background: var(--lf-orange); }
.report-card-body  { padding: 18px; }
.kpi-row { display: flex; gap: 10px; margin-top: 14px; }
.kpi { flex: 1; background: var(--lf-gray-100); border-radius: 6px; padding: 10px; text-align: center; }
.kpi-val   { font-family: var(--lf-font-display); font-size: 24px; letter-spacing: .5px; }
.kpi-label { font-size: 10px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-400); margin-top: 2px; }
.risk-flag { display: flex; align-items: center; gap: 6px; margin-top: 10px; padding: 7px 10px; background: #fff5f5; border: 1.5px solid #feb2b2; border-radius: 6px; font-size: 12px; color: #c53030; font-weight: 600; }
</style>
