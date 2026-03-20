import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useExamsStore = defineStore('exams', () => {
  const exams   = ref([])
  const results = ref([])
  const loading = ref(false)

  async function fetchExam(id) {
    const { data } = await api.get(`/exams/${id}/`)
    return data
  }

  async function fetchExamByCourse(courseId) {
    const { data } = await api.get('/exams/', { params: { course: courseId } })
    const list = data.results ?? data
    return list.find(e => e.course === courseId) ?? null
  }

  async function saveExam(courseId, payload) {
    const existing = await fetchExamByCourse(courseId)
    if (existing) {
      const { data } = await api.put(`/exams/${existing.id}/`, { course: courseId, ...payload })
      return data
    }
    const { data } = await api.post('/exams/', { course: courseId, ...payload })
    return data
  }

  async function deleteExam(id) {
    await api.delete(`/exams/${id}/`)
  }

  async function submitExam(examId, answers) {
    const { data } = await api.post('/exams/results/', { exam: examId, answers })
    results.value.unshift(data)
    return data
  }

  async function fetchResults(params = {}) {
    const { data } = await api.get('/exams/results/', { params })
    results.value = data.results ?? data
    return results.value
  }

  /**
   * Returns all attempts for a specific course, newest first.
   * Used by ExamView to show attempt history and decide retake eligibility.
   */
  function getResultsByCourse(courseId) {
    return results.value
      .filter(r => r.course_id === courseId)
      .sort((a, b) => b.attempt - a.attempt)
  }

  /**
   * Latest attempt for a course — used by dashboards / course cards.
   */
  function getLatestResult(courseId) {
    return getResultsByCourse(courseId)[0] ?? null
  }

  /**
   * Upload (or delete) the image for a single question.
   * examId   — the exam's UUID
   * questionId — the question's UUID
   * imageFile  — File object to upload, or null to remove the image
   */
  async function uploadQuestionImage(examId, questionId, imageFile) {
    if (!imageFile) {
      const { data } = await api.delete(
        `/exams/${examId}/questions/${questionId}/image/`
      )
      return data
    }
    const fd = new FormData()
    fd.append('image', imageFile, imageFile.name)
    const { data } = await api.post(
      `/exams/${examId}/questions/${questionId}/image/`,
      fd
      // No Content-Type header — Axios sets multipart/form-data with boundary automatically
    )
    return data  // { image_url: '...' }
  }

  async function gradeOpenAnswer(resultId, questionIndex, grade) {
    const { data } = await api.patch(`/exams/results/${resultId}/grade-open/`, {
      question_index: questionIndex,
      grade,
    })
    const idx = results.value.findIndex(r => r.id === resultId)
    if (idx > -1) results.value[idx] = data
    return data
  }

  return {
    exams, results, loading,
    fetchExam, fetchExamByCourse, saveExam, deleteExam, uploadQuestionImage,
    submitExam, fetchResults, getResultsByCourse, getLatestResult,
    gradeOpenAnswer,
  }
})