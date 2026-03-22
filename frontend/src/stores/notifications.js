import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const loading       = ref(false)

  // Derived — avoids recomputing everywhere
  const unreadCount = computed(() =>
    notifications.value.filter(n => !n.is_read).length
  )
  const hasUnread = computed(() => unreadCount.value > 0)

  /**
   * Fetch the 30 most-recent notifications for the current user.
   * Called once on login and then on-demand when the panel opens.
   */
  async function fetchNotifications() {
    loading.value = true
    try {
      const { data } = await api.get('/notifications/')
      notifications.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  /**
   * Lightweight poll — only fetches the count, not the full list.
   * Called every 30s by AppTopbar so the badge stays current.
   * If count has changed since last fetch, refresh the full list too.
   */
  async function pollUnreadCount() {
    try {
      const { data } = await api.get('/notifications/unread-count/')
      const serverCount = data.unread ?? 0
      // If there are new notifications the client doesn't know about yet, refresh
      if (serverCount > unreadCount.value) {
        await fetchNotifications()
      }
    } catch {
      // Silently ignore network errors during background polling
    }
  }

  /**
   * Mark a single notification as read.
   * Updates local state optimistically so the badge updates instantly.
   */
  async function markRead(id) {
    const notif = notifications.value.find(n => n.id === id)
    if (!notif || notif.is_read) return
    // Optimistic update
    notif.is_read = true
    try {
      await api.post(`/notifications/${id}/mark-read/`)
    } catch {
      // Rollback if the request fails
      notif.is_read = false
    }
  }

  /**
   * Mark all notifications as read.
   * Optimistically updates all local items.
   */
  async function markAllRead() {
    notifications.value.forEach(n => { n.is_read = true })
    try {
      await api.post('/notifications/mark-all-read/')
    } catch {
      // On failure the server state diverges — re-fetch to reconcile
      await fetchNotifications()
    }
  }

  /**
   * Clear local state on logout.
   */
  function clearNotifications() {
    notifications.value = []
  }

  return {
    notifications, loading, unreadCount, hasUnread,
    fetchNotifications, pollUnreadCount,
    markRead, markAllRead, clearNotifications,
  }
})
