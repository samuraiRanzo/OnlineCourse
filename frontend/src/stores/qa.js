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
    async function fetchCourseQuestions(courseId) {
      loading.value = true;
      try {
        // This assumes your backend supports a ?course= query param on the questions endpoint
        // If not, you may need to fetch lessons first and loop, or update the backend view.
        const { data } = await api.get(`/courses/${courseId}/all-questions/`);
        questions.value = data.results ?? data;
      } finally {
        loading.value = false;
      }
    }
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
    // Push answer into the question's answers array in local state
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
    fetchQuestions, postQuestion, deleteQuestion, resolveQuestion,
    postAnswer, deleteAnswer, clearQuestions,fetchCourseQuestions
  }
})
