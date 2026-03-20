<template>
  <!-- Overlay (mobile only) — click to close sidebar -->
  <div
    class="lf-sidebar-overlay"
    :class="{ open: sidebarOpen }"
    @click="sidebarOpen = false"
  ></div>

  <div class="lf-shell">
    <AppSidebar :open="sidebarOpen" @close="sidebarOpen = false" />
    <main class="lf-main-content">
      <AppTopbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />

        <RouterView />

    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AppTopbar  from './AppTopbar.vue'

const sidebarOpen = ref(false)
</script>