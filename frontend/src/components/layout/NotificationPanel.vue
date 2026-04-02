<template>
  <div class="notif-portal-root">
    <div
        class="notif-backdrop"
        :class="{ active: modelValue }"
        @click="$emit('update:modelValue', false)"
    />

    <div class="notif-drawer" :class="{ open: modelValue }">
      <div class="notif-header">
        <div class="display" style="font-size:22px;letter-spacing:.4px">
          {{ $t('notifications.title') }}
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <button
              v-if="store.hasUnread"
              class="notif-action-btn"
              @click="store.markAllRead()"
          >
            {{ $t('notifications.markAllRead') }}
          </button>
          <button class="notif-close-btn" @click="$emit('update:modelValue', false)">✕</button>
        </div>
      </div>

      <div class="notif-filters">
        <button
            v-for="f in filters"
            :key="f.key"
            class="notif-filter-btn"
            :class="{ active: activeFilter === f.key }"
            @click="activeFilter = f.key"
        >
          {{ $t(f.label) }}
          <span v-if="f.key === 'unread' && store.unreadCount > 0" class="notif-filter-count">
              {{ store.unreadCount }}
            </span>
        </button>
      </div>

      <div v-if="store.loading" class="notif-empty">
        <div class="notif-spinner"/>
      </div>

      <div v-else-if="!filtered.length" class="notif-empty">
        <span style="font-size:36px">{{ activeFilter === 'unread' ? '✓' : '🔔' }}</span>
        <p style="margin-top:10px;font-size:14px;color:var(--lf-gray-600)">
          {{ activeFilter === 'unread' ? $t('notifications.emptyUnread') : $t('notifications.emptyAll') }}
        </p>
      </div>

      <div v-else class="notif-list">
        <div
            v-for="n in filtered"
            :key="n.id"
            class="notif-item"
            :class="{ unread: !n.is_read, clickable: !!n.link }"
            @click="handleClick(n)"
        >
          <div class="notif-icon" :class="`notif-icon-${n.type}`">
            {{ typeIcon(n.type) }}
          </div>

          <div class="notif-content">
            <div class="notif-title">{{ n.title }}</div>
            <div v-if="n.body" class="notif-body text-sm text-muted">{{ n.body }}</div>
            <div class="notif-time text-sm" style="color:var(--lf-gray-400);margin-top:3px">
              {{ relativeTime(n.created_at) }}
            </div>
          </div>

          <div v-if="!n.is_read" class="notif-unread-dot"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, computed} from 'vue'
import {useRouter} from 'vue-router'
import {useNotificationsStore} from '@/stores/notifications'
import {useI18n} from 'vue-i18n'

const {t, locale} = useI18n()

defineProps({
  modelValue: {type: Boolean, default: false},
})
const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const store = useNotificationsStore()

const activeFilter = ref('all')
const filters = [
  {key: 'all', label: 'notifications.filters.all'},
  {key: 'unread', label: 'notifications.filters.unread'},
]

const filtered = computed(() => {
  if (activeFilter.value === 'unread') return store.notifications.filter(n => !n.is_read)
  return store.notifications
})

const TYPE_ICONS = {
  qa_answer: '💬',
  exam_graded: '✍️',
  cert_issued: '🎓',
  announcement: '📣',
}

function typeIcon(type) {
  return TYPE_ICONS[type] ?? '🔔'
}

function relativeTime(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)

  if (mins < 1) return t('notifications.time.justNow')
  if (mins < 60) return t('notifications.time.minutesAgo', {n: mins})

  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return t('notifications.time.hoursAgo', {n: hrs})

  const days = Math.floor(hrs / 24)
  if (days < 7) return t('notifications.time.daysAgo', {n: days})

  // Use browser locale or fixed 'mn-MN'/'en-GB' based on app state
  const dateLocale = locale.value === 'mn' ? 'mn-MN' : 'en-GB'
  return new Date(iso).toLocaleDateString(dateLocale, {day: 'numeric', month: 'short'})
}

async function handleClick(notif) {
  if (!notif.is_read) await store.markRead(notif.id)
  if (notif.link) {
    emit('update:modelValue', false)
    router.push(notif.link)
  }
}
</script>

<style scoped>
/*
  The portal root is always present — zero visual footprint when inactive.
  pointer-events: none on the root means it never intercepts clicks when closed.
*/
.notif-portal-root {
  position: fixed;
  inset: 0;
  z-index: 200;
  pointer-events: none;
}

/* ── Backdrop ── */
.notif-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  opacity: 0;
  pointer-events: none;
  transition: opacity .2s ease;
}

.notif-backdrop.active {
  opacity: 1;
  pointer-events: all;
}

/* ── Drawer ── */
.notif-drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: 380px;
  max-width: 100vw;
  height: 100vh;
  background: var(--lf-white);
  border-left: 1.5px solid var(--lf-gray-200);
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform .22s cubic-bezier(.4, 0, .2, 1),
  box-shadow .22s ease;
  pointer-events: none;
}

.notif-drawer.open {
  transform: translateX(0);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.1);
  pointer-events: all;
}

/* ── Header ── */
.notif-header {
  padding: 20px 20px 14px;
  border-bottom: 1.5px solid var(--lf-gray-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.notif-action-btn {
  background: none;
  border: none;
  font-size: 12px;
  font-weight: 600;
  color: var(--lf-orange);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--lf-radius);
  transition: background .15s;
}

.notif-action-btn:hover {
  background: var(--lf-orange-light);
}

.notif-close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--lf-gray-600);
  line-height: 1;
  padding: 4px 6px;
  transition: color .15s;
}

.notif-close-btn:hover {
  color: var(--lf-black);
}

/* ── Filters ── */
.notif-filters {
  display: flex;
  border-bottom: 1.5px solid var(--lf-gray-200);
  flex-shrink: 0;
}

.notif-filter-btn {
  flex: 1;
  padding: 10px 0;
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--lf-gray-600);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.notif-filter-btn:hover {
  color: var(--lf-black);
}

.notif-filter-btn.active {
  color: var(--lf-orange);
  border-bottom-color: var(--lf-orange);
}

.notif-filter-count {
  background: var(--lf-orange);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

/* ── Empty / loading ── */
.notif-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}

.notif-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--lf-gray-200);
  border-top-color: var(--lf-orange);
  border-radius: 50%;
  animation: spin .7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── List ── */
.notif-list {
  flex: 1;
  overflow-y: auto;
}

.notif-list::-webkit-scrollbar {
  width: 4px;
}

.notif-list::-webkit-scrollbar-track {
  background: var(--lf-gray-100);
}

.notif-list::-webkit-scrollbar-thumb {
  background: var(--lf-gray-200);
  border-radius: 2px;
}

/* ── Item ── */
.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--lf-gray-200);
  transition: background .12s;
  position: relative;
}

.notif-item.clickable {
  cursor: pointer;
}

.notif-item.clickable:hover {
  background: var(--lf-gray-100);
}

.notif-item.unread {
  background: var(--lf-orange-light);
}

.notif-item.unread.clickable:hover {
  background: #fde8d0;
}

/* ── Type icon badge ── */
.notif-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.notif-icon-qa_answer {
  background: #e8f0fe;
}

.notif-icon-exam_graded {
  background: #faeeda;
}

.notif-icon-cert_issued {
  background: #e6f7ee;
}

.notif-icon-announcement {
  background: var(--lf-orange-light);
}

/* ── Content ── */
.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--lf-black);
}

.notif-body {
  margin-top: 3px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-time {
  font-size: 11px;
}

/* ── Unread dot ── */
.notif-unread-dot {
  width: 8px;
  height: 8px;
  background: var(--lf-orange);
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
</style>
