<template>
  <div class="lf-auth-page">
    <div class="lf-auth-left">
      <div class="setup-logo display">LEARN<span>FORGE</span></div>
      <p class="setup-tagline">Welcome. Let's get you set up.</p>
      <div class="setup-steps">
        <div class="setup-step" :class="{ done: step > 1, active: step === 1 }">
          <div class="step-dot">{{ step > 1 ? '✓' : '1' }}</div>
          <span>Create teacher account</span>
        </div>
        <div class="setup-step" :class="{ active: step === 2 }">
          <div class="step-dot">2</div>
          <span>Add students</span>
        </div>
        <div class="setup-step" :class="{ active: step === 3 }">
          <div class="step-dot">3</div>
          <span>Create your first course</span>
        </div>
      </div>
    </div>

    <div class="lf-auth-right">
      <div class="lf-auth-form-wrap">
        <div class="setup-badge">First-time setup</div>
        <h2 class="display" style="font-size:34px;letter-spacing:.5px;margin-top:10px">Create Teacher Account</h2>
        <p class="text-muted text-sm" style="margin-top:4px;margin-bottom:28px">
          This is the main admin account. You can add students after logging in.
        </p>

        <form @submit.prevent="handleSetup">
          <div class="form-group">
            <label class="form-label">Full Name</label>
            <input
              v-model="form.name"
              type="text"
              class="form-control"
              placeholder="Alex Teacher"
              required
              autofocus
            />
          </div>

          <div class="form-group">
            <label class="form-label">Email Address</label>
            <input
              v-model="form.email"
              type="email"
              class="form-control"
              placeholder="teacher@yourschool.com"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="form-control"
              placeholder="Min 6 characters"
              required
              minlength="6"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Confirm Password</label>
            <input
              v-model="form.confirm"
              type="password"
              class="form-control"
              placeholder="Repeat password"
              required
            />
          </div>

          <p v-if="error" class="form-error">{{ error }}</p>

          <button
            type="submit"
            class="btn btn-primary btn-lg"
            style="width:100%;margin-top:8px"
            :disabled="loading"
          >
            <span v-if="loading">Creating account…</span>
            <span v-else>Create Account &amp; Continue →</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter }     from 'vue-router'
import { useAuthStore }  from '@/stores/auth'
import api               from '@/api'

const router  = useRouter()
const auth    = useAuthStore()

const step    = ref(1)
const loading = ref(false)
const error   = ref('')
const form    = reactive({ name: '', email: '', password: '', confirm: '' })

async function handleSetup() {
  error.value = ''

  if (form.password.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }
  if (form.password !== form.confirm) {
    error.value = 'Passwords do not match.'
    return
  }

  loading.value = true
  try {
    // 1. Create the teacher account via the public setup endpoint
    await api.post('/users/setup/', {
      name:     form.name,
      email:    form.email,
      password: form.password,
    })

    // 2. Immediately log them in so they land on the dashboard
    await auth.login(form.email, form.password)
    router.push('/dashboard')
  } catch (e) {
    const data = e.response?.data
    if (data?.email)    error.value = data.email[0]
    else if (data?.detail) error.value = data.detail
    else error.value = 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.setup-logo    { font-size: 44px; color: #fff; letter-spacing: 2px; line-height: 1; }
.setup-logo span { color: var(--lf-orange); }
.setup-tagline { color: var(--lf-gray-400); font-size: 15px; margin-top: 12px; }
.setup-steps   { margin-top: 52px; display: flex; flex-direction: column; gap: 20px; }
.setup-step    { display: flex; align-items: center; gap: 14px; color: #555; font-size: 14px; transition: color .2s; }
.setup-step.active { color: #fff; }
.setup-step.done   { color: #25a244; }
.step-dot {
  width: 30px; height: 30px; border-radius: 50%;
  border: 2px solid #333; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0; transition: all .2s;
}
.setup-step.active .step-dot { border-color: var(--lf-orange); color: var(--lf-orange); }
.setup-step.done   .step-dot { border-color: #25a244; color: #25a244; }

.setup-badge {
  display: inline-block; padding: 4px 12px; background: var(--lf-orange-light);
  color: var(--lf-orange); border-radius: 20px; font-size: 12px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .5px;
}
.form-group  { margin-bottom: 16px; }
.form-label  { display: block; font-size: 12px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-600); margin-bottom: 6px; }
.form-control {
  width: 100%; padding: 10px 14px; border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px;
  background: var(--lf-white); color: var(--lf-black); outline: none; transition: border-color .15s;
}
.form-control:focus { border-color: var(--lf-orange); }
.form-error  { color: #e53e3e; font-size: 13px; margin-bottom: 10px; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-lg { padding: 14px 32px; font-size: 16px; }
</style>