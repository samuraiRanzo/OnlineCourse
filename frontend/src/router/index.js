import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ── First-run setup ───────────────────────────────────────────────
    {
      path: '/setup',
      name: 'setup',
      component: () => import('@/views/auth/SetupView.vue'),
      meta: { public: true },
    },

    // ── Auth ──────────────────────────────────────────────────────────
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true },
    },

    // ── App shell ─────────────────────────────────────────────────────
    {
      path: '/',
      component: () => import('@/components/layout/AppShell.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },

        { path: 'dashboard',   name: 'dashboard',   component: () => import('@/views/DashboardView.vue') },

        // Admin
        { path: 'students',    name: 'students',    component: () => import('@/views/admin/StudentsView.vue'),      meta: { adminOnly: true } },
        { path: 'courses',     name: 'courses',     component: () => import('@/views/admin/CoursesView.vue'),       meta: { adminOnly: true } },
        { path: 'courses/:id', name: 'course-detail', component: () => import('@/views/admin/CourseDetailView.vue'), meta: { adminOnly: true } },
        { path: 'attendance',  name: 'attendance-admin', component: () => import('@/views/admin/AttendanceView.vue'), meta: { adminOnly: true } },
        { path: 'reports',     name: 'reports',     component: () => import('@/views/admin/ReportsView.vue'),       meta: { adminOnly: true } },
        { path: 'reports/:id', name: 'student-report', component: () => import('@/views/admin/StudentReportView.vue'), meta: { adminOnly: true } },
        { path: 'announcements', name: 'announcements', component: () => import('@/views/admin/AnnouncementsView.vue'), meta: { adminOnly: true } },

        // Student
        { path: 'my-courses',  name: 'my-courses',  component: () => import('@/views/student/MyCoursesView.vue'),  meta: { studentOnly: true } },
        { path: 'my-courses/:id', name: 'course-view', component: () => import('@/views/student/CourseView.vue'),  meta: { studentOnly: true } },
        { path: 'my-courses/:courseId/lessons/:lessonId', name: 'lesson-view', component: () => import('@/views/student/LessonView.vue'), meta: { studentOnly: true } },
        { path: 'my-courses/:courseId/exam', name: 'exam-view', component: () => import('@/views/student/ExamView.vue'), meta: { studentOnly: true } },
        { path: 'check-in',    name: 'check-in',    component: () => import('@/views/student/CheckInView.vue'),    meta: { studentOnly: true } },
        { path: 'my-attendance', name: 'my-attendance', component: () => import('@/views/student/MyAttendanceView.vue'), meta: { studentOnly: true } },
        { path: 'notices',     name: 'notices',     component: () => import('@/views/student/NoticesView.vue'),    meta: { studentOnly: true } },
        { path: 'profile',     name: 'profile',     component: () => import('@/views/student/ProfileView.vue'),    meta: { studentOnly: true } },
      ],
    },

    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

// ── Navigation guard ──────────────────────────────────────────────────
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // Always allow public routes through immediately
  if (to.meta.public) return next()

  // ── First-run check: if no users exist, redirect to /setup ──────────
  // Only run this check once per session (cache the result)
  if (!router._setupChecked) {
    try {
      const { data } = await api.get('/users/needs-setup/')
      router._setupChecked = true
      if (data.needs_setup && to.path !== '/setup') {
        return next('/setup')
      }
    } catch {
      router._setupChecked = true
    }
  }

  // Already on setup — don't loop
  if (to.path === '/setup') return next()

  // ── Auth check ───────────────────────────────────────────────────────
  if (!auth.isLoggedIn) return next('/login')

  if (to.meta.adminOnly   && !auth.isAdmin)   return next('/dashboard')
  if (to.meta.studentOnly && !auth.isStudent) return next('/dashboard')

  next()
})

export default router
