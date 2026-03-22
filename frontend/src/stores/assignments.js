import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useAssignmentsStore = defineStore('assignments', () => {
  /**
   * Assignments keyed by lessonId — used by student LessonView.
   * { [lessonId]: Assignment[] }
   */
  const lessonAssignments = ref({})

  /**
   * Assignments keyed by courseId — used by teacher CourseDetailView.
   * { [courseId]: Assignment[] }
   */
  const courseAssignments = ref({})

  /**
   * Submissions keyed by assignmentId — loaded on demand in teacher view.
   * { [assignmentId]: Submission[] }
   */
  const assignmentSubmissions = ref({})

  const loading = ref(false)

  // ── Fetch ─────────────────────────────────────────────────────────────────

  async function fetchByLesson(lessonId) {
    const { data } = await api.get('/assignments/', { params: { lesson: lessonId } })
    lessonAssignments.value[lessonId] = data.results ?? data
    return lessonAssignments.value[lessonId]
  }

  async function fetchByCourse(courseId) {
    loading.value = true
    try {
      const { data } = await api.get('/assignments/', { params: { course: courseId } })
      courseAssignments.value[courseId] = data.results ?? data
      return courseAssignments.value[courseId]
    } finally {
      loading.value = false
    }
  }

  async function fetchSubmissions(assignmentId) {
    const { data } = await api.get('/assignments/submissions/', {
      params: { assignment: assignmentId },
    })
    assignmentSubmissions.value[assignmentId] = data.results ?? data
    return assignmentSubmissions.value[assignmentId]
  }

  // ── Teacher CRUD ──────────────────────────────────────────────────────────

  async function createAssignment(courseId, payload) {
    const { data } = await api.post('/assignments/', payload)
    if (courseAssignments.value[courseId]) {
      courseAssignments.value[courseId].push(data)
    }
    return data
  }

  async function updateAssignment(courseId, id, payload) {
    const { data } = await api.patch(`/assignments/${id}/`, payload)
    if (courseAssignments.value[courseId]) {
      const idx = courseAssignments.value[courseId].findIndex(a => a.id === id)
      if (idx > -1) courseAssignments.value[courseId][idx] = data
    }
    return data
  }

  async function deleteAssignment(courseId, id) {
    await api.delete(`/assignments/${id}/`)
    if (courseAssignments.value[courseId]) {
      courseAssignments.value[courseId] = courseAssignments.value[courseId].filter(
        a => a.id !== id
      )
    }
    // Remove cached submissions for this assignment
    delete assignmentSubmissions.value[id]
  }

  // ── Teacher grading ───────────────────────────────────────────────────────

  async function grade(submissionId, score, feedback) {
    const { data } = await api.patch(
      `/assignments/submissions/${submissionId}/grade/`,
      { score, feedback },
    )
    // Update cached submission in place
    for (const list of Object.values(assignmentSubmissions.value)) {
      const idx = list.findIndex(s => s.id === submissionId)
      if (idx > -1) { list[idx] = data; break }
    }
    return data
  }

  // ── Student submit / resubmit ─────────────────────────────────────────────

  /**
   * Submit or resubmit an assignment.
   * Uses FormData so files are sent as multipart.
   * After success, refreshes the lesson's assignment list so my_submission is current.
   */
  async function submit(lessonId, assignmentId, textAnswer, file) {
    const fd = new FormData()
    fd.append('assignment', assignmentId)
    if (textAnswer?.trim()) fd.append('text_answer', textAnswer)
    if (file) fd.append('file', file, file.name)

    const { data } = await api.post('/assignments/submissions/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // Refresh lesson assignments so my_submission reflects new data
    await fetchByLesson(lessonId)
    return data
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  function getByLesson(lessonId) {
    return lessonAssignments.value[lessonId] ?? []
  }

  function getByCourse(courseId) {
    return courseAssignments.value[courseId] ?? []
  }

  function getSubmissions(assignmentId) {
    return assignmentSubmissions.value[assignmentId] ?? []
  }

  function clearAll() {
    lessonAssignments.value  = {}
    courseAssignments.value  = {}
    assignmentSubmissions.value = {}
  }

  return {
    lessonAssignments, courseAssignments, assignmentSubmissions, loading,
    fetchByLesson, fetchByCourse, fetchSubmissions,
    createAssignment, updateAssignment, deleteAssignment,
    grade, submit,
    getByLesson, getByCourse, getSubmissions,
    clearAll,
  }
})
