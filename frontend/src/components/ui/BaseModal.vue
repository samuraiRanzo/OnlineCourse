<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="$emit('update:modelValue', false)">
      <div class="modal" :style="{ maxWidth: width }">
        <div class="modal-header">
          <h3 class="display">{{ title }}</h3>
          <button class="modal-close" @click="$emit('update:modelValue', false)">✕</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String,  default: '' },
  width:      { type: String,  default: '560px' },
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 1000;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal {
  background: var(--lf-white); border-radius: 8px; width: 100%;
  max-height: 90vh; overflow-y: auto; box-shadow: var(--lf-shadow-lg);
}
.modal-header {
  padding: 20px 24px; border-bottom: 1.5px solid var(--lf-gray-200);
  display: flex; align-items: center; justify-content: space-between;
}
.modal-header h3 { font-size: 22px; letter-spacing: .4px; }
.modal-body   { padding: 24px; }
.modal-footer {
  padding: 16px 24px; border-top: 1.5px solid var(--lf-gray-200);
  display: flex; justify-content: flex-end; gap: 10px;
}
.modal-close {
  background: none; border: none; font-size: 22px; cursor: pointer;
  color: var(--lf-gray-600); line-height: 1; padding: 2px 6px;
}
.modal-close:hover { color: var(--lf-black); }
</style>
