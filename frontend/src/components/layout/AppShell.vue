<template>
  <div class="shell">
    <AppSidebar />
    <main class="main-content">
      <AppTopbar />
      <div class="page-content">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import AppSidebar from './AppSidebar.vue'
import AppTopbar  from './AppTopbar.vue'
</script>

<style scoped>
.shell        { display: flex; min-height: 100vh; }
.main-content { margin-left: 240px; flex: 1; min-height: 100vh; background: var(--lf-gray-100); }
</style>
