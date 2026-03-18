import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useCertificatesStore = defineStore('certificates', () => {
  const certificates = ref([])

  async function fetchCertificates(params = {}) {
    const { data } = await api.get('/certificates/', { params })
    certificates.value = data.results ?? data
    return certificates.value
  }

  function getCertForCourse(courseId) {
    return certificates.value.find(c => c.course === courseId) ?? null
  }

  return { certificates, fetchCertificates, getCertForCourse }
})
