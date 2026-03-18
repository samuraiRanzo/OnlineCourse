<template>
  <div class="empty-state">
    <span class="empty-icon">{{ icon }}</span>
    <h3 class="display" style="font-size:24px;letter-spacing:.5px;color:var(--lf-black)">{{ title }}</h3>
    <p style="font-size:14px;margin-top:6px">{{ message }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  icon:    { type: String, default: '📭' },
  title:   { type: String, default: 'Nothing here yet' },
  message: { type: String, default: '' },
})
</script>
