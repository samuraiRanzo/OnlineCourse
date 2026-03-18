<template>
  <aside class="sidebar">
    <div class="sidebar-logo">LEARN<span>FORGE</span></div>

    <nav class="sidebar-nav">
      <template v-for="item in navItems" :key="item.route ?? item.section">
        <div v-if="item.section" class="nav-section">{{ item.section }}</div>
        <RouterLink
          v-else
          :to="item.route"
          class="nav-item"
          :class="{ active: isActive(item.route) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          {{ item.label }}
          <span v-if="item.badge && unreadCount > 0" class="nav-badge">{{ unreadCount }}</span>
        </RouterLink>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="sidebar-avatar">{{ avatarLetter }}</div>
        <div class="sidebar-user-info">
          <div class="sidebar-user-name">{{ auth.user?.name }}</div>
          <div class="sidebar-user-role">{{ roleLabel }}</div>
        </div>
        <button class="logout-btn" title="Logout" @click="handleLogout">⏻</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore }          from '@/stores/auth'
import { useAnnouncementsStore } from '@/stores/announcements'

const auth          = useAuthStore()
const annStore      = useAnnouncementsStore()
const router        = useRouter()
const route         = useRoute()

const unreadCount = computed(() => annStore.unreadCount)
const avatarLetter = computed(() => auth.user?.name?.charAt(0).toUpperCase() ?? '?')
const roleLabel    = computed(() => {
  if (auth.isAdmin)   return 'Teacher'
  if (auth.isOnsite)  return 'On-site Student'
  return 'Online Student'
})

const adminNav = [
  { section: 'Overview' },
  { route: '/dashboard',    icon: '⊞', label: 'Dashboard' },
  { section: 'Manage' },
  { route: '/students',     icon: '👥', label: 'Students' },
  { route: '/courses',      icon: '📚', label: 'Courses' },
  { route: '/attendance',   icon: '📋', label: 'Attendance' },
  { route: '/reports',      icon: '📈', label: 'Reports' },
  { route: '/announcements', icon: '📣', label: 'Announcements' },
]

const onsiteNav = [
  { section: 'Overview' },
  { route: '/dashboard',     icon: '⊞', label: 'Dashboard' },
  { section: 'Learning' },
  { route: '/my-courses',    icon: '📚', label: 'My Courses' },
  { route: '/notices',       icon: '📣', label: 'Notices', badge: true },
  { section: 'Attendance' },
  { route: '/check-in',      icon: '📋', label: 'Check In' },
  { route: '/my-attendance', icon: '📊', label: 'My Attendance' },
  { section: 'Account' },
  { route: '/profile',       icon: '👤', label: 'Profile' },
]

const onlineNav = [
  { section: 'Overview' },
  { route: '/dashboard',  icon: '⊞', label: 'Dashboard' },
  { section: 'Learning' },
  { route: '/my-courses', icon: '📚', label: 'My Courses' },
  { route: '/notices',    icon: '📣', label: 'Notices', badge: true },
  { section: 'Account' },
  { route: '/profile',    icon: '👤', label: 'Profile' },
]

const navItems = computed(() => {
  if (auth.isAdmin)  return adminNav
  if (auth.isOnsite) return onsiteNav
  return onlineNav
})

function isActive(routePath) {
  return route.path === routePath || route.path.startsWith(routePath + '/')
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

onMounted(() => {
  if (auth.isStudent) annStore.fetchUnreadCount()
})
</script>

<style scoped>
.sidebar {
  width: 240px; background: var(--lf-black); display: flex; flex-direction: column;
  position: fixed; top: 0; left: 0; height: 100vh; overflow-y: auto; z-index: 100;
}
.sidebar-logo {
  padding: 24px 20px; font-family: var(--lf-font-display); font-size: 28px;
  color: #fff; letter-spacing: 1px; border-bottom: 1px solid #1e1e1e; flex-shrink: 0;
}
.sidebar-logo span { color: var(--lf-orange); }
.sidebar-nav  { padding: 16px 0; flex: 1; }
.nav-section  { padding: 8px 20px 4px; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #555; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 20px;
  color: #888; font-size: 14px; font-weight: 500; cursor: pointer;
  transition: all .15s; border-left: 3px solid transparent; text-decoration: none;
}
.nav-item:hover { color: #fff; background: rgba(255,255,255,.05); }
.nav-item.active { color: #fff; border-left-color: var(--lf-orange); background: rgba(255,107,0,.08); }
.nav-icon { width: 18px; text-align: center; font-size: 16px; }
.nav-badge {
  margin-left: auto; background: var(--lf-orange); color: #fff;
  font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 20px;
}
.sidebar-footer { padding: 16px 20px; border-top: 1px solid #1e1e1e; flex-shrink: 0; }
.sidebar-user   { display: flex; align-items: center; gap: 10px; }
.sidebar-avatar {
  width: 34px; height: 34px; background: var(--lf-orange); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; color: #fff; font-size: 14px; flex-shrink: 0;
}
.sidebar-user-info { flex: 1; overflow: hidden; }
.sidebar-user-name { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sidebar-user-role { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: .5px; }
.logout-btn { background: none; border: none; color: #555; cursor: pointer; font-size: 16px; padding: 4px; transition: color .15s; }
.logout-btn:hover { color: var(--lf-orange); }
</style>
