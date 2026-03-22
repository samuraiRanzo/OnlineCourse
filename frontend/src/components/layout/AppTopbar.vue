<template>
  <div class="topbar">
    <!-- Hamburger — visible on mobile only via CSS -->
    <button class="hamburger" @click="sidebar.toggle()" aria-label="Toggle menu">
      <span class="hamburger-line" />
      <span class="hamburger-line" />
      <span class="hamburger-line" />
    </button>

    <div class="topbar-title display">{{ title }}</div>

    <!-- Notification bell — students only -->
    <button
      v-if="auth.isStudent"
      class="bell-btn"
      :class="{ 'has-unread': notifStore.hasUnread }"
      title="Notifications"
      @click="panelOpen = !panelOpen"
    >
      🔔
      <span v-if="notifStore.unreadCount > 0" class="bell-badge">
        {{ notifStore.unreadCount > 99 ? '99+' : notifStore.unreadCount }}
      </span>
    </button>
  </div>

  <!-- Notification panel — always mounted, CSS-hidden when closed -->
  <NotificationPanel v-model="panelOpen" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute }              from 'vue-router'
import { useAuthStore }          from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { useSidebar }            from '@/composables/useSidebar'
import NotificationPanel         from './NotificationPanel.vue'

const auth       = useAuthStore()
const notifStore = useNotificationsStore()
const sidebar    = useSidebar()
const route      = useRoute()
const panelOpen  = ref(false)

// ── Title — read from route.meta.title set in router/index.js ─────────────────
// Fallback map kept for routes that haven't been updated yet.
const FALLBACK_TITLES = {
  dashboard:          'Dashboard',
  students:           'Students',
  courses:            'Courses',
  'course-detail':    'Course Detail',
  'attendance-admin': 'Attendance',
  reports:            'Reports',
  'student-report':   'Student Report',
  announcements:      'Announcements',
  'my-courses':       'My Courses',
  'course-view':      'Course',
  'lesson-view':      'Lesson',
  'exam-view':        'Exam',
  'check-in':         'Check In',
  'my-attendance':    'My Attendance',
  notices:            'Notices',
  profile:            'Profile',
}
const title = computed(
  () => route.meta?.title ?? FALLBACK_TITLES[route.name] ?? 'LearnForge'
)

// ── Notification polling ──────────────────────────────────────────────────────
let pollTimer = null
onMounted(() => {
  if (!auth.isStudent) return
  notifStore.fetchNotifications()
  pollTimer = setInterval(() => notifStore.pollUnreadCount(), 30_000)
})
onUnmounted(() => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } })
</script>

<style scoped>
.topbar {
  background: var(--lf-white);
  border-bottom: 1.5px solid var(--lf-gray-200);
  padding: 16px 32px;
  display: flex; align-items: center; gap: 12px;
  position: sticky; top: 0; z-index: 50;
}

.topbar-title {
  font-size: 26px;
  flex: 1;            /* push actions to the right */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Hamburger ── */
.hamburger {
  display: none;
  flex-direction: column; justify-content: center; align-items: center;
  gap: 5px;
  background: transparent;
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  width: 38px; height: 38px;
  cursor: pointer; flex-shrink: 0;
  transition: border-color .15s, background .15s;
}
.hamburger:hover { border-color: var(--lf-black); background: var(--lf-gray-100); }
.hamburger-line  { display: block; width: 16px; height: 2px; background: var(--lf-black); border-radius: 2px; }

@media (max-width: 768px) {
  .hamburger { display: flex; }
  .topbar    { padding: 12px 16px; }
  .topbar-title { font-size: 20px; }
}

/* ── Bell ── */
.bell-btn {
  position: relative; flex-shrink: 0;
  background: transparent;
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; cursor: pointer;
  transition: border-color .15s, background .15s;
}
.bell-btn:hover { border-color: var(--lf-black); background: var(--lf-gray-100); }
.bell-btn.has-unread {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
  animation: bell-pulse 2.5s ease-in-out 3;
}
@keyframes bell-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255,107,0,0); }
  50%       { box-shadow: 0 0 0 6px rgba(255,107,0,.15); }
}
.bell-badge {
  position: absolute; top: -6px; right: -6px;
  background: var(--lf-orange); color: #fff;
  font-size: 9px; font-weight: 700;
  min-width: 16px; height: 16px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 4px; border: 2px solid var(--lf-white); line-height: 1;
}
</style>
