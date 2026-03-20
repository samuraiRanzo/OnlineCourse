<template>
  <div class="page-content">
    <div class="stats-grid">
      <div class="stat-card accent">
        <div class="stat-label">Total Students</div>
        <div class="stat-value">{{ stats.students }}</div>
        <div class="stat-sub">{{ stats.online }} online · {{ stats.onsite }} on-site</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Courses</div>
        <div class="stat-value">{{ stats.courses }}</div>
        <div class="stat-sub">Active courses</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Sessions Held</div>
        <div class="stat-value">{{ stats.sessions }}</div>
        <div class="stat-sub">Attendance sessions</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Exams Taken</div>
        <div class="stat-value">{{ stats.exams }}</div>
        <div class="stat-sub">Submitted exams</div>
      </div>
    </div>

    <div class="lf-col-2">
      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">Recent Students</div>
          <RouterLink to="/students" class="btn btn-ghost btn-sm">View all</RouterLink>
        </div>
        <p v-if="!recentStudents.length" class="text-muted text-sm">No students yet.</p>
        <div v-else class="table-wrap">
        <table class="lf-table">
          <thead><tr><th>Name</th><th>Type</th><th>Email</th></tr></thead>
          <tbody>
            <tr v-for="s in recentStudents" :key="s.id">
              <td><strong>{{ s.name }}</strong></td>
              <td><span :class="['type-pill', `type-${s.student_type}`]">{{ s.student_type }}</span></td>
              <td class="text-muted">{{ s.email }}</td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>

      <div class="lf-card">
        <div class="section-header" style="margin-bottom:16px">
          <div class="card-title">Recent Exam Results</div>
        </div>
        <p v-if="!recentResults.length" class="text-muted text-sm">No results yet.</p>
        <div v-else  class="table-wrap">
        <table class="lf-table">
          <thead><tr><th>Student</th><th>Course</th><th>Score</th></tr></thead>
          <tbody>
            <tr v-for="r in recentResults" :key="r.id">
              <td>{{ r.student_name }}</td>
              <td class="text-muted">{{ r.course_title ?? '—' }}</td>
              <td><span :class="['badge', r.score >= 70 ? 'badge-green' : 'badge-orange']">{{ r.score }}%</span></td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useStudentsStore }  from '@/stores/students'
import { useCoursesStore }   from '@/stores/courses'
import { useAttendanceStore } from '@/stores/attendance'
import { useExamsStore }     from '@/stores/exams'

const studentsStore   = useStudentsStore()
const coursesStore    = useCoursesStore()
const attendanceStore = useAttendanceStore()
const examsStore      = useExamsStore()

const recentResults = ref([])

const recentStudents = computed(() =>
  [...studentsStore.students].reverse().slice(0, 5)
)

const stats = computed(() => ({
  students: studentsStore.students.length,
  online:   studentsStore.students.filter(s => s.student_type === 'online').length,
  onsite:   studentsStore.students.filter(s => s.student_type === 'onsite').length,
  courses:  coursesStore.courses.length,
  sessions: attendanceStore.sessions.length,
  exams:    recentResults.value.length,
}))

onMounted(async () => {
  await Promise.all([
    studentsStore.fetchStudents(),
    coursesStore.fetchCourses(),
    attendanceStore.fetchSessions(),
    examsStore.fetchResults().then(r => { recentResults.value = r.slice(0, 6) }),
  ])
})
</script>

<style scoped>
.lf-table { width: 100%; border-collapse: collapse; }
.lf-table th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; letter-spacing: .7px; text-transform: uppercase; color: var(--lf-gray-600); border-bottom: 2px solid var(--lf-gray-200); }
.lf-table td { padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--lf-gray-200); }
.lf-table tr:last-child td { border-bottom: none; }
.lf-table tr:hover td { background: var(--lf-gray-100); }
.btn { display: inline-flex; align-items: center; padding: 6px 14px; border: 1px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-size: 12px; font-weight: 600; cursor: pointer; background: transparent; color: var(--lf-gray-600); text-decoration: none; transition: all .15s; }
.btn:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-sm { padding: 6px 14px; font-size: 12px; }
.btn-ghost { background: transparent; }
</style>