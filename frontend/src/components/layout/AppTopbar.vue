<template>
  <div class="topbar">
    <div class="topbar-title display">{{ title }}</div>
    <div class="topbar-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const routeTitles = {
  dashboard:        'Dashboard',
  students:         'Students',
  courses:          'Courses',
  'course-detail':  'Course Detail',
  'attendance-admin': 'Attendance',
  reports:          'Reports',
  'student-report': 'Student Report',
  announcements:    'Announcements',
  'my-courses':     'My Courses',
  'course-view':    'Course',
  'lesson-view':    'Lesson',
  'exam-view':      'Exam',
  'check-in':       'Check In',
  'my-attendance':  'My Attendance',
  notices:          'Notices',
  profile:          'Profile',
}
const title = computed(() => routeTitles[route.name] ?? 'LearnForge')
</script>

<style scoped>
.topbar {
  background: var(--lf-white); border-bottom: 1.5px solid var(--lf-gray-200);
  padding: 16px 32px; display: flex; align-items: center; justify-content: space-between;
  position: sticky; top: 0; z-index: 50;
}
.topbar-title { font-size: 26px; }
.topbar-actions { display: flex; align-items: center; gap: 10px; }
</style>
