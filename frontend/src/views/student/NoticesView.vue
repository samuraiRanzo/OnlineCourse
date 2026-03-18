<template>
  <div class="page-content">
    <EmptyState
      v-if="!loading && !announcements.length"
      icon="📣"
      title="No notices yet"
      message="Your teacher hasn't posted any announcements."
    />

    <div v-else>
      <div v-for="n in announcements" :key="n.id" class="notice-card" :class="{ pinned: n.pinned }">
        <div class="notice-card-header">
          <div style="font-size:20px;flex-shrink:0">{{ n.pinned ? '📌' : '📣' }}</div>
          <div style="flex:1">
            <div style="font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px">
              {{ n.title }}
              <span v-if="!n.is_read" class="unread-dot" />
            </div>
            <div class="text-muted text-sm">{{ n.course_title }} · {{ formatDate(n.created_at) }}{{ n.pinned ? ' · Pinned' : '' }}</div>
          </div>
        </div>
        <div class="notice-card-body text-muted">{{ n.body }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted }   from 'vue'
import EmptyState                from '@/components/ui/EmptyState.vue'
import { useAnnouncementsStore } from '@/stores/announcements'

const annStore    = useAnnouncementsStore()
const loading     = computed(() => annStore.loading)
const announcements = computed(() => annStore.announcements)

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(async () => {
  await annStore.fetchAnnouncements()
  // Mark all as read when the page opens
  await annStore.markAllRead()
})
</script>

<style scoped>
.notice-card { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; overflow: hidden; margin-bottom: 14px; }
.notice-card.pinned { border-color: var(--lf-orange); }
.notice-card-header { padding: 16px 20px; display: flex; align-items: flex-start; gap: 12px; }
.notice-card-body   { padding: 0 20px 16px; font-size: 14px; line-height: 1.7; white-space: pre-wrap; }
.unread-dot { display: inline-block; width: 8px; height: 8px; background: var(--lf-orange); border-radius: 50%; flex-shrink: 0; }
</style>
