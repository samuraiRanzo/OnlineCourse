<template>
  <div
    class="course-card"
    :class="{ 'has-status-bar': showStatusBar }"
    @click="$emit('click')"
  >
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

    <!-- ── Status bar (admin-only, shown when showStatusBar prop is true) ── -->
    <div
      v-if="showStatusBar"
      class="course-status-bar"
      :class="course.status"
      @click.stop
    >
      <div class="status-bar-top">
        <span class="status-badge" :class="course.status">
          {{ course.status === 'published' ? '✓ Published' : '✎ Draft' }}
        </span>
        <button
          class="status-btn"
          :class="course.status === 'published' ? 'btn-unpublish' : 'btn-publish'"
          :disabled="toggling"
          @click.stop="$emit('toggle-status', course)"
        >
          {{ toggling ? '…' : course.status === 'published' ? 'Unpublish' : 'Publish' }}
        </button>
      </div>
      <div class="status-bar-meta">
        <span v-if="course.status === 'published' && course.published_at">
          Live since {{ formatDate(course.published_at) }}
        </span>
        <span v-else>
          {{ course.published_lesson_count ?? 0 }}/{{ course.lesson_count ?? 0 }} lessons published
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  course:       { type: Object,  required: true },
  enrollment:   { type: Object,  default: null },
  examResult:   { type: Object,  default: null },
  attStats:     { type: Object,  default: null },
  hasCert:      { type: Boolean, default: false },
  isOnsite:     { type: Boolean, default: false },
  // Admin props for the status bar
  showStatusBar: { type: Boolean, default: false },
  toggling:      { type: Boolean, default: false },
})

defineEmits(['click', 'toggle-status'])

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

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}
</script>

<style scoped>
/* ── Card shell ── */
.course-card {
  background: var(--lf-white); border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px; overflow: hidden;
  transition: box-shadow .2s, transform .2s; cursor: pointer;
}
.course-card:hover { box-shadow: var(--lf-shadow-lg); transform: translateY(-2px); }

/* When status bar is present, square off the bottom corners of the body */
.course-card.has-status-bar { border-radius: 8px; }
.course-card.has-status-bar .course-card-body { border-radius: 0; }

/* ── Thumb ── */
.course-card-thumb {
  height: 140px; background: var(--lf-black); display: flex; align-items: center;
  justify-content: center; font-family: var(--lf-font-display); font-size: 40px;
  color: var(--lf-orange); position: relative;
}
.course-card-thumb::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0;
  height: 4px; background: var(--lf-orange);
}

/* ── Body ── */
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

/* ── Status bar ── */
.course-status-bar {
  padding: 10px 14px;
  border-top: 1.5px solid var(--lf-gray-200);
  background: var(--lf-gray-100);
  cursor: default;
}
.course-status-bar.published {
  border-top-color: #25a244;
  background: #f4fdf6;
}

.status-bar-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 4px;
}

.status-bar-meta {
  font-size: 12px; color: var(--lf-gray-400);
}

/* Badge */
.status-badge {
  display: inline-flex; align-items: center;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .5px; padding: 3px 10px; border-radius: 10px;
}
.status-badge.draft     { background: var(--lf-gray-200); color: var(--lf-gray-600); }
.status-badge.published { background: #d1fae5; color: #166534; }

/* Toggle button */
.status-btn {
  padding: 4px 14px; border-radius: var(--lf-radius);
  font-family: var(--lf-font-body); font-size: 12px; font-weight: 600;
  cursor: pointer; border: 1.5px solid; transition: all .15s; white-space: nowrap;
}
.status-btn:disabled { opacity: .55; cursor: not-allowed; }

.btn-publish {
  background: var(--lf-orange); border-color: var(--lf-orange); color: #fff;
}
.btn-publish:hover:not(:disabled) { background: var(--lf-orange-dark); border-color: var(--lf-orange-dark); }

.btn-unpublish {
  background: transparent; border-color: var(--lf-gray-200); color: var(--lf-gray-600);
}
.btn-unpublish:hover:not(:disabled) { background: #fff5f5; border-color: #e53e3e; color: #e53e3e; }
</style>