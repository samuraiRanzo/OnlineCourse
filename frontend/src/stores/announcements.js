import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useAnnouncementsStore = defineStore('announcements', () => {
  const announcements = ref([])
  const unreadCount   = ref(0)
  const loading       = ref(false)

  async function fetchAnnouncements(courseId = null) {
    loading.value = true
    try {
      const params  = courseId ? { course: courseId } : {}
      const { data } = await api.get('/announcements/', { params })
      announcements.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    const { data } = await api.get('/announcements/unread-count/')
    unreadCount.value = data.unread
    return data.unread
  }

  async function createAnnouncement(payload) {
    const { data } = await api.post('/announcements/', payload)
    announcements.value.unshift(data)
    return data
  }

  async function updateAnnouncement(id, payload) {
    const { data } = await api.patch(`/announcements/${id}/`, payload)
    const idx = announcements.value.findIndex(a => a.id === id)
    if (idx > -1) announcements.value[idx] = data
    return data
  }

  async function deleteAnnouncement(id) {
    await api.delete(`/announcements/${id}/`)
    announcements.value = announcements.value.filter(a => a.id !== id)
  }

  async function markRead(id) {
    await api.post(`/announcements/${id}/mark-read/`)
    const ann = announcements.value.find(a => a.id === id)
    if (ann) ann.is_read = true
    if (unreadCount.value > 0) unreadCount.value--
  }

  async function markAllRead() {
    await api.post('/announcements/mark-all-read/')
    announcements.value.forEach(a => { a.is_read = true })
    unreadCount.value = 0
  }

  return {
    announcements, unreadCount, loading,
    fetchAnnouncements, fetchUnreadCount,
    createAnnouncement, updateAnnouncement, deleteAnnouncement,
    markRead, markAllRead,
  }
})
