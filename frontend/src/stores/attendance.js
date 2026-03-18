import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useAttendanceStore = defineStore('attendance', () => {
  const sessions = ref([])
  const loading  = ref(false)

  async function fetchSessions(courseId = null) {
    loading.value = true
    try {
      const params  = courseId ? { course: courseId } : {}
      const { data } = await api.get('/attendance/sessions/', { params })
      sessions.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  async function createSession(payload) {
    // payload: { course, label, date }
    // server auto-generates the code
    const { data } = await api.post('/attendance/sessions/', payload)
    sessions.value.unshift(data)
    return data
  }

  async function deleteSession(id) {
    await api.delete(`/attendance/sessions/${id}/`)
    sessions.value = sessions.value.filter(s => s.id !== id)
  }

  async function toggleAttendance(sessionId, studentId) {
    const { data } = await api.post(
      `/attendance/sessions/${sessionId}/toggle-attendance/`,
      { student_id: studentId }
    )
    // Refresh session in local list
    const idx = sessions.value.findIndex(s => s.id === sessionId)
    if (idx > -1) {
      if (data.status === 'added') {
        sessions.value[idx].attendee_ids.push(studentId)
        sessions.value[idx].attendee_count++
      } else {
        sessions.value[idx].attendee_ids =
          sessions.value[idx].attendee_ids.filter(id => id !== studentId)
        sessions.value[idx].attendee_count--
      }
    }
    return data
  }

  async function checkIn(code) {
    const { data } = await api.post('/attendance/checkin/', { code })
    return data
  }

  async function getStats(studentId, courseId) {
    const { data } = await api.get('/attendance/sessions/stats/', {
      params: { student: studentId, course: courseId },
    })
    return data
  }

  return {
    sessions, loading,
    fetchSessions, createSession, deleteSession,
    toggleAttendance, checkIn, getStats,
  }
})
