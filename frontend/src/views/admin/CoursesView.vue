<template>
  <div>
    <Teleport v-if="teleportReady" to="#topbar-actions">
      <button class="btn btn-primary btn-sm" @click="showCreate = true">+ New Course</button>
    </Teleport>

    <div class="page-content">
      <!-- Status filter tabs -->
      <div class="filter-tabs">
        <button
            v-for="tab in filterTabs" :key="tab.key"
            class="filter-tab"
            :class="{ active: statusFilter === tab.key }"
            @click="statusFilter = tab.key"
        >
          {{ tab.label }}
          <span class="filter-count">{{ tabCount(tab.key) }}</span>
        </button>
      </div>

      <EmptyState
          v-if="!filteredCourses.length && !loading"
          icon="📚"
          title="No courses yet"
          message="Create your first course."
      />

      <div v-else class="courses-grid">
        <CourseCard
            v-for="c in filteredCourses" :key="c.id"
            :course="c"
            :show-status-bar="true"
            :toggling="toggling === c.id"
            @click="$router.push(`/courses/${c.id}`)"
            @toggle-status="toggleStatus"
        />
      </div>
    </div>

    <BaseModal v-model="showCreate" title="Create New Course">
      <FormGroup label="Course Title"><input v-model="form.title" class="form-control"
                                             placeholder="e.g. Python Fundamentals"/></FormGroup>
      <FormGroup label="Description"><textarea v-model="form.description" class="form-control" rows="3"
                                               placeholder="What will students learn?"/></FormGroup>
      <FormGroup label="Icon (emoji)"><input v-model="form.icon" class="form-control" placeholder="📚" maxlength="2"/>
      </FormGroup>
      <FormGroup label="Attendance Threshold (%)"><input v-model.number="form.attendance_threshold" type="number"
                                                         class="form-control" min="0" max="100"/></FormGroup>
      <div
          style="background:var(--lf-orange-light);border:1.5px solid var(--lf-orange);border-radius:6px;padding:12px;font-size:13px;color:var(--lf-orange-dark)">
        ℹ️ New courses start as <strong>Draft</strong>. Publish when ready so students can see it.
      </div>
      <template #footer>
        <button class="btn btn-ghost" @click="showCreate = false">Cancel</button>
        <button class="btn btn-primary" :disabled="saving" @click="handleCreate">Create Draft</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted} from 'vue'
import {useToast} from 'primevue/usetoast'
import BaseModal from '@/components/ui/BaseModal.vue'
import FormGroup from '@/components/ui/FormGroup.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import CourseCard from '@/components/shared/CourseCard.vue'
import {useCoursesStore} from '@/stores/courses'

import {useTeleportReady} from '@/composables/useTeleportReady'

const teleportReady = useTeleportReady()
const store = useCoursesStore()
const toast = useToast()

const courses = computed(() => store.courses)
const loading = computed(() => store.loading)
const showCreate = ref(false)
const saving = ref(false)
const toggling = ref(null)
const statusFilter = ref('all')

const form = reactive({title: '', description: '', icon: '📚', attendance_threshold: 75})

const filterTabs = [
  {key: 'all', label: 'All'},
  {key: 'published', label: '✓ Published'},
  {key: 'draft', label: '✎ Drafts'},
]

const filteredCourses = computed(() =>
    statusFilter.value === 'all'
        ? courses.value
        : courses.value.filter(c => c.status === statusFilter.value)
)

function tabCount(tab) {
  if (tab === 'all') return courses.value.length
  return courses.value.filter(c => c.status === tab).length
}

async function toggleStatus(course) {
  toggling.value = course.id
  try {
    if (course.status === 'published') {
      await store.unpublishCourse(course.id)
      toast.add({severity: 'info', summary: `"${course.title}" moved to draft`, life: 3000})
    } else {
      await store.publishCourse(course.id)
      toast.add({severity: 'success', summary: `"${course.title}" is now live`, life: 3000})
    }
  } catch {
    toast.add({severity: 'error', summary: 'Failed to update status', life: 3000})
  } finally {
    toggling.value = null
  }
}

async function handleCreate() {
  if (!form.title) return
  saving.value = true
  try {
    await store.createCourse({...form})
    Object.assign(form, {title: '', description: '', icon: '📚', attendance_threshold: 75})
    showCreate.value = false
    toast.add({severity: 'success', summary: 'Course created as draft', life: 3000})
  } finally {
    saving.value = false
  }
}

onMounted(() => store.fetchCourses())
</script>

<style scoped>
.filter-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-tab {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  background: transparent;
  border: 1.5px solid var(--lf-gray-200);
  color: var(--lf-gray-600);
  cursor: pointer;
  transition: all .15s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-tab:hover {
  border-color: var(--lf-black);
  color: var(--lf-black);
}

.filter-tab.active {
  background: var(--lf-black);
  color: #fff;
  border-color: var(--lf-black);
}

.filter-count {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--lf-gray-200);
  color: var(--lf-gray-600);
}

.filter-tab.active .filter-count {
  background: rgba(255, 255, 255, .2);
  color: #fff;
}
</style>