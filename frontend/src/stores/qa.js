import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useQaStore = defineStore('qa', () => {
  const questions = ref([])
  const loading   = ref(false)

  // Base URL for a lesson's questions
  function baseUrl(courseId, lessonId) {
    return `/courses/${courseId}/lessons/${lessonId}/questions/`
  }
  function answerUrl(courseId, lessonId, questionId) {
    return `/courses/${courseId}/lessons/${lessonId}/questions/${questionId}/answers/`
  }

  /**
   * Fetch ALL questions across every lesson in a course.
   * Used by the teacher Q&A inbox tab in CourseDetailView.
   * Calls the new /api/courses/{id}/all-questions/ endpoint.
   *
   * @param {string} courseId
   * @param {Object} params  — optional { is_resolved: true|false }
   */
  async function fetchCourseQuestions(courseId, params = {}) {
    loading.value = true
    try {
      const { data } = await api.get(`/courses/${courseId}/all-questions/`, { params })
      questions.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch questions for a single lesson.
   * Used by the student LessonView Q&A panel.
   */
  async function fetchQuestions(courseId, lessonId) {
    loading.value = true
    try {
      const { data } = await api.get(baseUrl(courseId, lessonId))
      questions.value = data.results ?? data
    } finally {
      loading.value = false
    }
  }

  async function postQuestion(courseId, lessonId, body) {
    const { data } = await api.post(baseUrl(courseId, lessonId), { body })
    questions.value.unshift(data)
    return data
  }

  async function deleteQuestion(courseId, lessonId, questionId) {
    await api.delete(`${baseUrl(courseId, lessonId)}${questionId}/`)
    questions.value = questions.value.filter(q => q.id !== questionId)
  }

  async function resolveQuestion(courseId, lessonId, questionId, isResolved) {
    const { data } = await api.patch(
      `${baseUrl(courseId, lessonId)}${questionId}/`,
      { is_resolved: isResolved }
    )
    const idx = questions.value.findIndex(q => q.id === questionId)
    if (idx > -1) questions.value[idx] = data
    return data
  }

  async function postAnswer(courseId, lessonId, questionId, body) {
    const { data } = await api.post(answerUrl(courseId, lessonId, questionId), { body })
    const q = questions.value.find(q => q.id === questionId)
    if (q) {
      q.answers.push(data)
      q.answer_count = (q.answer_count ?? 0) + 1
    }
    return data
  }

  async function deleteAnswer(courseId, lessonId, questionId, answerId) {
    await api.delete(`${answerUrl(courseId, lessonId, questionId)}${answerId}/`)
    const q = questions.value.find(q => q.id === questionId)
    if (q) {
      q.answers     = q.answers.filter(a => a.id !== answerId)
      q.answer_count = Math.max(0, (q.answer_count ?? 1) - 1)
    }
  }

  function clearQuestions() {
    questions.value = []
  }

  return {
    questions, loading,
    fetchQuestions, fetchCourseQuestions,
    postQuestion, deleteQuestion, resolveQuestion,
    postAnswer, deleteAnswer, clearQuestions,
  }
})
