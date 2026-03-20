<template>
  <div class="page-content">

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">Enrolled Courses</div>
        <div class="stat-value">{{ enrollments.length }}</div>
        <div class="stat-sub">{{ auth.isOnsite ? '🏫 On-site' : '💻 Online' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Exams Taken</div>
        <div class="stat-value">{{ results.length }}</div>
        <div class="stat-sub">{{ results.length ? 'Best: ' + bestScore : 'None yet' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ auth.isOnsite ? 'Avg Attendance' : 'Avg Progress' }}</div>
        <div class="stat-value" :class="auth.isOnsite ? 'text-orange' : ''">
          {{ auth.isOnsite ? avgAtt + '%' : avgProgress + '%' }}
        </div>
        <div class="stat-sub">Across all courses</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Unread Notices</div>
        <div class="stat-value" :style="unreadNotices.length ? 'color:var(--lf-orange)' : ''">
          {{ unreadNotices.length }}
        </div>
        <div class="stat-sub">From your teachers</div>
      </div>
    </div>

    <!-- Two-column layout -->
    <div class="lf-col-2">

      <!-- Left: My Courses -->
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">My Courses</div>
          <RouterLink to="/my-courses" class="btn btn-ghost btn-sm">View all</RouterLink>
        </div>
        <EmptyState v-if="!enriched.length" icon="📚" title="No courses yet"
                    message="Ask your teacher to enroll you."/>
        <table v-else class="lf-table">
          <thead>
          <tr>
            <th>Course</th>
            <th>{{ auth.isOnsite ? 'Attendance' : 'Progress' }}</th>
            <th>Exam</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="e in enriched" :key="e.id">
            <td><strong>{{ e.course_title }}</strong></td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="progress-bar" style="width:60px">
                  <div class="progress-fill" :style="{ width: (e.lesson_completion_pct ?? 0) + '%' }"/>
                </div>
                <span class="text-muted text-sm">{{ e.lesson_completion_pct ?? 0 }}%</span>
              </div>
            </td>
            <td>
                <span v-if="courseResult(e.course)" class="badge badge-green">
                  {{ courseResult(e.course).score }}%
                </span>
              <span v-else class="badge badge-gray">—</span>
            </td>
            <td>
              <button class="btn btn-primary btn-sm"
                      @click="$router.push(`/my-courses/${e.course}`)">
                Go →
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- Right: Notices or Check-In -->
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">
            {{ unreadNotices.length ? '📣 Notices' : 'Notices' }}
          </div>
          <RouterLink to="/notices" class="btn btn-ghost btn-sm">View all</RouterLink>
        </div>

        <EmptyState v-if="!unreadNotices.length" icon="📭" title="All caught up"
                    message="No unread notices from your teachers."/>

        <div v-else>
          <div
              v-for="n in unreadNotices.slice(0, 4)" :key="n.id"
              class="notice-banner"
              :class="{ pinned: n.pinned }"
              @click="goToNotices(n.id)"
          >
            <div class="notice-unread-dot"></div>
            <div class="notice-banner-body">
              <div class="notice-banner-title">{{ n.pinned ? '📌 ' : '' }}{{ n.title }}</div>
              <div class="text-muted text-sm">{{ n.course_title }} · {{ formatDate(n.created_at) }}</div>
              <div class="notice-banner-text text-muted text-sm">{{ n.body }}</div>
            </div>
            <span style="font-size:18px;color:var(--lf-gray-400)">›</span>
          </div>
        </div>

        <!-- On-site: quick check-in CTA at the bottom -->
        <div v-if="auth.isOnsite"
             style="margin-top:16px;padding-top:16px;border-top:1px solid var(--lf-gray-200)">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div>
              <div style="font-weight:600;font-size:14px">Quick Check-In</div>
              <div class="text-muted text-sm">Ask your teacher for today's code</div>
            </div>
            <RouterLink to="/check-in" class="btn btn-primary btn-sm">Check In →</RouterLink>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import {computed, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import {useCoursesStore} from '@/stores/courses'
import {useExamsStore} from '@/stores/exams'
import {useAnnouncementsStore} from '@/stores/announcements'
import {useAttendanceStore} from '@/stores/attendance'
import EmptyState from '@/components/ui/EmptyState.vue'

const auth = useAuthStore()
const courses = useCoursesStore()
const exams = useExamsStore()
const annStore = useAnnouncementsStore()
const attStore = useAttendanceStore()
const router = useRouter()

const enrollments = computed(() => courses.enrollments)
const results = computed(() => exams.results)
const enriched = computed(() => enrollments.value)
const unreadNotices = computed(() => annStore.announcements.filter(a => !a.is_read))

const bestScore = computed(() => {
  if (!results.value.length) return '—'
  return Math.max(...results.value.map(r => r.score)) + '%'
})

const avgProgress = computed(() => {
  if (!enriched.value.length) return 0
  const sum = enriched.value.reduce((s, e) => s + (e.lesson_completion_pct ?? 0), 0)
  return Math.round(sum / enriched.value.length)
})

const avgAtt = computed(() => {
  const sessions = attStore.sessions
  if (!sessions.length || !auth.user) return 0
  const enrolled = enrollments.value.map(e => e.course)
  const relevant = sessions.filter(s => enrolled.includes(s.course))
  if (!relevant.length) return 0
  const attended = relevant.filter(s => s.attendee_ids?.includes(auth.user.id)).length
  return Math.round((attended / relevant.length) * 100)
})

function courseResult(courseId) {
  return results.value.find(r => r.course_id === courseId) ?? null
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {day: '2-digit', month: 'short', year: 'numeric'})
}

async function goToNotices(id) {
  await annStore.markRead(id)
  router.push('/notices')
}

onMounted(() => Promise.all([
  courses.fetchEnrollments(),
  exams.fetchResults(),
  annStore.fetchAnnouncements(),
  auth.isOnsite ? attStore.fetchSessions() : Promise.resolve(),
]))
</script>

<style scoped>
/* Notice banner — view-specific interactive card, not a global utility */
.notice-banner {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 14px;
  background: var(--lf-orange-light);
  border: 1.5px solid var(--lf-orange);
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background .15s;
}

.notice-banner:hover {
  background: #fde8d0;
}

.notice-banner.pinned {
  border-color: var(--lf-black);
  background: var(--lf-gray-100);
}

.notice-unread-dot {
  width: 8px;
  height: 8px;
  background: var(--lf-orange);
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}

.notice-banner-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--lf-black);
}

.notice-banner-text {
  margin-top: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>