<template>
  <div>
    <AppTopbar>
      <template #actions>
        <button class="btn btn-primary btn-sm" @click="showCreate = true">+ New Course</button>
      </template>
    </AppTopbar>
    <div class="page-content">
      <EmptyState v-if="!courses.length && !loading" icon="📚" title="No courses yet" message="Create your first course." />
      <div v-else class="courses-grid">
        <CourseCard
          v-for="c in courses" :key="c.id"
          :course="c"
          @click="$router.push(`/courses/${c.id}`)"
        />
      </div>
    </div>

    <BaseModal v-model="showCreate" title="Create New Course">
      <FormGroup label="Course Title"><input v-model="form.title" class="form-control" placeholder="e.g. Python Fundamentals" /></FormGroup>
      <FormGroup label="Description"><textarea v-model="form.description" class="form-control" rows="3" placeholder="What will students learn?" /></FormGroup>
      <FormGroup label="Icon (emoji)"><input v-model="form.icon" class="form-control" placeholder="📚" maxlength="2" /></FormGroup>
      <FormGroup label="Attendance Threshold (%)"><input v-model.number="form.attendance_threshold" type="number" class="form-control" min="0" max="100" /></FormGroup>
      <template #footer>
        <button class="btn btn-ghost" @click="showCreate = false">Cancel</button>
        <button class="btn btn-primary" :disabled="saving" @click="handleCreate">Create Course</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useToast }         from 'primevue/usetoast'
import AppTopbar            from '@/components/layout/AppTopbar.vue'
import BaseModal            from '@/components/ui/BaseModal.vue'
import FormGroup            from '@/components/ui/FormGroup.vue'
import EmptyState           from '@/components/ui/EmptyState.vue'
import CourseCard           from '@/components/shared/CourseCard.vue'
import { useCoursesStore }  from '@/stores/courses'

const store  = useCoursesStore()
const toast  = useToast()
const courses  = computed(() => store.courses)
const loading  = computed(() => store.loading)
const showCreate = ref(false)
const saving     = ref(false)
const form = reactive({ title: '', description: '', icon: '📚', attendance_threshold: 75 })

async function handleCreate() {
  if (!form.title) return
  saving.value = true
  try {
    await store.createCourse({ ...form })
    Object.assign(form, { title: '', description: '', icon: '📚', attendance_threshold: 75 })
    showCreate.value = false
    toast.add({ severity: 'success', summary: 'Course created', life: 3000 })
  } finally { saving.value = false }
}

onMounted(() => store.fetchCourses())
</script>

<style scoped>
.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.btn { display: inline-flex; align-items: center; padding: 6px 14px; border: none; border-radius: var(--lf-radius); font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; }
.btn:disabled { opacity: .55; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-ghost { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-sm { padding: 6px 14px; font-size: 12px; }
.form-control { width: 100%; padding: 10px 14px; border: 2px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; outline: none; }
.form-control:focus { border-color: var(--lf-orange); }
</style>
