<template>
  <div class="page-content">

    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">{{ $t('attendance.stats.totalSessions') }}</div>
        <div class="stat-value">{{ sessions.length }}</div>
        <div class="stat-sub">{{ $t('attendance.stats.acrossCourses') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('attendance.stats.totalCheckins') }}</div>
        <div class="stat-value">{{ totalCheckins }}</div>
        <div class="stat-sub">{{ $t('attendance.stats.allCombined') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('attendance.stats.onsiteStudents') }}</div>
        <div class="stat-value">{{ onsiteStudents.length }}</div>
        <div class="stat-sub">{{ $t('attendance.stats.tracking') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('attendance.stats.belowThreshold') }}</div>
        <div class="stat-value">{{ atRiskCount }}</div>
        <div class="stat-sub">{{ $t('attendance.stats.needAttention') }}</div>
      </div>
    </div>

    <div class="lf-col-2">

      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">{{ $t('attendance.studentTable.title') }}</div>
          <RouterLink to="/reports" class="btn btn-ghost btn-sm">
            {{ $t('attendance.studentTable.fullReport') }}
          </RouterLink>
        </div>
        <p v-if="!onsiteStudents.length" class="text-muted text-sm">
          {{ $t('attendance.studentTable.empty') }}
        </p>
        <div v-else class="table-wrap">
          <table class="lf-table">
            <thead>
            <tr>
              <th>{{ $t('attendance.studentTable.headers.student') }}</th>
              <th>{{ $t('attendance.studentTable.headers.course') }}</th>
              <th>{{ $t('attendance.studentTable.headers.rate') }}</th>
              <th>{{ $t('attendance.studentTable.headers.status') }}</th>
            </tr>
            </thead>
            <tbody>
            <template v-for="s in onsiteStudents" :key="s.id">
              <tr v-for="e in studentEnrollments(s.id)" :key="e.id">
                <td><strong>{{ s.name }}</strong></td>
                <td class="text-muted">{{ e.course_title }}</td>
                <td>
                    <span :class="attClass(attStats(s.id, e.course).pct)">
                      {{ attStats(s.id, e.course).pct }}%
                    </span>
                </td>
                <td>
                  <span v-if="attStats(s.id, e.course).total === 0" class="badge badge-gray">
                    {{ $t('attendance.studentTable.status.noData') }}
                  </span>
                  <span v-else-if="attStats(s.id, e.course).pct >= courseThreshold(e.course)" class="badge badge-green">
                    ✓ {{ $t('attendance.studentTable.status.onTrack') }}
                  </span>
                  <span v-else class="badge badge-red">
                    ⚠ {{ $t('attendance.studentTable.status.below') }}
                  </span>
                </td>
              </tr>
            </template>
            </tbody>
          </table>
        </div>
      </div>

      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">{{ $t('attendance.sessionsLog.title') }}</div>
        </div>
        <EmptyState
            v-if="!sessions.length"
            icon="📋"
            :title="$t('attendance.sessionsLog.empty.title')"
            :message="$t('attendance.sessionsLog.empty.message')"
        />
        <div v-else class="table-wrap">
          <table class="lf-table">
            <thead>
            <tr>
              <th>{{ $t('attendance.sessionsLog.headers.date') }}</th>
              <th>{{ $t('attendance.sessionsLog.headers.course') }}</th>
              <th>{{ $t('attendance.sessionsLog.headers.code') }}</th>
              <th>{{ $t('attendance.sessionsLog.headers.attended') }}</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="s in sessions" :key="s.id">
              <td>{{ formatDate(s.date) }}</td>
              <td class="text-muted">{{ s.course_title }}</td>
              <td><span class="session-code">{{ s.code }}</span></td>
              <td>{{ s.attendee_count }}</td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import {computed, onMounted} from 'vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import {useCoursesStore} from '@/stores/courses'
import {useStudentsStore} from '@/stores/students'
import {useAttendanceStore} from '@/stores/attendance'
import {useI18n} from 'vue-i18n'

const {locale} = useI18n()
const coursesStore = useCoursesStore()
const studentsStore = useStudentsStore()
const attStore = useAttendanceStore()

const courses = computed(() => coursesStore.courses)
const sessions = computed(() => attStore.sessions)

const totalCheckins = computed(() =>
    sessions.value.reduce((s, sess) => s + sess.attendee_count, 0)
)

const onsiteStudents = computed(() =>
    studentsStore.students.filter(s => s.student_type === 'onsite')
)

const atRiskCount = computed(() => {
  let count = 0
  for (const s of onsiteStudents.value) {
    for (const e of studentEnrollments(s.id)) {
      const stats = attStats(s.id, e.course)
      const threshold = courseThreshold(e.course)
      if (stats.total > 0 && stats.pct < threshold) count++
    }
  }
  return count
})

function studentEnrollments(studentId) {
  return coursesStore.enrollments.filter(e => e.student === studentId)
}

function courseThreshold(courseId) {
  return courses.value.find(c => c.id === courseId)?.attendance_threshold ?? 75
}

function attStats(studentId, courseId) {
  const courseSessions = sessions.value.filter(s => s.course === courseId)
  const total = courseSessions.length
  const attended = courseSessions.filter(s => s.attendee_ids?.includes(studentId)).length
  const pct = total > 0 ? Math.round((attended / total) * 100) : 0
  return {attended, total, pct}
}

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

function formatDate(d) {
  const dateLocale = locale.value === 'mn' ? 'mn-MN' : 'en-GB'
  return new Date(d).toLocaleDateString(dateLocale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

onMounted(() => Promise.all([
  coursesStore.fetchCourses(),
  coursesStore.fetchEnrollments(),
  studentsStore.fetchStudents(),
  attStore.fetchSessions(),
]))
</script>