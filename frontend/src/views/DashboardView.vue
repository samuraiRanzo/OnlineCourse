<template>
  <div>
    <AdminDashboard v-if="auth.isAdmin" />
    <StudentDashboard v-else />
  </div>
</template>

<script setup>
import { useAuthStore }    from '@/stores/auth'
import AdminDashboard      from './admin/AdminDashboard.vue'
import StudentDashboard    from './student/StudentDashboard.vue'

const auth = useAuthStore()
</script>
