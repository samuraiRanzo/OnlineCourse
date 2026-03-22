<template>
  <div class="page-content">

    <!-- Loading -->
    <div v-if="loading" class="loading-wrap">
      <div class="spinner" />
      <p class="text-muted text-sm" style="margin-top:14px">Loading your courses…</p>
    </div>

    <!-- Empty -->
    <div v-else-if="!enrollments.length" class="empty-wrap">
      <div class="empty-icon">📚</div>
      <h2 class="display" style="font-size:32px;margin-bottom:8px">No courses yet</h2>
      <p class="text-muted text-sm">Ask your teacher to enroll you in a course.</p>
    </div>

    <!-- Course grid -->
    <div v-else>
      <div class="courses-header">
        <h1 class="display" style="font-size:36px;letter-spacing:.5px">My Courses</h1>
        <p class="text-muted text-sm" style="margin-top:4px">{{ enrollments.length }} course{{ enrollments.length === 1 ? '' : 's' }} enrolled</p>
      </div>

      <div class="course-grid">
        <div
          v-for="enroll in enrollments"
          :key="enroll.id"
          class="course-card"
        >
          <!-- Card header -->
          <div class="course-card-header">
            <div class="course-card-icon">{{ courseIcon(enroll.course_title) }}</div>
            <div class="course-card-meta">
              <div class="course-card-title display">{{ enroll.course_title }}</div>
              <div class="course-card-type text-muted text-sm">
                {{ auth.isOnsite ? '🏫 On-site' : '💻 Online' }}
              </div>
            </div>
          </div>

          <!-- Progress -->
          <div class="progress-section">
            <div class="progress-label">
              <span class="text-sm" style="font-weight:600">Lessons</span>
              <span class="text-muted text-sm">
                {{ completedCount(enroll) }}/{{ enroll.total_lessons ?? '?' }}
              </span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{ width: lessonProgressPct(enroll) + '%' }"
              />
            </div>
            <div class="text-muted text-sm" style="text-align:right;margin-top:3px">
              {{ lessonProgressPct(enroll) }}%
            </div>
          </div>

          <!-- Exam status -->
          <div class="status-row" v-if="enroll.has_exam">
            <span class="status-label">Exam</span>
            <template v-if="gradeData[enroll.course]?.exam_score !== null && gradeData[enroll.course]?.exam_score !== undefined">
              <span
                class="badge"
                :class="gradeData[enroll.course].passed ? 'badge-green' : 'badge-red'"
              >
                {{ gradeData[enroll.course].exam_score }}%
                {{ gradeData[enroll.course].passed ? '✓ Passed' : 'Not Passed' }}
              </span>
            </template>
            <span v-else class="badge badge-gray">Not Taken</span>
          </div>

          <!-- Assignment average -->
          <div class="status-row" v-if="gradeData[enroll.course]?.total_assignments">
            <span class="status-label">Assignments</span>
            <span class="text-sm">
              {{ gradeData[enroll.course].graded_submissions }}/{{ gradeData[enroll.course].total_assignments }} graded
              <template v-if="gradeData[enroll.course].assignment_avg !== null">
                · {{ gradeData[enroll.course].assignment_avg }}% avg
              </template>
            </span>
          </div>

          <!-- Final grade -->
          <div
            class="final-grade-row"
            v-if="gradeData[enroll.course]?.final_grade !== null && gradeData[enroll.course]?.final_grade !== undefined"
          >
            <div class="final-grade-label text-muted text-sm">Final Grade</div>
            <div
              class="final-grade-val display"
              :style="gradeData[enroll.course].passed ? 'color:#25a244' : 'color:#e53e3e'"
            >
              {{ gradeData[enroll.course].final_grade }}%
            </div>
          </div>
          <div v-else-if="gradeDataLoading[enroll.course]" class="final-grade-row">
            <div class="final-grade-label text-muted text-sm">Final Grade</div>
            <div class="text-muted text-sm">Loading…</div>
          </div>

          <!-- CTA button -->
          <div class="course-card-actions">
            <button
              v-if="nextLesson(enroll)"
              class="btn btn-primary btn-block"
              @click="goToLesson(enroll)"
            >
              {{ completedCount(enroll) === 0 ? 'Start Course →' : 'Continue →' }}
            </button>
            <button
              v-else-if="isAllLessonsComplete(enroll) && enroll.has_exam && !examTaken(enroll)"
              class="btn btn-primary btn-block"
              @click="router.push(`/my-courses/${enroll.course}/exam`)"
            >
              ✍ Take Exam
            </button>
            <button
              v-else-if="examTaken(enroll)"
              class="btn btn-ghost btn-block"
              @click="router.push(`/my-courses/${enroll.course}/exam`)"
            >
              View Results
            </button>
            <button
              v-else
              class="btn btn-ghost btn-block"
              @click="router.push(`/my-courses/${enroll.course}`)"
            >
              View Course
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter }       from 'vue-router'
import { useAuthStore }    from '@/stores/auth'
import { useCoursesStore } from '@/stores/courses'
import { useExamsStore }   from '@/stores/exams'
import api                 from '@/api'

const router   = useRouter()
const auth     = useAuthStore()
const courses  = useCoursesStore()
const exStore  = useExamsStore()

const loading          = ref(true)
const gradeData        = ref({})   // { [courseId]: finalGradePayload }
const gradeDataLoading = ref({})   // { [courseId]: bool }

const enrollments = computed(() => courses.enrollments ?? [])

// ── Helpers ───────────────────────────────────────────────────────────────────

function completedCount(enroll) {
  return enroll.completed_lesson_ids?.length ?? 0
}
function lessonProgressPct(enroll) {
  const total = enroll.total_lessons ?? 0
  if (!total) return 0
  return Math.round((completedCount(enroll) / total) * 100)
}
function isAllLessonsComplete(enroll) {
  return (enroll.total_lessons ?? 0) > 0 && completedCount(enroll) >= enroll.total_lessons
}
function examTaken(enroll) {
  return gradeData.value[enroll.course]?.submitted_count > 0
}
function nextLesson(enroll) {
  // Find first incomplete lesson from the course lesson list
  const courseObj = courses.courses?.find(c => c.id === enroll.course)
  if (!courseObj?.lessons?.length) return null
  const completed = enroll.completed_lesson_ids ?? []
  return courseObj.lessons.find(l => !completed.includes(l.id)) ?? null
}
function goToLesson(enroll) {
  const lesson = nextLesson(enroll)
  if (lesson) {
    router.push(`/my-courses/${enroll.course}/lessons/${lesson.id}`)
  } else {
    router.push(`/my-courses/${enroll.course}`)
  }
}
function courseIcon(title) {
  const t = (title ?? '').toLowerCase()
  if (t.includes('python') || t.includes('programm')) return '🐍'
  if (t.includes('java'))    return '☕'
  if (t.includes('web') || t.includes('html') || t.includes('css')) return '🌐'
  if (t.includes('data') || t.includes('sql'))  return '📊'
  if (t.includes('design'))  return '🎨'
  if (t.includes('math'))    return '📐'
  if (t.includes('english') || t.includes('writing')) return '✍️'
  if (t.includes('science')) return '🔬'
  return '📚'
}

// ── Load grade data per course ────────────────────────────────────────────────

async function loadGradeData(courseId) {
  gradeDataLoading.value[courseId] = true
  try {
    const { data } = await api.get(`/courses/${courseId}/final-grade/`)
    gradeData.value[courseId] = data
  } catch {
    // Grade not available yet — that's fine
    gradeData.value[courseId] = null
  } finally {
    gradeDataLoading.value[courseId] = false
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    await courses.fetchEnrollments()
    await courses.fetchCourses()
    // Load final grades in parallel — one call per enrolled course
    await Promise.all(enrollments.value.map(e => loadGradeData(e.course)))
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.loading-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}
.spinner {
  width: 40px; height: 40px;
  border-radius: 50%;
  border: 3px solid var(--lf-gray-200);
  border-top-color: var(--lf-orange);
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-wrap {
  text-align: center;
  padding: 80px 20px;
}
.empty-icon { font-size: 72px; margin-bottom: 16px; }

.courses-header { margin-bottom: 28px; }

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* ── Course card ── */
.course-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color .2s, box-shadow .2s;
}
.course-card:hover {
  border-color: var(--lf-orange);
  box-shadow: 0 4px 20px rgba(0,0,0,.06);
}

.course-card-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.course-card-icon {
  font-size: 40px;
  flex-shrink: 0;
  width: 56px; height: 56px;
  background: var(--lf-orange-light);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.course-card-meta { flex: 1; overflow: hidden; }
.course-card-title {
  font-size: 20px;
  letter-spacing: .3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.course-card-type { margin-top: 3px; }

/* ── Progress ── */
.progress-section { }
.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.progress-track {
  height: 8px;
  background: var(--lf-gray-200);
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--lf-orange);
  border-radius: 4px;
  transition: width .4s ease;
}

/* ── Status row ── */
.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.status-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: var(--lf-gray-400);
  min-width: 80px;
}

/* ── Final grade ── */
.final-grade-row {
  padding: 12px 14px;
  background: var(--lf-gray-100);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.final-grade-label { font-size: 13px; }
.final-grade-val   { font-size: 26px; }

/* ── CTA ── */
.course-card-actions { margin-top: auto; }
.btn-block { width: 100%; justify-content: center; }

/* ── Buttons ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 20px;
  border: none; border-radius: var(--lf-radius);
  font-family: var(--lf-font-body); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all .15s; white-space: nowrap;
  text-decoration: none;
}
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover { background: var(--lf-orange-dark); }
.btn-ghost   { background: transparent; color: var(--lf-gray-600); border: 1.5px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.text-sm   { font-size: 13px; }
.text-muted { color: var(--lf-gray-400); }
</style>
