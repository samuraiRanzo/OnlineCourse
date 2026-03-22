import {createRouter, createWebHistory} from 'vue-router'
import {useAuthStore} from '@/stores/auth'

// ── Lazy imports ───────────────────────────────────────────────────────────────
// Auth
const LoginView = () => import('@/views/auth/LoginView.vue')

// Shared shell
const AppShell = () => import('@/components/layout/AppShell.vue')

// Admin
const DashboardView = () => import('@/views/admin/AdminDashboard.vue')
const StudentsView = () => import('@/views/admin/StudentsView.vue')
const CoursesView = () => import('@/views/admin/CoursesView.vue')
const CourseDetailView = () => import('@/views/admin/CourseDetailView.vue')
const AttendanceView = () => import('@/views/admin/AttendanceView.vue')
const ReportsView = () => import('@/views/admin/ReportsView.vue')
const StudentReportView = () => import('@/views/admin/StudentReportView.vue')
const AnnouncementsView = () => import('@/views/admin/AnnouncementsView.vue')

// Student
const MyCoursesView = () => import('@/views/student/MyCoursesView.vue')
const CourseView = () => import('@/views/student/CourseView.vue')
const LessonView = () => import('@/views/student/LessonView.vue')
const ExamView = () => import('@/views/student/ExamView.vue')
const CheckInView = () => import('@/views/student/CheckInView.vue')
const MyAttendanceView = () => import('@/views/student/MyAttendanceView.vue')
const NoticesView = () => import('@/views/student/NoticesView.vue')

// Shared
const ProfileView = () => import('@/views/student/ProfileView.vue')

// ── Route definitions ──────────────────────────────────────────────────────────
const routes = [
    // Public
    {
        path: '/login',
        name: 'login',
        component: LoginView,
        meta: {public: true},
    },

    // Authenticated — all wrapped in AppShell
    {
        path: '/',
        component: AppShell,
        meta: {requiresAuth: true},
        children: [
            {path: '', redirect: '/dashboard'},

            // ── Admin ────────────────────────────────────────────────────────────────
            {
                path: 'dashboard',
                name: 'dashboard',
                component: DashboardView,
                meta: {title: 'Dashboard'},
            },
            {
                path: 'students',
                name: 'students',
                component: StudentsView,
                meta: {title: 'Students', adminOnly: true},
            },
            {
                path: 'courses',
                name: 'courses',
                component: CoursesView,
                meta: {title: 'Courses', adminOnly: true},
            },
            {
                path: 'courses/:id',
                name: 'course-detail',
                component: CourseDetailView,
                meta: {title: 'Course Detail', adminOnly: true},
            },
            {
                path: 'attendance',
                name: 'attendance-admin',
                component: AttendanceView,
                meta: {title: 'Attendance', adminOnly: true},
            },
            {
                path: 'reports',
                name: 'reports',
                component: ReportsView,
                meta: {title: 'Reports', adminOnly: true},
            },
            {
                path: 'reports/:id',
                name: 'student-report',
                component: StudentReportView,
                meta: {title: 'Student Report', adminOnly: true},
            },
            {
                path: 'announcements',
                name: 'announcements',
                component: AnnouncementsView,
                meta: {title: 'Announcements', adminOnly: true},
            },

            // ── Student ──────────────────────────────────────────────────────────────
            {
                path: 'my-courses',
                name: 'my-courses',
                component: MyCoursesView,
                meta: {title: 'My Courses', studentOnly: true},
            },
            {
                path: 'my-courses/:courseId',
                name: 'course-view',
                component: CourseView,
                meta: {title: 'Course', studentOnly: true},
            },
            {
                path: 'my-courses/:courseId/lessons/:lessonId',
                name: 'lesson-view',
                component: LessonView,
                meta: {title: 'Lesson', studentOnly: true},
            },
            {
                /**
                 * ExamView — student exam taking UI.
                 * Route: /my-courses/:courseId/exam
                 *
                 * ExamView reads route.params.courseId and calls:
                 *   1. coursesStore.fetchCourse(courseId)      — to get course title
                 *   2. examsStore.fetchExamByCourse(courseId)  — to get the exam object
                 *
                 * Navigation to this route happens from:
                 *   - LessonView sidebar "Take Exam →" button (when allDone === true)
                 *   - LessonView next-button when last lesson is complete
                 *   - Notification link (link: `/my-courses/${course.id}/exam`)
                 *   - MyCoursesView "Take Exam" CTA
                 */
                path: 'my-courses/:courseId/exam',
                name: 'exam-view',
                component: ExamView,
                meta: {title: 'Exam', studentOnly: true},
            },
            {
                path: 'check-in',
                name: 'check-in',
                component: CheckInView,
                meta: {title: 'Check In', studentOnly: true},
            },
            {
                path: 'my-attendance',
                name: 'my-attendance',
                component: MyAttendanceView,
                meta: {title: 'My Attendance', studentOnly: true},
            },
            {
                path: 'notices',
                name: 'notices',
                component: NoticesView,
                meta: {title: 'Notices', studentOnly: true},
            },

            // ── Shared ────────────────────────────────────────────────────────────────
            {
                path: 'profile',
                name: 'profile',
                component: ProfileView,
                meta: {title: 'Profile'},
            },
        ],
    },

    // Catch-all
    {path: '/:pathMatch(.*)*', redirect: '/'},
]

// ── Router instance ────────────────────────────────────────────────────────────
const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) return savedPosition
        return {top: 0}
    },
})

// ── Navigation guards ──────────────────────────────────────────────────────────
router.beforeEach(async (to) => {
    const auth = useAuthStore()

    // Initialise auth state from persisted token on first load
    if (!auth.user && auth.accessToken) {
        await auth.fetchUser().catch(() => {
        })
    }

    // Allow public routes always
    if (to.meta.public) return true

    // Redirect unauthenticated users to login
    if (!auth.user) return {name: 'login', query: {redirect: to.fullPath}}

    // Admin-only routes — block students
    if (to.meta.adminOnly && !auth.isAdmin) {
        return {name: 'my-courses'}
    }

    // Student-only routes — block admins
    if (to.meta.studentOnly && !auth.isStudent) {
        return {name: 'dashboard'}
    }

    return true
})

export default router
