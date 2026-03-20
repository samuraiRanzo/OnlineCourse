<template>
  <div class="page-content">
    <div class="lf-code-wrap">
      <div class="lf-card" style="text-align:center;margin-bottom:20px">
        <div style="font-size:36px;margin-bottom:8px">📋</div>
        <div class="display" style="font-size:28px;letter-spacing:.5px">Enter Session Code</div>
        <p class="text-muted" style="margin-top:8px;font-size:14px">
          Ask your teacher for the code and enter it below to mark your attendance.
        </p>
      </div>

      <div class="lf-card">
        <div class="form-group">
          <label class="form-label">6-Character Code</label>
          <input
            v-model="code"
            type="text"
            class="lf-code-input"
            maxlength="6"
            placeholder="XXXXXX"
            @input="code = code.toUpperCase()"
            @keydown.enter="handleCheckIn"
          />
        </div>
        <button
          class="btn btn-primary btn-lg"
          style="width:100%"
          :disabled="loading || code.length < 6"
          @click="handleCheckIn"
        >
          {{ loading ? 'Checking in…' : 'Mark Me Present →' }}
        </button>
      </div>

      <!-- Result card -->
      <div v-if="result" style="margin-top:16px">
        <!-- Error: invalid code -->
        <div v-if="result.type === 'invalid'" class="result-card result-error">
          <div style="font-size:32px">❌</div>
          <div style="font-weight:700;margin-top:8px">Invalid Code</div>
          <p class="text-muted text-sm" style="margin-top:4px">Double-check the code with your teacher.</p>
        </div>

        <!-- Error: not enrolled -->
        <div v-else-if="result.type === 'not-enrolled'" class="result-card result-error">
          <div style="font-size:32px">⛔</div>
          <div style="font-weight:700;margin-top:8px">Not Enrolled</div>
          <p class="text-muted text-sm" style="margin-top:4px">You are not enrolled in the course this session belongs to.</p>
        </div>

        <!-- Already checked in -->
        <div v-else-if="result.type === 'already'" class="result-card result-warn">
          <div style="font-size:32px">ℹ️</div>
          <div style="font-weight:700;margin-top:8px">Already Checked In</div>
          <p class="text-muted text-sm" style="margin-top:4px">You already marked attendance for this session.</p>
        </div>

        <!-- Success -->
        <div v-else-if="result.type === 'success'" class="result-card result-success">
          <div style="font-size:40px">{{ result.cert ? '🏆' : '✅' }}</div>
          <div class="display" style="font-size:28px;letter-spacing:.5px;margin-top:8px">
            {{ result.cert ? 'Attendance Marked + Certificate Earned!' : 'Attendance Marked!' }}
          </div>
          <p class="text-muted" style="font-size:14px;margin-top:6px">
            <strong>{{ result.session.label }}</strong> · {{ result.session.course_title }}
          </p>

          <div style="margin-top:16px;padding-top:16px;border-top:1px solid #b7e4c7">
            <div style="font-size:12px;color:var(--lf-gray-600);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Your Attendance Rate</div>
            <div class="display" style="font-size:40px;color:#25a244">{{ result.stats.pct }}%</div>
            <div class="text-muted text-sm">{{ result.stats.attended }} of {{ result.stats.total }} sessions attended</div>
          </div>

          <div v-if="result.cert" style="margin-top:16px">
            <button class="cert-badge" @click="$router.push(`/my-courses/${result.session.course}`)">🎓 View Certificate</button>
          </div>
          <button class="btn btn-secondary" style="margin-top:16px" @click="$router.push('/my-attendance')">View My Attendance →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAttendanceStore } from '@/stores/attendance'
import { useCertificatesStore } from '@/stores/certificates'

const attStore  = useAttendanceStore()
const certStore = useCertificatesStore()

const code    = ref('')
const loading = ref(false)
const result  = ref(null)

async function handleCheckIn() {
  if (code.value.length < 6) return
  loading.value = true
  result.value  = null
  try {
    const data = await attStore.checkIn(code.value)
    if (data.already_checked_in) {
      result.value = { type: 'already' }
    } else {
      await certStore.fetchCertificates()
      const cert = certStore.getCertForCourse(data.session?.course)
      result.value = { type: 'success', session: data.session, stats: data.attendance_stats, cert }
      code.value = ''
    }
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail ?? ''
    if (status === 404) result.value = { type: 'invalid' }
    else if (status === 403) result.value = { type: 'not-enrolled' }
    else result.value = { type: 'invalid' }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.result-card { border-radius: 8px; padding: 28px; text-align: center; }
.result-success { border: 1.5px solid #25a244; background: #e6f7ee; }
.result-warn    { border: 1.5px solid var(--lf-orange); background: var(--lf-orange-light); }
.result-error   { border: 1.5px solid #e53e3e; background: #fff5f5; }
.form-group  { margin-bottom: 16px; }
.form-label  { display: block; font-size: 12px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-600); margin-bottom: 6px; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary   { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-secondary { background: var(--lf-black); color: #fff; }
.btn-lg { padding: 14px 32px; font-size: 16px; }
</style>