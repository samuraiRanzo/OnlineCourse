import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useCoursesStore = defineStore('courses', () => {
  const courses     = ref([])
  const current     = ref(null)
  const enrollments = ref([])
  const loading     = ref(false)

  async function fetchCourses() {
    loading.value = true
    try {
      const { data } = await api.get('/courses/')
      courses.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  async function fetchCourse(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/courses/${id}/`)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function createCourse(payload) {
    const { data } = await api.post('/courses/', payload)
    courses.value.unshift(data)
    return data
  }

  async function updateCourse(id, payload) {
    const { data } = await api.patch(`/courses/${id}/`, payload)
    const idx = courses.value.findIndex(c => c.id === id)
    if (idx > -1) courses.value[idx] = data
    if (current.value?.id === id) current.value = data
    return data
  }

  async function deleteCourse(id) {
    await api.delete(`/courses/${id}/`)
    courses.value = courses.value.filter(c => c.id !== id)
  }

  // ── Lessons ────────────────────────────────────────────────────────
  const uploadProgress = ref(0) // 0-100, used by the UI for the progress bar

  async function createLesson(courseId, payload) {
    const formData = buildLessonFormData(payload)
    const { data } = await api.post(
      `/courses/${courseId}/lessons/`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress(e) {
          uploadProgress.value = e.total
            ? Math.round((e.loaded / e.total) * 100)
            : 0
        },
      }
    )
    uploadProgress.value = 0
    if (current.value?.id === courseId) current.value.lessons.push(data)
    return data
  }

  async function updateLesson(courseId, lessonId, payload) {
    const formData = buildLessonFormData(payload)
    const { data } = await api.patch(
      `/courses/${courseId}/lessons/${lessonId}/`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress(e) {
          uploadProgress.value = e.total
            ? Math.round((e.loaded / e.total) * 100)
            : 0
        },
      }
    )
    uploadProgress.value = 0
    if (current.value?.id === courseId) {
      const idx = current.value.lessons.findIndex(l => l.id === lessonId)
      if (idx > -1) current.value.lessons[idx] = data
    }
    return data
  }

  /**
   * Build a FormData object from a lesson payload.
   * Handles the video_file (File object) correctly.
   * Skips null/undefined values so PATCH only sends changed fields.
   */
  function buildLessonFormData(payload) {
    const fd = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (value === null || value === undefined) return
      // File objects must be appended directly — not JSON stringified
      if (value instanceof File) {
        fd.append(key, value, value.name)
      } else {
        fd.append(key, String(value))
      }
    })
    return fd
  }

  async function deleteLesson(courseId, lessonId) {
    await api.delete(`/courses/${courseId}/lessons/${lessonId}/`)
    if (current.value?.id === courseId) {
      current.value.lessons = current.value.lessons.filter(l => l.id !== lessonId)
    }
  }

  async function reorderLessons(courseId, orderedIds) {
    const { data } = await api.post(`/courses/${courseId}/reorder-lessons/`, { order: orderedIds })
    if (current.value?.id === courseId) current.value.lessons = data
    return data
  }

  // ── Enrollments ────────────────────────────────────────────────────
  async function fetchEnrollments(params = {}) {
    const { data } = await api.get('/courses/enrollments/', { params })
    enrollments.value = data.results ?? data
    return enrollments.value
  }

  async function createEnrollment(studentId, courseId) {
    const { data } = await api.post('/courses/enrollments/', {
      student: studentId, course: courseId,
    })
    enrollments.value.push(data)
    return data
  }

  async function deleteEnrollment(id) {
    await api.delete(`/courses/enrollments/${id}/`)
    enrollments.value = enrollments.value.filter(e => e.id !== id)
  }

  // ── Lesson completion ──────────────────────────────────────────────
  async function markLessonComplete(enrollmentId, lessonId) {
    const { data } = await api.post('/courses/completions/', {
      enrollment: enrollmentId, lesson: lessonId,
    })
    return data
  }

  return {
    courses, current, enrollments, loading, uploadProgress,
    fetchCourses, fetchCourse,
    createCourse, updateCourse, deleteCourse,
    createLesson, updateLesson, deleteLesson, reorderLessons,
    fetchEnrollments, createEnrollment, deleteEnrollment,
    markLessonComplete,
  }
})
