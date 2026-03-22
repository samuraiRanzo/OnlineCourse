<template>
  <div class="shell">
    <AppSidebar />
    <main class="main-content">
      <!--
        AppTopbar lives HERE and only here — never import it in views.
        Each view manages its own page-level action buttons inside its own
        page-actions-bar — no Teleport, no shared slot needed.
      -->
      <AppTopbar />
      <RouterView />
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

@media (max-width: 768px) {
  .main-content { margin-left: 0; }
}
</style>
