<template>
  <button
    class="btn"
    :class="[`btn-${variant}`, size ? `btn-${size}` : '']"
    :disabled="disabled || loading"
    v-bind="$attrs"
  >
    <span v-if="loading" class="btn-spinner" />
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant:  { type: String,  default: 'primary' },
  size:     { type: String,  default: '' },
  disabled: { type: Boolean, default: false },
  loading:  { type: Boolean, default: false },
})
</script>

<style scoped>
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 20px; border: none; border-radius: var(--lf-radius);
  font-family: var(--lf-font-body); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all .18s ease; white-space: nowrap;
}
.btn:disabled { opacity: .55; cursor: not-allowed; transform: none !important; }
.btn-primary  { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled)  { background: var(--lf-orange-dark); transform: translateY(-1px); }
.btn-secondary { background: var(--lf-black); color: #fff; }
.btn-secondary:hover:not(:disabled) { background: #222; }
.btn-outline  { background: transparent; color: var(--lf-black); border: 2px solid var(--lf-black); }
.btn-outline:hover:not(:disabled)  { background: var(--lf-black); color: #fff; }
.btn-ghost    { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover:not(:disabled)    { border-color: var(--lf-black); color: var(--lf-black); }
.btn-danger   { background: #e53e3e; color: #fff; }
.btn-danger:hover:not(:disabled)   { background: #c53030; }
.btn-sm  { padding: 6px 14px; font-size: 12px; }
.btn-lg  { padding: 14px 32px; font-size: 16px; }
.btn-spinner {
  width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.4);
  border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
