/**
 * api.js — Axios instance for the LearnForge backend.
 *
 * ── Base URL ──────────────────────────────────────────────────────────────────
 * Set VITE_API_URL in .env to override (e.g. for staging/production):
 *   VITE_API_URL=https://api.yourserver.com/api
 *
 * The default assumes Django is running on localhost:8000 with the standard
 * learnforge url config:  path('api/', include(...))
 *
 * ALL store/view calls use paths WITHOUT the /api/ prefix, e.g.:
 *   api.get('/courses/')          → http://localhost:8000/api/courses/
 *   api.get('/assignments/')      → http://localhost:8000/api/assignments/
 *   api.get('/notifications/')    → http://localhost:8000/api/notifications/
 *
 * ── Auth flow ─────────────────────────────────────────────────────────────────
 * 1. Request interceptor:  reads access token from localStorage and injects
 *    Authorization: Bearer <token> on every request (except login/refresh).
 *
 * 2. Response interceptor: on 401, attempts a single silent token refresh via
 *    POST /auth/refresh/.  If successful, retries the original request once.
 *    If the refresh itself fails (refresh token expired) the user is logged out
 *    and redirected to /login.
 *
 * ── Storage keys ──────────────────────────────────────────────────────────────
 *   localStorage.access_token   — short-lived JWT (5–60 min)
 *   localStorage.refresh_token  — long-lived refresh token (1–30 days)
 */

import axios from 'axios'

// ── Instance ──────────────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // Allow cookies to be sent cross-origin (needed if you use session auth fallback)
  withCredentials: false,
})

// ── Paths that never carry an Authorization header ────────────────────────────
const PUBLIC_PATHS = ['/auth/login/', '/auth/refresh/']

// ── Request interceptor — inject access token ─────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const isPublic = PUBLIC_PATHS.some((p) => config.url?.includes(p))
    if (!isPublic) {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor — silent token refresh on 401 ────────────────────────
let isRefreshing    = false           // prevent concurrent refresh loops
let refreshQueue    = []              // requests queued while refreshing

function processQueue(error, token = null) {
  refreshQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  refreshQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only intercept 401 responses that haven't already been retried
    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      PUBLIC_PATHS.some((p) => originalRequest.url?.includes(p))
    ) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      // Queue this request until refresh completes
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject })
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    const refreshToken = localStorage.getItem('refresh_token')

    if (!refreshToken) {
      // No refresh token — log the user out immediately
      _logout()
      return Promise.reject(error)
    }

    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/refresh/`,
        { refresh: refreshToken },
      )

      const newAccess = data.access
      localStorage.setItem('access_token', newAccess)

      // Update the default header for future requests
      api.defaults.headers.common.Authorization = `Bearer ${newAccess}`

      // Unblock all queued requests
      processQueue(null, newAccess)

      // Retry the original failed request
      originalRequest.headers.Authorization = `Bearer ${newAccess}`
      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      _logout()
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

// ── Logout helper ─────────────────────────────────────────────────────────────
function _logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  // Redirect to login — use window.location to avoid circular import with router
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}

export default api
