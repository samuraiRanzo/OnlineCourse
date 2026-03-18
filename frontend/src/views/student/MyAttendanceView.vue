<template>
  <div class="page-content">
    <div style="display:flex;justify-content:flex-end;margin-bottom:20px">
      <RouterLink to="/check-in" class="btn btn-primary btn-sm">📋 Check In →</RouterLink>
    </div>

    <EmptyState
      v-if="!enrollments.length"
      icon="📋"
      title="Not enrolled yet"
      message="Ask your teacher to enroll you in a course."
    />

    <div v-for="e in enriched" :key="e.id" class="lf-card" style="margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;flex-wrap:wrap;gap:10px">
        <div>
          <div class="card-title">{{ e.course.title }}</div>
          <div class="text-muted text-sm">Required: {{ e.course.attendance_threshold }}% attendance</div>
        </div>
        <div style="text-align:right">
          <div :class="attClass(e.stats.pct)" style="font-size:32px;font-family:var(--lf-font-display)">{{ e.stats.pct }}%</div>
          <div class="text-muted text-sm">{{ e.stats.attended }}/{{ e.stats.total }} sessions</div>
        </div>
      </div>

      <div class="progress-bar" style="height:10px;margin-bottom:6px">
        <div class="progress-fill" :style="{ width: e.stats.pct + '%' }" />
      </div>
      <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--lf-gray-600);margin-bottom:16px">
        <span>0%</span>
        <span style="color:var(--lf-orange)">Threshold: {{ e.course.attendance_threshold }}%</span>
        <span>100%</span>
      </div>

      <!-- Status alert -->
      <div
        v-if="e.stats.pct < e.course.attendance_threshold && e.stats.total > 0"
        style="background:#fff5f5;border:1.5px solid #e53e3e;border-radius:6px;padding:12px;margin-bottom:14px;font-size:13px;color:#e53e3e"
      >
        ⚠️ Your attendance is below the required threshold.
      </div>
      <div
        v-else-if="e.stats.pct >= e.course.attendance_threshold && e.stats.total > 0"
        style="background:#e6f7ee;border:1.5px solid #25a244;border-radius:6px;padding:12px;margin-bottom:14px;font-size:13px;color:#25a244"
      >
        ✓ You're meeting the attendance requirement!
      </div>

      <!-- Session log -->
      <p v-if="!e.sessions.length" class="text-muted text-sm">No sessions scheduled yet.</p>
      <table v-else class="lf-table">
        <thead><tr><th>Date</th><th>Session</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="s in e.sessions" :key="s.id">
            <td>{{ formatDate(s.date) }}</td>
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
</template>

<script setup>
import { computed, onMounted }   from 'vue'
import { useAuthStore }          from '@/stores/auth'
import { useCoursesStore }       from '@/stores/courses'
import { useAttendanceStore }    from '@/stores/attendance'
import EmptyState                from '@/components/ui/EmptyState.vue'

const auth    = useAuthStore()
const courses = useCoursesStore()
const attStore = useAttendanceStore()

const enrollments = computed(() => courses.enrollments)
const allSessions = computed(() => attStore.sessions)

const enriched = computed(() =>
  enrollments.value.map(e => {
    const course   = courses.courses.find(c => c.id === e.course)
    if (!course) return null
    const sessions = allSessions.value.filter(s => s.course === e.course).sort((a, b) => new Date(b.date) - new Date(a.date))
    const total    = sessions.length
    const attended = sessions.filter(s => s.attendee_ids?.includes(auth.user?.id)).length
    const pct      = total > 0 ? Math.round((attended / total) * 100) : 0
    return { id: e.id, course, sessions, stats: { attended, total, pct } }
  }).filter(Boolean)
)

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(() => Promise.all([
  courses.fetchCourses(),
  courses.fetchEnrollments(),
  attStore.fetchSessions(),
]))
</script>

<style scoped>
.lf-table { width: 100%; border-collapse: collapse; }
.lf-table th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; letter-spacing: .7px; text-transform: uppercase; color: var(--lf-gray-600); border-bottom: 2px solid var(--lf-gray-200); }
.lf-table td { padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--lf-gray-200); }
.lf-table tr:last-child td { border-bottom: none; }
.btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; text-decoration: none; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover { background: var(--lf-orange-dark); }
.btn-sm { padding: 6px 14px; font-size: 12px; }
</style>
