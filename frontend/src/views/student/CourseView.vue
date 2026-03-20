<template>
  <div class="page-content" v-if="course">
    <div style="margin-bottom:16px">
      <button class="btn btn-ghost btn-sm" @click="$router.push('/my-courses')">← My Courses</button>
    </div>

    <div class="lf-content-sidebar">
      <!-- Main content -->
      <div>
        <div class="lf-card" style="margin-bottom:20px">
          <div class="card-title">{{ course.title }}</div>
          <p class="text-muted" style="margin-top:8px;font-size:14px">{{ course.description }}</p>

          <!-- Online: lesson progress bar -->
          <div v-if="!auth.isOnsite" style="margin-top:16px">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="text-sm text-muted">Overall Progress</span>
              <span class="text-sm font-600">{{ enrollment?.lesson_completion_pct ?? 0 }}% ({{ completedCount }}/{{ course.lessons?.length ?? 0 }})</span>
            </div>
            <div class="progress-bar" style="height:8px">
              <div class="progress-fill" :style="{ width: (enrollment?.lesson_completion_pct ?? 0) + '%' }" />
            </div>
          </div>

          <!-- Onsite: attendance bar -->
          <div v-else style="margin-top:16px;padding:16px;background:var(--lf-gray-100);border-radius:6px">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:13px;font-weight:600">Attendance</span>
              <span :class="attClass(attStats.pct)" style="font-size:14px">{{ attStats.pct }}% · {{ attStats.attended }}/{{ attStats.total }} sessions</span>
            </div>
            <div class="progress-bar" style="height:8px">
              <div class="progress-fill" :style="{ width: attStats.pct + '%' }" />
            </div>
            <div style="margin-top:6px;font-size:12px;color:var(--lf-gray-600)">
              Required threshold: <strong>{{ course.attendance_threshold }}%</strong>
              <span v-if="attStats.pct >= course.attendance_threshold" class="badge badge-green" style="margin-left:6px">On track ✓</span>
              <span v-else-if="attStats.total > 0" class="badge badge-red" style="margin-left:6px">Below threshold</span>
            </div>
          </div>
        </div>

        <div class="section-title" style="margin-bottom:12px">Lessons</div>
        <div class="lesson-list">
          <div
            v-for="(l, i) in course.lessons"
            :key="l.id"
            class="lesson-item"
            @click="$router.push(`/my-courses/${course.id}/lessons/${l.id}`)"
          >
            <div
              class="lesson-num"
              :style="completedIds.includes(l.id) ? 'background:var(--lf-orange);color:white' : ''"
            >
              {{ completedIds.includes(l.id) ? '✓' : i + 1 }}
            </div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ l.title }}</div>
              <div class="lesson-item-type">{{ l.type === 'video' ? '🎬 Video Lesson' : '📄 Text Lesson' }}</div>
            </div>
            <span style="color:var(--lf-gray-400);font-size:18px">›</span>
          </div>
        </div>
      </div>

      <!-- Sidebar card -->
      <div class="course-sidebar-card lf-sticky-card">
        <div class="course-sidebar-thumb">{{ course.icon || '📚' }}</div>
        <div class="course-sidebar-info">
          <h3 class="display" style="font-size:22px;letter-spacing:.4px">{{ course.title }}</h3>
          <div style="margin-top:12px;display:flex;flex-direction:column;gap:8px">
            <div style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Type</span>
              <span :class="['type-pill', `type-${auth.user?.student_type}`]">{{ auth.isOnsite ? '🏫 On-site' : '💻 Online' }}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Lessons</span>
              <strong>{{ course.lessons?.length ?? 0 }}</strong>
            </div>
            <div v-if="auth.isOnsite" style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Attendance</span>
              <strong :class="attClass(attStats.pct)">{{ attStats.pct }}%</strong>
            </div>
            <div v-else style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Progress</span>
              <strong>{{ enrollment?.lesson_completion_pct ?? 0 }}%</strong>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Exam</span>
              <strong>{{ course.exam ? 'Yes' : 'No' }}</strong>
            </div>
            <div v-if="examResult" style="display:flex;justify-content:space-between;font-size:13px">
              <span class="text-muted">Your Score</span>
              <strong class="text-orange">{{ examResult.score }}%</strong>
            </div>
          </div>

          <div style="margin-top:16px;display:flex;flex-direction:column;gap:8px">
            <button
              v-if="course.lessons?.length"
              class="btn btn-primary"
              style="width:100%"
              @click="startLesson"
            >
              {{ completedCount > 0 ? 'Continue Learning →' : 'Start Course →' }}
            </button>
            <button
              v-if="course.exam && allLessonsDone && !examResult"
              class="btn btn-secondary"
              style="width:100%"
              @click="$router.push(`/my-courses/${course.id}/exam`)"
            >
              Take Exam →
            </button>
            <div
              v-if="examResult"
              class="badge badge-green"
              style="text-align:center;padding:10px;display:block"
            >
              ✓ Exam: {{ examResult.score }}%
            </div>
            <button
              v-if="hasCert"
              class="cert-badge"
              style="justify-content:center"
              @click="openCert"
            >
              🎓 View Certificate
            </button>
            <button
              v-if="auth.isOnsite"
              class="btn btn-outline"
              style="width:100%"
              @click="$router.push('/check-in')"
            >
              📋 Check In to Session
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted }  from 'vue'
import { useRoute, useRouter }  from 'vue-router'
import { useAuthStore }         from '@/stores/auth'
import { useCoursesStore }      from '@/stores/courses'
import { useExamsStore }        from '@/stores/exams'
import { useCertificatesStore } from '@/stores/certificates'
import { useAttendanceStore }   from '@/stores/attendance'
import api                      from '@/api'

const route   = useRoute()
const router  = useRouter()
const auth    = useAuthStore()
const courses = useCoursesStore()
const exams   = useExamsStore()
const certs   = useCertificatesStore()
const attStore = useAttendanceStore()

const course     = computed(() => courses.current)
const enrollment = computed(() =>
  courses.enrollments.find(e => e.course === route.params.id)
)
const completedIds  = computed(() => enrollment.value?.completed_lesson_ids ?? [])
const completedCount = computed(() => completedIds.value.length)
const allLessonsDone = computed(() =>
  course.value?.lessons?.length > 0 &&
  course.value.lessons.every(l => completedIds.value.includes(l.id))
)
const examResult = computed(() =>
  exams.results.find(r => r.course_id === route.params.id) ?? null
)
const hasCert = computed(() =>
  certs.certificates.some(c => c.course === route.params.id)
)
const attStats = computed(() => {
  const sessions = attStore.sessions.filter(s => s.course === route.params.id)
  const total    = sessions.length
  if (!total || !auth.user) return { attended: 0, total: 0, pct: 0 }
  const attended = sessions.filter(s => s.attendee_ids?.includes(auth.user.id)).length
  return { attended, total, pct: Math.round((attended / total) * 100) }
})

function attClass(pct) {
  if (pct >= 75) return 'att-good'
  if (pct >= 50) return 'att-warn'
  return 'att-bad'
}

function startLesson() {
  const firstLesson = course.value?.lessons?.[0]
  if (firstLesson) router.push(`/my-courses/${route.params.id}/lessons/${firstLesson.id}`)
}

function openCert() {
  const cert     = certs.certificates.find(c => c.course === route.params.id)
  const student  = auth.user
  if (!cert || !student || !course.value) return
  const issued = new Date(cert.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  const track  = auth.isOnsite ? 'On-site Programme' : 'Online Programme'
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Certificate</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet"/>
  <style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5}
  .cert{background:#fff;max-width:640px;width:100%;padding:56px;text-align:center;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.1);position:relative;overflow:hidden}
  .cert::before{content:'';position:absolute;top:0;left:0;right:0;height:6px;background:#FF6B00}
  .logo{font-family:'Bebas Neue',sans-serif;font-size:24pt;letter-spacing:3px;margin-bottom:24px}.logo span{color:#FF6B00}
  .sub{font-size:10pt;color:#aaa;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px}
  .name{font-family:'Bebas Neue',sans-serif;font-size:40pt;letter-spacing:3px;color:#0a0a0a;border-bottom:3px solid #FF6B00;padding-bottom:16px;margin-bottom:20px}
  .course{font-family:'Bebas Neue',sans-serif;font-size:20pt;color:#FF6B00;margin-bottom:24px}
  .track{display:inline-block;padding:4px 16px;border:1.5px solid #0a0a0a;border-radius:20px;font-size:9pt;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:24px}
  .meta{font-size:10pt;color:#aaa;text-transform:uppercase;letter-spacing:.8px}
  .meta span{color:#0a0a0a;font-weight:600}
  .no-print{margin-top:24px}@media print{.no-print{display:none}}</style></head>
  <body><div class="cert">
  <div class="logo">LEARN<span>FORGE</span></div>
  <div class="sub">This certificate is presented to</div>
  <div class="name">${student.name}</div>
  <div class="sub">for successfully completing</div>
  <div class="course">${course.value.title}</div>
  <div class="track">${track}</div>
  <div class="meta"><p>Issued: <span>${issued}</span></p><p style="margin-top:4px">Certificate ID: <span>${cert.cert_code}</span></p></div>
  <div class="no-print" style="margin-top:28px">
  <button onclick="window.print()" style="padding:10px 28px;background:#FF6B00;color:#fff;border:none;border-radius:4px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;cursor:pointer">🖨 Print / Save PDF</button>
  </div></div></body></html>`
  window.open(URL.createObjectURL(new Blob([html], { type: 'text/html' })), '_blank')
}

onMounted(async () => {
  await Promise.all([
    courses.fetchCourse(route.params.id),
    courses.fetchEnrollments(),
    exams.fetchResults(),
    certs.fetchCertificates(),
    attStore.fetchSessions(route.params.id),
  ])
})
</script>

<style scoped>
.course-sidebar-card  { background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px; overflow: hidden; }
.course-sidebar-thumb { height: 160px; background: var(--lf-black); display: flex; align-items: center; justify-content: center; font-family: var(--lf-font-display); font-size: 56px; color: var(--lf-orange); }
.course-sidebar-info  { padding: 20px; }
.lesson-list  { border: 1.5px solid var(--lf-gray-200); border-radius: 6px; overflow: hidden; }
.lesson-item  { padding: 14px 18px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--lf-gray-200); cursor: pointer; transition: background .15s; }
.lesson-item:last-child { border-bottom: none; }
.lesson-item:hover  { background: var(--lf-gray-100); }
.lesson-num   { width: 28px; height: 28px; border-radius: 50%; background: var(--lf-gray-200); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; color: var(--lf-gray-600); }
.lesson-item-info  { flex: 1; }
.lesson-item-title { font-size: 14px; font-weight: 500; }
.lesson-item-type  { font-size: 12px; color: var(--lf-gray-400); }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s; }
.btn-primary  { background: var(--lf-orange); color: #fff; }
.btn-primary:hover  { background: var(--lf-orange-dark); }
.btn-secondary { background: var(--lf-black); color: #fff; }
.btn-outline  { background: transparent; color: var(--lf-black); border: 2px solid var(--lf-black); }
.btn-outline:hover { background: var(--lf-black); color: #fff; }
.btn-ghost    { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-sm { padding: 6px 14px; font-size: 12px; }

</style>