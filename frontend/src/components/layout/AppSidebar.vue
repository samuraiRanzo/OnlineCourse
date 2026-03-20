<template>
  <aside class="lf-sidebar" :class="{ open: props.open }">
    <div class="sb-logo">LEARN<span>FORGE</span></div>

    <nav class="sb-nav">
      <template v-for="item in navItems" :key="item.route ?? item.section">
        <div v-if="item.section" class="sb-section">{{ item.section }}</div>
        <RouterLink
          v-else
          :to="item.route"
          class="sb-item"
          :class="{ active: isActive(item.route) }"
          @click="$emit('close')"
        >
          <span class="sb-icon">{{ item.icon }}</span>
          {{ item.label }}
          <span v-if="item.badge && unreadCount > 0" class="sb-badge">{{ unreadCount }}</span>
        </RouterLink>
      </template>
    </nav>

    <div class="sb-footer">
      <div class="sb-user">
        <div class="lf-avatar lf-avatar-md">{{ avatarLetter }}</div>
        <div class="sb-user-info">
          <div class="sb-user-name truncate">{{ auth.user?.name }}</div>
          <div class="sb-user-role">{{ roleLabel }}</div>
        </div>
        <button class="sb-logout" title="Logout" @click="handleLogout">
          <i class="pi pi-power-off" />
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute }   from 'vue-router'
import { useAuthStore }          from '@/stores/auth'
import { useAnnouncementsStore } from '@/stores/announcements'

const props = defineProps({ open: { type: Boolean, default: false } })
defineEmits(['close'])

const auth     = useAuthStore()
const annStore = useAnnouncementsStore()
const router   = useRouter()
const route    = useRoute()

const unreadCount  = computed(() => annStore.unreadCount)
const avatarLetter = computed(() => auth.user?.name?.charAt(0).toUpperCase() ?? '?')
const roleLabel    = computed(() => {
  if (auth.isAdmin)  return 'Teacher'
  if (auth.isOnsite) return 'On-site Student'
  return 'Online Student'
})

const adminNav = [
  { section: 'Overview' },
  { route: '/dashboard',     icon: '⊞', label: 'Dashboard' },
  { section: 'Manage' },
  { route: '/students',      icon: '👥', label: 'Students' },
  { route: '/courses',       icon: '📚', label: 'Courses' },
  { route: '/attendance',    icon: '📋', label: 'Attendance' },
  { route: '/reports',       icon: '📈', label: 'Reports' },
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
/* Sidebar-specific styles only — layout comes from global .lf-sidebar */
.sb-logo {
  padding: 22px 20px;
  font-family: var(--lf-font-display);
  font-size: 28px; color: #fff; letter-spacing: 1px;
  border-bottom: 1px solid #1e1e1e;
  flex-shrink: 0;
}
.sb-logo span { color: var(--lf-orange); }

.sb-nav  { padding: 14px 0; flex: 1; overflow-y: auto; }
.sb-section { padding: 8px 20px 4px; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #444; }

.sb-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px;
  color: #888; font-size: 14px; font-weight: 500;
  cursor: pointer; transition: all .15s;
  border-left: 3px solid transparent;
  text-decoration: none;
}
.sb-item:hover  { color: #fff; background: rgba(255,255,255,.05); }
.sb-item.active { color: #fff; border-left-color: var(--lf-orange); background: rgba(255,107,0,.08); }
.sb-icon  { width: 18px; text-align: center; font-size: 16px; }
.sb-badge {
  margin-left: auto; background: var(--lf-orange); color: #fff;
  font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 20px;
}

.sb-footer { padding: 14px 20px; border-top: 1px solid #1e1e1e; flex-shrink: 0; }
.sb-user   { display: flex; align-items: center; gap: 10px; }
.sb-user-info { flex: 1; overflow: hidden; }
.sb-user-name { font-size: 13px; font-weight: 600; color: #fff; }
.sb-user-role { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: .5px; }
.sb-logout {
  background: none; border: none; color: #555; cursor: pointer;
  font-size: 14px; padding: 6px; border-radius: 4px; transition: color .15s;
}
.sb-logout:hover { color: var(--lf-orange); }
</style>