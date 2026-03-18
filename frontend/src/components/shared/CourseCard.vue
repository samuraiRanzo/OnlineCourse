<template>
  <div class="course-card" @click="$emit('click')">
    <div class="course-card-thumb">{{ course.icon || '📚' }}</div>
    <div class="course-card-body">
      <div class="course-card-title display">{{ course.title }}</div>
      <div class="course-card-desc text-muted text-sm">{{ course.description }}</div>

      <div v-if="enrollment" style="margin-top:12px">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span class="text-sm text-muted">{{ isOnsite ? 'Attendance' : 'Progress' }}</span>
          <span class="text-sm font-600">{{ progressLabel }}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" :style="{ width: progressPct + '%' }" /></div>
      </div>

      <div class="course-card-meta">
        <div class="course-meta-item text-sm text-muted">
          <strong style="color:var(--lf-black)">{{ course.lesson_count ?? course.lessons?.length ?? 0 }}</strong> Lessons
        </div>
        <div style="display:flex;gap:6px;align-items:center">
          <span v-if="examResult" class="badge badge-green">Exam: {{ examResult.score }}%</span>
          <span v-else-if="course.exam" class="badge badge-orange">Exam pending</span>
          <span v-if="hasCert" class="badge badge-green">🎓 Certified</span>
          <span v-if="!course.exam && !enrollment" class="badge badge-gray">No Exam</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  course:     { type: Object, required: true },
  enrollment: { type: Object, default: null },
  examResult: { type: Object, default: null },
  attStats:   { type: Object, default: null },
  hasCert:    { type: Boolean, default: false },
  isOnsite:   { type: Boolean, default: false },
})
defineEmits(['click'])

const progressPct = computed(() => {
  if (props.isOnsite && props.attStats) return props.attStats.pct
  if (!props.enrollment) return 0
  return props.enrollment.lesson_completion_pct ?? 0
})

const progressLabel = computed(() => {
  if (props.isOnsite && props.attStats)
    return `${props.attStats.pct}% (${props.attStats.attended}/${props.attStats.total})`
  if (!props.enrollment) return '0%'
  return `${props.enrollment.lesson_completion_pct ?? 0}%`
})
</script>

<style scoped>
.course-card {
  background: var(--lf-white); border: 1.5px solid var(--lf-gray-200); border-radius: 8px;
  overflow: hidden; transition: box-shadow .2s, transform .2s; cursor: pointer;
}
.course-card:hover { box-shadow: var(--lf-shadow-lg); transform: translateY(-2px); }
.course-card-thumb {
  height: 140px; background: var(--lf-black); display: flex; align-items: center;
  justify-content: center; font-family: var(--lf-font-display); font-size: 40px;
  color: var(--lf-orange); position: relative;
}
.course-card-thumb::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0;
  height: 4px; background: var(--lf-orange);
}
.course-card-body  { padding: 18px; }
.course-card-title { font-size: 20px; letter-spacing: .3px; line-height: 1.2; }
.course-card-desc  {
  margin-top: 6px; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.course-card-meta {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--lf-gray-200);
}
</style>
