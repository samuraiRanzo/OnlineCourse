<template>
  <div class="lf-topbar">
    <button class="lf-topbar-hamburger" @click="$emit('toggle-sidebar')">
      <i class="pi pi-bars" />
    </button>

    <div class="lf-topbar-title display">{{ title }}</div>

    <!-- Teleport target: any view can <Teleport to="#topbar-actions"> its buttons here -->
    <div id="topbar-actions" class="lf-topbar-actions"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const routeTitles = {
  dashboard:           'Dashboard',
  students:            'Students',
  courses:             'Courses',
  'course-detail':     'Course Detail',
  'attendance-admin':  'Attendance',
  reports:             'Reports',
  'student-report':    'Student Report',
  announcements:       'Announcements',
  'my-courses':        'My Courses',
  'course-view':       'Course',
  'lesson-view':       'Lesson',
  'exam-view':         'Exam',
  'check-in':          'Check In',
  'my-attendance':     'My Attendance',
  notices:             'Notices',
  profile:             'Profile',
}
const title = computed(() => routeTitles[route.name] ?? 'LearnForge')
</script>