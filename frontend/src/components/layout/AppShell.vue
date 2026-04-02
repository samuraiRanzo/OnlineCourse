<template>
  <div class="shell">
    <AppSidebar/>
    <main class="main-content">
      <AppTopbar/>
      <RouterView/>
    </main>
  </div>
</template>

<script setup>
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'
</script>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: 240px;
  flex: 1;
  min-height: 100vh;
  background: var(--lf-gray-100);
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
}
</style>
