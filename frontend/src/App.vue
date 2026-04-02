<template>
  <RouterView/>
  <Toast position="bottom-right"/>
</template>

<script setup>
import {onMounted} from 'vue'
import Toast from 'primevue/toast'
import {useI18n} from 'vue-i18n'

const {locale} = useI18n()

onMounted(() => {
  const initialLanguage = localStorage.getItem('lang')
  if (!initialLanguage) {
    localStorage.removeItem('lang')
    locale.value = 'mn'
    localStorage.setItem('lang', locale.value)
  } else {
    locale.value = localStorage.getItem('lang')
  }
})
</script>
