import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import api from '@/api'

export const useExamsStore = defineStore('exams', () => {
  // ── State ─────────────────────────────────────────────────────────────────
  const exam          = ref(null)        // current course's exam (teacher full or student-safe)
  const currentAttempt = ref(null)       // in-progress or last attempt
  const myAttemptsData = ref(null)       // { attempts, retakes_remaining, ... }
  const finalGrade    = ref(null)        // computed final grade for current student
  const allAttempts   = ref([])          // teacher: all student attempts
  const allFinalGrades = ref(null)       // teacher: all students' final grades
  const loading       = ref(false)

  // ── Teacher: fetch / save exam ────────────────────────────────────────────

  async function fetchExamByCourse(courseId) {
    const { data } = await api.get('/exams/', { params: { course: courseId } })
    const list = data.results ?? data
    exam.value = list[0] ?? null
    return exam.value
  }

  async function saveExam(courseId, payload) {
    if (exam.value?.id) {
      const { data } = await api.patch(`/exams/${exam.value.id}/`, payload)
      exam.value = data
    } else {
      const { data } = await api.post('/exams/', { course: courseId, ...payload })
      exam.value = data
    }
    return exam.value
  }

  // ── Student: start an attempt ─────────────────────────────────────────────

  async function startAttempt(examId) {
    loading.value = true
    try {
      const { data } = await api.post(`/exams/${examId}/start/`)
      currentAttempt.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  // ── Student: get exam questions (safe — no correct_index) ──────────────────

  async function fetchExamForStudent(examId) {
    const { data } = await api.get(`/exams/${examId}/for-student/`)
    exam.value = data
    return data
  }

  // ── Student: submit ───────────────────────────────────────────────────────

  /**
   * @param {string} examId
   * @param {string} attemptId
   * @param {Array}  responses  [{question_index, selected_index?, text_answer?}]
   * @param {boolean} autoSubmitted  true when timer expired
   */
  async function submitAttempt(examId, attemptId, responses, autoSubmitted = false) {
    loading.value = true
    try {
      const { data } = await api.post(`/exams/${examId}/submit/`, {
        attempt_id:     attemptId,
        auto_submitted: autoSubmitted,
        responses,
      })
      currentAttempt.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  // ── Student: my attempts / results ────────────────────────────────────────

  async function fetchMyAttempts(examId) {
    const { data } = await api.get(`/exams/${examId}/my-attempts/`)
    myAttemptsData.value = data
    return data
  }

  // ── Student: final course grade ───────────────────────────────────────────

  async function fetchFinalGrade(courseId) {
    const { data } = await api.get(`/courses/${courseId}/final-grade/`)
    finalGrade.value = data
    return data
  }

  // ── Teacher: all attempts for grading ─────────────────────────────────────

  async function fetchAllAttempts(examId) {
    loading.value = true
    try {
      const { data } = await api.get(`/exams/${examId}/all-attempts/`)
      allAttempts.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchAllFinalGrades(courseId) {
    loading.value = true
    try {
      const { data } = await api.get(`/courses/${courseId}/final-grade/`)
      allFinalGrades.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  // ── Teacher: grade an open question response ──────────────────────────────

  async function gradeResponse(responseId, pointsEarned, teacherFeedback) {
    const { data } = await api.patch(`/exams/responses/${responseId}/grade/`, {
      points_earned:    pointsEarned,
      teacher_feedback: teacherFeedback,
    })
    // Update the response in allAttempts in place
    for (const attempt of allAttempts.value) {
      const idx = attempt.responses?.findIndex(r => r.id === responseId) ?? -1
      if (idx > -1) {
        attempt.responses[idx] = data
        // Recompute attempt score from the responses array
        const graded = attempt.responses.filter(r => r.points_earned !== null)
        const earned = graded.reduce((s, r) => s + r.points_earned, 0)
        const possible = attempt.responses.reduce((s, r) => s + r.max_points, 0)
        attempt.score = possible ? Math.round((earned / possible) * 100 * 10) / 10 : 0
        break
      }
    }
    return data
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  function clearExam() {
    exam.value           = null
    currentAttempt.value = null
    myAttemptsData.value = null
    finalGrade.value     = null
    allAttempts.value    = []
    allFinalGrades.value = null
  }

  return {
    exam, currentAttempt, myAttemptsData, finalGrade,
    allAttempts, allFinalGrades, loading,
    fetchExamByCourse, saveExam,
    startAttempt, fetchExamForStudent, submitAttempt,
    fetchMyAttempts, fetchFinalGrade,
    fetchAllAttempts, fetchAllFinalGrades, gradeResponse,
    clearExam,
  }
})
