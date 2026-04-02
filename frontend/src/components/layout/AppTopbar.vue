<template>
  <div class="topbar">
    <button class="hamburger" @click="sidebar.toggle()" :aria-label="$t('topbar.toggleMenu')">
      <span class="hamburger-line"/>
      <span class="hamburger-line"/>
      <span class="hamburger-line"/>
    </button>

    <div class="topbar-title display">{{ title }}</div>

    <button
        v-if="auth.isStudent"
        class="bell-btn"
        :class="{ 'has-unread': notifStore.hasUnread }"
        :title="$t('topbar.notifications')"
        @click="panelOpen = !panelOpen"
    >
      🔔
      <span v-if="notifStore.unreadCount > 0" class="bell-badge">
        {{ notifStore.unreadCount > 99 ? '99+' : notifStore.unreadCount }}
      </span>
    </button>
    <div @click="changeLanguage" class="cursor-pointer">
      <img v-if="locale === 'en'" src="/assets/icon/mn.svg" :alt="locale">
      <img v-else src="/assets/icon/en.svg" :alt="locale">
    </div>
  </div>

  <NotificationPanel v-model="panelOpen"/>
</template>

<script setup>
import {computed, onMounted, onUnmounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import {useNotificationsStore} from '@/stores/notifications'
import {useSidebar} from '@/composables/useSidebar'
import NotificationPanel from './NotificationPanel.vue'
import {useI18n} from 'vue-i18n'

const {t, locale} = useI18n({useScope: 'global'})
const auth = useAuthStore()
const notifStore = useNotificationsStore()
const sidebar = useSidebar()
const route = useRoute()
const router = useRouter()

const panelOpen = ref(false)

// ── Title — read from route.meta.title set in router/index.js ─────────────────
const FALLBACK_TITLES = computed(() => {
  return {
    dashboard: t('titles.dashboard'),
    students: t('titles.students'),
    courses: t('titles.courses'),
    'course-detail': t('titles.courseDetail'),
    'attendance-admin': t('titles.attendance'),
    reports: t('titles.reports'),
    'student-report': t('titles.studentReport'),
    announcements: t('titles.announcements'),
    'my-courses': t('titles.myCourses'),
    'course-view': t('titles.course'),
    'lesson-view': t('titles.lesson'),
    'exam-view': t('titles.exam'),
    'check-in': t('titles.checkIn'),
    'my-attendance': t('titles.myAttendance'),
    notices: t('titles.notices'),
    profile: t('titles.profile'),
  }
})

const title = computed(() => {
  // If route.meta.title is a translation key, we translate it, otherwise check fallback
  if (route.meta?.title) return t(route.meta.title)
  return FALLBACK_TITLES.value[route.name] ?? t('titles.default')
})

const changeLanguage = () => {
  locale.value = locale.value === 'en' ? 'mn' : 'en';
  localStorage.setItem('lang', locale.value);
  // router.go() is used to refresh the app state with the new language
  router.go();
}

// ── Notification polling ──────────────────────────────────────────────────────
let pollTimer = null
onMounted(() => {
  // Sync locale from storage on mount
  const savedLang = localStorage.getItem('lang');
  if (savedLang) locale.value = savedLang;

  if (!auth.isStudent) return
  notifStore.fetchNotifications()
  pollTimer = setInterval(() => notifStore.pollUnreadCount(), 30_000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null
  }
})
</script>

<style scoped>
.topbar {
  background: var(--lf-white);
  border-bottom: 1.5px solid var(--lf-gray-200);
  padding: 16px 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar-title {
  font-size: 26px;
  flex: 1; /* push actions to the right */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Hamburger ── */
.hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  width: 38px;
  height: 38px;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color .15s, background .15s;
}

.hamburger:hover {
  border-color: var(--lf-black);
  background: var(--lf-gray-100);
}

.hamburger-line {
  display: block;
  width: 16px;
  height: 2px;
  background: var(--lf-black);
  border-radius: 2px;
}

@media (max-width: 768px) {
  .hamburger {
    display: flex;
  }

  .topbar {
    padding: 12px 16px;
  }

  .topbar-title {
    font-size: 20px;
  }
}

/* ── Bell ── */
.bell-btn {
  position: relative;
  flex-shrink: 0;
  background: transparent;
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}

.bell-btn:hover {
  border-color: var(--lf-black);
  background: var(--lf-gray-100);
}

.bell-btn.has-unread {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
  animation: bell-pulse 2.5s ease-in-out 3;
}

@keyframes bell-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 107, 0, 0);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(255, 107, 0, .15);
  }
}

.bell-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: var(--lf-orange);
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  border: 2px solid var(--lf-white);
  line-height: 1;
}
</style>
