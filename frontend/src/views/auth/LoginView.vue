<template>
  <div class="lf-auth-page">
    <!-- Left panel -->
    <div class="lf-auth-left">
      <div class="login-logo display">LEARN<span>FORGE</span></div>
      <p class="login-tagline">Build skills. Take exams. Track progress.</p>
      <div class="login-features">
        <div class="login-feature"><div class="feat-icon">📚</div>Text &amp; Video lessons</div>
        <div class="login-feature"><div class="feat-icon">✍️</div>Built-in exam engine</div>
        <div class="login-feature"><div class="feat-icon">📋</div>Attendance tracking</div>
        <div class="login-feature"><div class="feat-icon">🎓</div>Auto-issued certificates</div>
      </div>
    </div>

    <!-- Right panel -->
    <div class="lf-auth-right">
      <div class="lf-auth-form-wrap">
        <h2 class="display" style="font-size:36px;letter-spacing:.5px">Welcome back</h2>
        <p class="text-muted text-sm" style="margin-top:4px;margin-bottom:32px">Sign in to continue to LearnForge</p>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label class="form-label">Email address</label>
            <input v-model="form.email" type="email" class="form-control" placeholder="you@example.com" required />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" placeholder="••••••••" required />
          </div>

          <p v-if="error" class="login-error">{{ error }}</p>

          <button type="submit" class="btn btn-primary btn-lg" style="width:100%;margin-top:8px" :disabled="loading">
            <span v-if="loading">Signing in…</span>
            <span v-else>Sign In →</span>
          </button>
        </form>

        <div class="login-divider"><hr /><span>DEMO ACCOUNTS</span><hr /></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-ghost btn-sm" style="flex:1" @click="quickLogin('admin@learnforge.com','admin123')">🎓 Teacher</button>
          <button class="btn btn-ghost btn-sm" style="flex:1" @click="quickLogin('online@learnforge.com','student123')">💻 Online</button>
          <button class="btn btn-ghost btn-sm" style="flex:1" @click="quickLogin('onsite@learnforge.com','student123')">🏫 On-site</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter }     from 'vue-router'
import { useAuthStore }  from '@/stores/auth'

const auth    = useAuthStore()
const router  = useRouter()
const loading = ref(false)
const error   = ref('')
const form    = reactive({ email: '', password: '' })

async function handleLogin() {
  loading.value = true
  error.value   = ''
  try {
    await auth.login(form.email, form.password)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}

function quickLogin(email, password) {
  form.email    = email
  form.password = password
  handleLogin()
}
</script>

<style scoped>
.login-logo    { font-size: 48px; color: #fff; letter-spacing: 2px; line-height: 1; }
.login-logo span { color: var(--lf-orange); }
.login-tagline { color: var(--lf-gray-400); font-size: 15px; margin-top: 12px; max-width: 260px; line-height: 1.5; }
.login-features { margin-top: 48px; display: flex; flex-direction: column; gap: 16px; }
.login-feature  { display: flex; align-items: center; gap: 12px; color: var(--lf-gray-400); font-size: 14px; }
.feat-icon      {
  width: 32px; height: 32px; background: rgba(255,107,0,.15); border-radius: 6px;
  display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
}
.login-error    { color: #e53e3e; font-size: 13px; margin-bottom: 10px; }
.login-divider  { display: flex; align-items: center; gap: 12px; margin: 20px 0; }
.login-divider hr { flex: 1; border: none; border-top: 1px solid var(--lf-gray-200); }
.login-divider span { font-size: 12px; color: var(--lf-gray-400); }

/* shared form control styles (not scoped — applies globally via main.css but repeat here for safety) */
.form-group  { margin-bottom: 16px; }
.form-label  { display: block; font-size: 12px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--lf-gray-600); margin-bottom: 6px; }
.form-control {
  width: 100%; padding: 10px 14px; border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px;
  background: var(--lf-white); color: var(--lf-black); transition: border-color .15s; outline: none;
}
.form-control:focus { border-color: var(--lf-orange); }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s ease; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-ghost   { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-sm  { padding: 6px 14px; font-size: 12px; }
.btn-lg  { padding: 14px 32px; font-size: 16px; }
</style>