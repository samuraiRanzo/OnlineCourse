<template>
  <div class="page-content">
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">{{ $t('reports.stats.students') }}</div>
        <div class="stat-value">{{ students.length }}</div>
      </div>
      <div class="stat-card" :class="{ accent: atRisk.length }">
        <div class="stat-label">{{ $t('reports.stats.atRisk') }}</div>
        <div class="stat-value" :style="!atRisk.length ? 'color:var(--lf-gray-400)' : ''">
          {{ atRisk.length }}
        </div>
        <div class="stat-sub">{{ $t('reports.stats.needAttention') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('reports.stats.certificates') }}</div>
        <div class="stat-value">{{ certs.length }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('reports.stats.gradesLoaded') }}</div>
        <div class="stat-value" :style="gradesLoading ? 'color:var(--lf-gray-400)' : 'color:#25a244'">
          {{ gradesLoading ? '…' : uniqueCourseIds.length }}
        </div>
        <div class="stat-sub">{{ $t('reports.stats.courses') }}</div>
      </div>
    </div>

    <div v-if="gradesLoading" style="text-align:center;padding:40px;color:var(--lf-gray-400);font-size:14px">
      <div class="spinner" style="margin:0 auto 12px"/>
      {{ $t('reports.loading') }}
    </div>

    <div v-else class="courses-grid">
      <div
          v-for="s in sortedStudents"
          :key="s.id"
          class="report-card"
          :class="{ 'at-risk': riskFlags(s).length }"
          @click="$router.push(`/reports/${s.id}`)"
      >
        <div class="report-card-strip" :style="riskFlags(s).length ? 'background:#e53e3e' : ''"/>
        <div class="report-card-body">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div style="font-family:var(--lf-font-display);font-size:20px;letter-spacing:.3px">
                {{ s.name }}
              </div>
              <div class="text-muted text-sm">{{ s.email }}</div>
            </div>
            <span :class="['type-pill', `type-${s.student_type}`]">
              {{ s.student_type === 'online' ? '💻' : '🏫' }} {{ s.student_type }}
            </span>
          </div>

          <div class="kpi-row">
            <div class="kpi">
              <div class="kpi-val">{{ studentEnrollments(s.id).length }}</div>
              <div class="kpi-label">{{ $t('reports.card.courses') }}</div>
            </div>

            <div class="kpi">
              <div
                  class="kpi-val"
                  :style="avgFinalGrade(s.id) !== null && avgFinalGrade(s.id) < 60
                  ? 'color:#e53e3e' : ''"
              >
                {{ avgFinalGrade(s.id) !== null ? avgFinalGrade(s.id) + '%' : '—' }}
              </div>
              <div class="kpi-label">{{ $t('reports.card.grade') }}</div>
            </div>

            <div class="kpi">
              <div
                  class="kpi-val"
                  :style="s.student_type === 'onsite' && avgAtt(s.id) > 0 && avgAtt(s.id) < 75
                  ? 'color:#e53e3e' : 'color:#25a244'"
              >
                {{ s.student_type === 'onsite' ? avgAtt(s.id) + '%' : lessonPct(s.id) + '%' }}
              </div>
              <div class="kpi-label">
                {{ s.student_type === 'onsite' ? $t('reports.card.attendance') : $t('reports.card.lessons') }}
              </div>
            </div>

            <div class="kpi">
              <div class="kpi-val" :style="studentCerts(s.id).length ? 'color:#25a244' : ''">
                {{ studentCerts(s.id).length ? '✓' : '—' }}
              </div>
              <div class="kpi-label">{{ $t('reports.card.cert') }}</div>
            </div>
          </div>

          <div v-if="riskFlags(s).length" class="risk-flag">
            ⚠ {{ riskFlags(s).join(' · ') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import api from '@/api'
import {useStudentsStore} from '@/stores/students'
import {useCoursesStore} from '@/stores/courses'
import {useCertificatesStore} from '@/stores/certificates'
import {useAttendanceStore} from '@/stores/attendance'
import {useI18n} from 'vue-i18n'

const {t} = useI18n()
const studentsStore = useStudentsStore()
const coursesStore = useCoursesStore()
const certsStore = useCertificatesStore()
const attStore = useAttendanceStore()

const students = computed(() => studentsStore.students)
const enrollments = computed(() => coursesStore.enrollments)
const certs = computed(() => certsStore.certificates)
const sessions = computed(() => attStore.sessions)

const gradesByCourse = ref({})
const gradesLoading = ref(false)

const uniqueCourseIds = computed(() => [
  ...new Set(enrollments.value.map(e => e.course)),
])

async function loadAllGrades() {
  if (!uniqueCourseIds.value.length) return
  gradesLoading.value = true
  try {
    await Promise.all(
        uniqueCourseIds.value.map(async (courseId) => {
          try {
            const {data} = await api.get(`/courses/${courseId}/final-grade/`)
            gradesByCourse.value[courseId] = data
          } catch {
            // Course may have no data yet
          }
        })
    )
  } finally {
    gradesLoading.value = false
  }
}

function getStudentGradeForCourse(studentId, courseId) {
  const courseData = gradesByCourse.value[courseId]
  if (!courseData?.students) return null
  return courseData.students.find(s => s.student_id === String(studentId)) ?? null
}

function avgFinalGrade(studentId) {
  const enrs = studentEnrollments(studentId)
  if (!enrs.length) return null
  const grades = enrs
      .map(e => getStudentGradeForCourse(studentId, e.course)?.final_grade)
      .filter(g => g !== null && g !== undefined)
  if (!grades.length) return null
  return Math.round(grades.reduce((a, b) => a + b, 0) / grades.length)
}

function passingScore(courseId) {
  return gradesByCourse.value[courseId]?.passing_score ?? 60
}

function studentEnrollments(id) {
  return enrollments.value.filter(e => e.student === id)
}

function studentCerts(id) {
  return certs.value.filter(c => c.student === id)
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
  const enrs = studentEnrollments(s.id)

  for (const enr of enrs) {
    const grade = getStudentGradeForCourse(s.id, enr.course)
    if (grade?.final_grade !== null && grade?.final_grade !== undefined) {
      if (grade.final_grade < passingScore(enr.course)) {
        flags.push(t('reports.card.riskLabel'))
        break
      }
    }
  }

  if (s.student_type === 'onsite') {
    const att = avgAtt(s.id)
    if (att > 0 && att < 75) {
      flags.push(t('reports.card.riskAttendance', {pct: att}))
    }
  }

  return flags
}

const atRisk = computed(() =>
    students.value.filter(s => riskFlags(s).length)
)

const sortedStudents = computed(() =>
    [...students.value].sort(
        (a, b) =>
            riskFlags(b).length - riskFlags(a).length ||
            a.name.localeCompare(b.name)
    )
)

onMounted(async () => {
  await Promise.all([
    studentsStore.fetchStudents(),
    coursesStore.fetchCourses(),
    coursesStore.fetchEnrollments(),
    certsStore.fetchCertificates(),
    attStore.fetchSessions(),
  ])
  await loadAllGrades()
})
</script>

<style scoped>
.courses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.report-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow .2s, transform .15s;
}

.report-card:hover {
  box-shadow: var(--lf-shadow-lg);
  transform: translateY(-2px);
}

.report-card-strip {
  height: 6px;
  background: var(--lf-orange);
}

.report-card-body {
  padding: 18px;
}

.kpi-row {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.kpi {
  flex: 1;
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 10px;
  text-align: center;
}

.kpi-val {
  font-family: var(--lf-font-display);
  font-size: 24px;
  letter-spacing: .5px;
}

.kpi-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--lf-gray-400);
  margin-top: 2px;
}

.risk-flag {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 7px 10px;
  background: #fff5f5;
  border: 1.5px solid #feb2b2;
  border-radius: 6px;
  font-size: 12px;
  color: #c53030;
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
</style>