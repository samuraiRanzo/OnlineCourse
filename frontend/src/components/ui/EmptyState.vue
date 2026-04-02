<template>
  <div class="empty-state">
    <div class="empty-state-icon">{{ icon }}</div>
    <h3 class="empty-state-title display">{{ title || $t('emptyState.defaultTitle') }}</h3>
    <p v-if="message || $t('emptyState.defaultMessage')" class="empty-state-message text-muted">
      {{ message || $t('emptyState.defaultMessage') }}
    </p>
  </div>
</template>

<script setup>
import {useI18n} from 'vue-i18n'

// Initializing i18n
const {t} = useI18n()

defineProps({
  icon: {
    type: String,
    default: '📭'
  },
  title: {
    type: String,
    default: '' // Default handled in template via $t
  },
  message: {
    type: String,
    default: '' // Default handled in template via $t
  },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state-title {
  font-size: 20px;
  margin-bottom: 8px;
  color: var(--lf-black);
}

.empty-state-message {
  font-size: 14px;
  max-width: 300px;
}
</style>