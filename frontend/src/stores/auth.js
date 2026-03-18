import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user         = ref(JSON.parse(localStorage.getItem('lf_user') || 'null'))
  const accessToken  = ref(localStorage.getItem('access_token')  || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin    = computed(() => user.value?.role === 'admin')
  const isStudent  = computed(() => user.value?.role === 'student')
  const isOnsite   = computed(() => user.value?.student_type === 'onsite')
  const isOnline   = computed(() => user.value?.student_type === 'online')

  async function login(email, password) {
    const { data } = await api.post('/auth/login/', { email, password })

    accessToken.value  = data.access
    refreshToken.value = data.refresh
    localStorage.setItem('access_token',  data.access)
    localStorage.setItem('refresh_token', data.refresh)

    if (data.user) {
      // CustomTokenObtainPairSerializer returns user inline — fast path
      user.value = data.user
      localStorage.setItem('lf_user', JSON.stringify(data.user))
    } else {
      // Fallback: fetch /users/me/ if user wasn't in the login response
      await fetchMe()
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout/', { refresh: refreshToken.value })
    } catch (_) { /* ignore — token may already be expired */ }
    accessToken.value  = ''
    refreshToken.value = ''
    user.value         = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('lf_user')
  }

  async function fetchMe() {
    const { data } = await api.get('/users/me/')
    user.value = data
    localStorage.setItem('lf_user', JSON.stringify(data))
    return data
  }

  async function updateMe(payload) {
    const { data } = await api.patch('/users/me/', payload)
    user.value = data
    localStorage.setItem('lf_user', JSON.stringify(data))
    return data
  }

  return {
    user, accessToken, refreshToken,
    isLoggedIn, isAdmin, isStudent, isOnsite, isOnline,
    login, logout, fetchMe, updateMe,
  }
})
