<template>
  <div class="form-group">
    <label v-if="label" class="form-label">{{ label }}</label>
    <slot />
    <p v-if="error" class="form-error">{{ error }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  error: { type: String, default: '' },
})
</script>

<style scoped>
.form-group  { margin-bottom: 16px; }
.form-label  {
  display: block; font-size: 12px; font-weight: 600; letter-spacing: .6px;
  text-transform: uppercase; color: var(--lf-gray-600); margin-bottom: 6px;
}
.form-error  { font-size: 12px; color: #e53e3e; margin-top: 4px; }
</style>
