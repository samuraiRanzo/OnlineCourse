<template>
  <div>
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">Enrolled Courses</div>
        <div class="stat-value">{{ enrollments.length }}</div>
        <div class="stat-sub">{{ auth.isOnsite ? '🏫 On-site track' : '💻 Online track' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Exams Taken</div>
        <div class="stat-value">{{ results.length }}</div>
      </div>
      <div class="stat-card" v-if="auth.isOnsite">
        <div class="stat-label">Avg Attendance</div>
        <div class="stat-value text-orange">{{ avgAtt }}%</div>
      </div>
      <div class="stat-card" v-else>
        <div class="stat-label">Best Score</div>
        <div class="stat-value">{{ bestScore }}</div>
      </div>
    </div>

    <!-- Unread notices -->
    <div v-if="unreadNotices.length" style="margin-bottom:20px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div class="display" style="font-size:20px;letter-spacing:.5px">📣 Notices</div>
        <RouterLink to="/notices" class="btn btn-ghost btn-sm">View all</RouterLink>
      </div>
      <div
        v-for="n in unreadNotices.slice(0,3)" :key="n.id"
        class="notice-banner"
        :class="{ pinned: n.pinned }"
        @click="goToNotices(n.id)"
      >
        <div class="notice-unread-dot" />
        <div class="notice-banner-body">
          <div class="notice-banner-title">{{ n.pinned ? '📌 ' : '' }}{{ n.title }}</div>
          <div class="notice-banner-meta text-muted text-sm">{{ n.course_title }} · {{ formatDate(n.created_at) }}</div>
          <div class="notice-banner-text text-muted text-sm">{{ n.body }}</div>
        </div>
        <span style="font-size:18px;color:var(--lf-gray-400)">›</span>
      </div>
    </div>

    <!-- Courses -->
    <div class="lf-card">
      <div class="card-title" style="margin-bottom:16px">Your Courses</div>
      <p v-if="!enriched.length" class="text-muted text-sm">You are not enrolled in any courses yet.</p>
      <div
        v-for="e in enriched" :key="e.id"
        style="display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--lf-gray-200)"
      >
        <div style="flex:1">
          <div style="font-weight:600;font-size:15px">{{ e.course_title }}</div>
          <div v-if="auth.isOnsite" style="margin-top:6px;display:flex;align-items:center;gap:12px">
            <span class="text-muted text-sm">Attendance</span>
            <div class="progress-bar" style="width:120px"><div class="progress-fill" :style="{ width: (e.lesson_completion_pct ?? 0) + '%' }" /></div>
          </div>
          <div v-else style="margin-top:6px;display:flex;align-items:center;gap:10px">
            <div class="progress-bar" style="width:160px"><div class="progress-fill" :style="{ width: (e.lesson_completion_pct ?? 0) + '%' }" /></div>
            <span class="text-muted text-sm">{{ e.lesson_completion_pct ?? 0 }}%</span>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <span v-if="courseResult(e.course)" class="badge badge-green">Exam: {{ courseResult(e.course).score }}%</span>
          <button class="btn btn-primary btn-sm" @click="$router.push(`/my-courses/${e.course}`)">Continue →</button>
        </div>
      </div>
    </div>

    <div v-if="auth.isOnsite" class="lf-card" style="margin-top:20px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
        <div class="card-title">Quick Check-In</div>
        <RouterLink to="/check-in" class="btn btn-primary btn-sm">Open Check-In →</RouterLink>
      </div>
      <p class="text-muted text-sm">Ask your teacher for today's session code.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter }              from 'vue-router'
import { useAuthStore }           from '@/stores/auth'
import { useCoursesStore }        from '@/stores/courses'
import { useExamsStore }          from '@/stores/exams'
import { useAnnouncementsStore }  from '@/stores/announcements'

const auth     = useAuthStore()
const courses  = useCoursesStore()
const exams    = useExamsStore()
const annStore = useAnnouncementsStore()
const router   = useRouter()

const enrollments    = computed(() => courses.enrollments)
const results        = computed(() => exams.results)
const enriched       = computed(() => enrollments.value)
const unreadNotices  = computed(() => annStore.announcements.filter(a => !a.is_read))

const bestScore = computed(() => {
  if (!results.value.length) return '—'
  return Math.max(...results.value.map(r => r.score)) + '%'
})

const avgAtt = computed(() => 0) // derived from attendance store in a real view

function courseResult(courseId) {
  return results.value.find(r => r.course_id === courseId) ?? null
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

async function goToNotices(id) {
  await annStore.markRead(id)
  router.push('/notices')
}

onMounted(() => Promise.all([
  courses.fetchEnrollments(),
  exams.fetchResults(),
  annStore.fetchAnnouncements(),
]))
</script>

<style scoped>
.notice-banner { display: flex; align-items: flex-start; gap: 14px; padding: 14px 18px; background: var(--lf-orange-light); border: 1.5px solid var(--lf-orange); border-radius: 8px; margin-bottom: 12px; cursor: pointer; transition: background .15s; }
.notice-banner:hover { background: #fde8d0; }
.notice-banner.pinned { border-color: var(--lf-black); background: var(--lf-gray-100); }
.notice-unread-dot { width: 8px; height: 8px; background: var(--lf-orange); border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.notice-banner-title { font-size: 14px; font-weight: 600; color: var(--lf-black); }
.notice-banner-text  { margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.btn { display: inline-flex; align-items: center; padding: 6px 14px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; text-decoration: none; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover { background: var(--lf-orange-dark); }
.btn-ghost { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-sm { padding: 6px 14px; font-size: 12px; }
</style>
