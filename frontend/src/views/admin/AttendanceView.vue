<template>
  <div class="page-content">

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">Total Sessions</div>
        <div class="stat-value">{{ sessions.length }}</div>
        <div class="stat-sub">Across all courses</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Check-ins</div>
        <div class="stat-value">{{ totalCheckins }}</div>
        <div class="stat-sub">All sessions combined</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">On-site Students</div>
        <div class="stat-value">{{ onsiteStudents.length }}</div>
        <div class="stat-sub">Tracking attendance</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Below Threshold</div>
        <div class="stat-value">{{ atRiskCount }}</div>
        <div class="stat-sub">Need attention</div>
      </div>
    </div>

    <!-- Two-column layout matching AdminDashboard -->
    <div class="lf-col-2">

      <!-- Left: Per-student attendance summary -->
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">Student Attendance</div>
          <RouterLink to="/reports" class="btn btn-ghost btn-sm">Full Report</RouterLink>
        </div>
        <p v-if="!onsiteStudents.length" class="text-muted text-sm">No on-site students enrolled.</p>
        <div v-else class="table-wrap">
          <table class="lf-table">
            <thead>
            <tr>
              <th>Student</th>
              <th>Course</th>
              <th>Rate</th>
              <th>Status</th>
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
                  <span v-if="attStats(s.id, e.course).total === 0" class="badge badge-gray">No data</span>
                  <span v-else-if="attStats(s.id, e.course).pct >= courseThreshold(e.course)" class="badge badge-green">✓ On track</span>
                  <span v-else class="badge badge-red">⚠ Below</span>
                </td>
              </tr>
            </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Right: Sessions log -->
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">Sessions Log</div>
        </div>
        <EmptyState v-if="!sessions.length" icon="📋" title="No sessions yet"
                    message="Go into a course → Sessions tab to create one."/>
        <div v-else class="table-wrap">
          <table class="lf-table">
            <thead>
            <tr>
              <th>Date</th>
              <th>Course</th>
              <th>Code</th>
              <th>Attended</th>
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
  return new Date(d).toLocaleDateString('en-GB', {day: '2-digit', month: 'short', year: 'numeric'})
}

onMounted(() => Promise.all([
  coursesStore.fetchCourses(),
  coursesStore.fetchEnrollments(),
  studentsStore.fetchStudents(),
  attStore.fetchSessions(),
]))
</script>
