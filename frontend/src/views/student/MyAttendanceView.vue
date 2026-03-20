<template>
  <div class="page-content">

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">Courses Enrolled</div>
        <div class="stat-value">{{ enriched.length }}</div>
        <div class="stat-sub">Active this term</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Sessions Attended</div>
        <div class="stat-value">{{ totalAttended }}</div>
        <div class="stat-sub">Out of {{ totalSessions }} total</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Overall Rate</div>
        <div class="stat-value" :class="attClass(overallPct)">{{ overallPct }}%</div>
        <div class="stat-sub">Across all courses</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">At Risk</div>
        <div class="stat-value" :style="atRiskCount ? 'color:var(--lf-red)' : ''">{{ atRiskCount }}</div>
        <div class="stat-sub">Below threshold</div>
      </div>
    </div>

    <EmptyState
        v-if="!enriched.length"
        icon="📋"
        title="Not enrolled yet"
        message="Ask your teacher to enroll you in a course."
    />

    <div v-else class="lf-col-2">

      <!-- Left: per-course summary -->
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">Course Summary</div>
          <RouterLink to="/check-in" class="btn btn-primary btn-sm">📋 Check In →</RouterLink>
        </div>
        <table class="lf-table">
          <thead>
          <tr>
            <th>Course</th>
            <th>Attended</th>
            <th>Rate</th>
            <th>Status</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="e in enriched" :key="e.id">
            <td><strong>{{ e.course.title }}</strong></td>
            <td class="text-muted">{{ e.stats.attended }}/{{ e.stats.total }}</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="progress-bar" style="width:60px">
                  <div class="progress-fill" :style="{ width: e.stats.pct + '%' }"/>
                </div>
                <span :class="attClass(e.stats.pct)">{{ e.stats.pct }}%</span>
              </div>
            </td>
            <td>
              <span v-if="e.stats.total === 0" class="badge badge-gray">No data</span>
              <span v-else-if="e.stats.pct >= e.course.attendance_threshold" class="badge badge-green">✓ On track</span>
              <span v-else class="badge badge-red">⚠ Below</span>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- Right: session log for selected / all courses -->
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">Sessions Log</div>
          <select v-model="selectedCourse" class="lf-select"
                  style="width:auto;font-size:13px;padding:5px 28px 5px 10px">
            <option value="">All Courses</option>
            <option v-for="e in enriched" :key="e.id" :value="e.course.id">{{ e.course.title }}</option>
          </select>
        </div>
        <EmptyState v-if="!filteredSessions.length" icon="📅" title="No sessions yet" message=""/>
        <div v-else class="table-wrap">
          <table class="lf-table">
            <thead>
            <tr>
              <th>Date</th>
              <th>Course</th>
              <th>Label</th>
              <th>Status</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="s in filteredSessions" :key="s.id">
              <td>{{ formatDate(s.date) }}</td>
              <td class="text-muted">{{ s.course_title }}</td>
              <td>{{ s.label }}</td>
              <td>
                <span v-if="s.attendee_ids?.includes(auth.user?.id)" class="badge badge-green">✓ Present</span>
                <span v-else class="badge badge-gray">Absent</span>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import {useAuthStore} from '@/stores/auth'
import {useCoursesStore} from '@/stores/courses'
import {useAttendanceStore} from '@/stores/attendance'
import EmptyState from '@/components/ui/EmptyState.vue'

const auth = useAuthStore()
const courses = useCoursesStore()
const attStore = useAttendanceStore()

const selectedCourse = ref('')

const enrollments = computed(() => courses.enrollments)
const allSessions = computed(() => attStore.sessions)

const enriched = computed(() =>
    enrollments.value.map(e => {
      const course = courses.courses.find(c => c.id === e.course)
      if (!course) return null
      const sessions = allSessions.value
          .filter(s => s.course === e.course)
          .sort((a, b) => new Date(b.date) - new Date(a.date))
      const total = sessions.length
      const attended = sessions.filter(s => s.attendee_ids?.includes(auth.user?.id)).length
      const pct = total > 0 ? Math.round((attended / total) * 100) : 0
      return {id: e.id, course, sessions, stats: {attended, total, pct}}
    }).filter(Boolean)
)

const totalAttended = computed(() =>
    enriched.value.reduce((sum, e) => sum + e.stats.attended, 0)
)
const totalSessions = computed(() =>
    enriched.value.reduce((sum, e) => sum + e.stats.total, 0)
)
const overallPct = computed(() =>
    totalSessions.value > 0
        ? Math.round((totalAttended.value / totalSessions.value) * 100)
        : 0
)
const atRiskCount = computed(() =>
    enriched.value.filter(e =>
        e.stats.total > 0 && e.stats.pct < e.course.attendance_threshold
    ).length
)

const filteredSessions = computed(() => {
  const flat = enriched.value.flatMap(e => e.sessions)
  if (!selectedCourse.value) return flat
  return flat.filter(s => s.course === selectedCourse.value)
})

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {day: '2-digit', month: 'short', year: 'numeric'})
}

onMounted(() => Promise.all([
  courses.fetchCourses(),
  courses.fetchEnrollments(),
  attStore.fetchSessions(),
]))
</script>
<!-- No scoped styles — all classes live in main.css -->