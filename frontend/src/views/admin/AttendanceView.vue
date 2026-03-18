<template>
  <div class="page-content">
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
    </div>

    <div v-for="course in courses" :key="course.id" class="lf-card" style="margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
        <div>
          <div class="card-title">{{ course.title }}</div>
          <div class="text-muted text-sm">Threshold: {{ course.attendance_threshold }}%</div>
        </div>
        <RouterLink :to="`/courses/${course.id}`" class="btn btn-ghost btn-sm">Manage →</RouterLink>
      </div>

      <p v-if="!onsiteEnrolled(course.id).length" class="text-muted text-sm">No on-site students enrolled.</p>
      <table v-else class="lf-table">
        <thead><tr><th>Student</th><th>Attended</th><th>Sessions</th><th>Rate</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="s in onsiteEnrolled(course.id)" :key="s.id">
            <td><strong>{{ s.name }}</strong><br><span class="text-muted text-sm">{{ s.email }}</span></td>
            <td>{{ attStats(s.id, course.id).attended }}</td>
            <td>{{ attStats(s.id, course.id).total }}</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="progress-bar" style="width:80px"><div class="progress-fill" :style="{ width: attStats(s.id, course.id).pct + '%' }" /></div>
                <span :class="attClass(attStats(s.id, course.id).pct)">{{ attStats(s.id, course.id).pct }}%</span>
              </div>
            </td>
            <td>
              <span v-if="attStats(s.id, course.id).pct >= course.attendance_threshold" class="badge badge-green">✓ On track</span>
              <span v-else-if="attStats(s.id, course.id).total === 0" class="badge badge-gray">No data</span>
              <span v-else class="badge badge-red">⚠ Below threshold</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="lf-card">
      <div class="card-title" style="margin-bottom:14px">All Sessions Log</div>
      <EmptyState v-if="!sessions.length" icon="📋" title="No sessions yet" message="Go into a course → Sessions tab to create one." />
      <table v-else class="lf-table">
        <thead><tr><th>Date</th><th>Course</th><th>Label</th><th>Code</th><th>Attended</th></tr></thead>
        <tbody>
          <tr v-for="s in sessions" :key="s.id">
            <td>{{ formatDate(s.date) }}</td>
            <td>{{ s.course_title }}</td>
            <td>{{ s.label }}</td>
            <td><span class="session-code">{{ s.code }}</span></td>
            <td>{{ s.attendee_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted }   from 'vue'
import EmptyState                from '@/components/ui/EmptyState.vue'
import { useCoursesStore }       from '@/stores/courses'
import { useStudentsStore }      from '@/stores/students'
import { useAttendanceStore }    from '@/stores/attendance'

const coursesStore  = useCoursesStore()
const studentsStore = useStudentsStore()
const attStore      = useAttendanceStore()

const courses  = computed(() => coursesStore.courses)
const sessions = computed(() => attStore.sessions)

const totalCheckins = computed(() => sessions.value.reduce((s, sess) => s + sess.attendee_count, 0))

function onsiteEnrolled(courseId) {
  return studentsStore.students.filter(s => s.student_type === 'onsite')
}

function attStats(studentId, courseId) {
  const courseSessions = sessions.value.filter(s => s.course === courseId || s.course_title === courses.value.find(c=>c.id===courseId)?.title)
  const total    = courseSessions.length
  const attended = courseSessions.filter(s => s.attendee_ids?.includes(studentId)).length
  const pct      = total > 0 ? Math.round((attended / total) * 100) : 0
  return { attended, total, pct }
}

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(() => Promise.all([
  coursesStore.fetchCourses(),
  studentsStore.fetchStudents(),
  attStore.fetchSessions(),
]))
</script>

<style scoped>
.lf-table { width: 100%; border-collapse: collapse; }
.lf-table th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; letter-spacing: .7px; text-transform: uppercase; color: var(--lf-gray-600); border-bottom: 2px solid var(--lf-gray-200); }
.lf-table td { padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--lf-gray-200); vertical-align: middle; }
.lf-table tr:last-child td { border-bottom: none; }
.session-code { font-family: monospace; font-weight: 700; letter-spacing: 3px; color: var(--lf-orange); background: var(--lf-orange-light); padding: 2px 8px; border-radius: 4px; font-size: 14px; }
.btn { display: inline-flex; align-items: center; padding: 6px 14px; border: 1px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-size: 12px; font-weight: 600; cursor: pointer; background: transparent; color: var(--lf-gray-600); text-decoration: none; transition: all .15s; }
.btn:hover { border-color: var(--lf-black); color: var(--lf-black); }
</style>
