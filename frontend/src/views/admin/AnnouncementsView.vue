<template>
  <div class="page-content">
    <div class="stats-grid">
      <div class="stat-card accent"><div class="stat-label">Total Notices</div><div class="stat-value">{{ announcements.length }}</div></div>
      <div class="stat-card"><div class="stat-label">Pinned</div><div class="stat-value">{{ pinned }}</div></div>
    </div>

    <div v-for="course in courses" :key="course.id" class="lf-card" style="margin-bottom:20px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <div>
          <div class="card-title">{{ course.title }}</div>
          <div class="text-muted text-sm">{{ courseAnn(course.id).length }} announcement(s)</div>
        </div>
        <RouterLink :to="`/courses/${course.id}`" class="btn btn-ghost btn-sm">Manage →</RouterLink>
      </div>
      <p v-if="!courseAnn(course.id).length" class="text-muted text-sm">No announcements for this course.</p>
      <div v-for="n in courseAnn(course.id)" :key="n.id" class="notice-card" :class="{ pinned: n.pinned }">
        <div class="notice-card-header">
          <span>{{ n.pinned ? '📌' : '📣' }}</span>
          <div style="flex:1">
            <div style="font-weight:600">{{ n.title }}</div>
            <div class="text-muted text-sm">{{ formatDate(n.created_at) }}</div>
          </div>
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost btn-sm" @click="togglePin(n)">{{ n.pinned ? 'Unpin' : 'Pin' }}</button>
            <button class="btn btn-danger btn-sm" @click="handleDelete(n.id)">Delete</button>
          </div>
        </div>
        <div class="notice-card-body text-muted">{{ n.body }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useCoursesStore }        from '@/stores/courses'
import { useAnnouncementsStore }  from '@/stores/announcements'

const coursesStore = useCoursesStore()
const annStore     = useAnnouncementsStore()

const courses       = computed(() => coursesStore.courses)
const announcements = computed(() => annStore.announcements)
const pinned        = computed(() => announcements.value.filter(a => a.pinned).length)

function courseAnn(courseId) {
  return announcements.value.filter(a => a.course === courseId)
}
function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
async function togglePin(n) {
  await annStore.updateAnnouncement(n.id, { pinned: !n.pinned })
}
async function handleDelete(id) {
  if (!confirm('Delete this announcement?')) return
  await annStore.deleteAnnouncement(id)
}

onMounted(() => Promise.all([coursesStore.fetchCourses(), annStore.fetchAnnouncements()]))
</script>

<style scoped>
.notice-card { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; overflow: hidden; margin-bottom: 14px; }
.notice-card.pinned { border-color: var(--lf-orange); }
.notice-card-header { padding: 14px 18px; display: flex; align-items: center; gap: 10px; }
.notice-card-body   { padding: 0 18px 14px; font-size: 14px; line-height: 1.7; }
.btn { display: inline-flex; align-items: center; padding: 6px 14px; border: 1px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-size: 12px; font-weight: 600; cursor: pointer; background: transparent; color: var(--lf-gray-600); text-decoration: none; transition: all .15s; }
.btn:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-danger { background: #e53e3e; color: #fff; border: none; }
.btn-danger:hover { background: #c53030; }
</style>
