import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useStudentsStore = defineStore('students', () => {
  const students = ref([])
  const loading  = ref(false)

  async function fetchStudents() {
    loading.value = true
    try {
      const { data } = await api.get('/users/', { params: { role: 'student' } })
      students.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  async function createStudent(payload) {
    const { data } = await api.post('/users/', { ...payload, role: 'student' })
    students.value.push(data)
    return data
  }

  async function deleteStudent(id) {
    await api.delete(`/users/${id}/`)
    students.value = students.value.filter(s => s.id !== id)
  }

  async function resetPassword(id, newPassword) {
    await api.post(`/users/${id}/reset-password/`, { new_password: newPassword })
  }

  return { students, loading, fetchStudents, createStudent, deleteStudent, resetPassword }
})
