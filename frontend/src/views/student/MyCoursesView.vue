<template>
  <div class="page-content">
    <EmptyState v-if="!enriched.length && !loading" icon="📚" title="No courses yet" message="Ask your teacher to enroll you in a course." />
    <div v-else class="courses-grid">
      <CourseCard
        v-for="e in enriched" :key="e.id"
        :course="e.courseObj"
        :enrollment="e"
        :exam-result="courseResult(e.course)"
        :has-cert="hasCert(e.course)"
        :is-onsite="auth.isOnsite"
        @click="$router.push(`/my-courses/${e.course}`)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted }    from 'vue'
import { useAuthStore }           from '@/stores/auth'
import { useCoursesStore }        from '@/stores/courses'
import { useExamsStore }          from '@/stores/exams'
import { useCertificatesStore }   from '@/stores/certificates'
import CourseCard                 from '@/components/shared/CourseCard.vue'
import EmptyState                 from '@/components/ui/EmptyState.vue'

const auth    = useAuthStore()
const courses = useCoursesStore()
const exams   = useExamsStore()
const certs   = useCertificatesStore()

const loading = computed(() => courses.loading)

const enriched = computed(() =>
  courses.enrollments.map(e => ({
    ...e,
    courseObj: courses.courses.find(c => c.id === e.course) ?? { id: e.course, title: '…', lessons: [] },
  }))
)

function courseResult(courseId) {
  return exams.results.find(r => r.course_id === courseId) ?? null
}

function hasCert(courseId) {
  return certs.certificates.some(c => c.course === courseId)
}

onMounted(() => Promise.all([
  courses.fetchCourses(),
  courses.fetchEnrollments(),
  exams.fetchResults(),
  certs.fetchCertificates(),
]))
</script>

<style scoped>
.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 20px; }
</style>
