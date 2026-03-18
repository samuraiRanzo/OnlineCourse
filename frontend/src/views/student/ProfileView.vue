<template>
  <div class="page-content">
    <div style="max-width:480px">

      <!-- Avatar + name header -->
      <div class="lf-card" style="display:flex;align-items:center;gap:16px;margin-bottom:24px">
        <div class="big-avatar">{{ auth.user?.name?.charAt(0).toUpperCase() }}</div>
        <div>
          <div class="display" style="font-size:26px;letter-spacing:.5px">{{ auth.user?.name }}</div>
          <div class="text-muted text-sm">{{ auth.user?.email }}</div>
          <span :class="['type-pill', `type-${auth.user?.student_type}`]" style="margin-top:6px;display:inline-flex">
            {{ auth.isOnsite ? '🏫 On-site' : '💻 Online' }}
          </span>
        </div>
      </div>

      <!-- Update name -->
      <div class="lf-card" style="margin-bottom:20px">
        <div class="card-title" style="margin-bottom:16px">Update Name</div>
        <FormGroup label="Display Name">
          <input v-model="nameForm.name" class="form-control" :placeholder="auth.user?.name" />
        </FormGroup>
        <button class="btn btn-primary" :disabled="savingName || !nameForm.name.trim()" @click="saveName">
          {{ savingName ? 'Saving…' : 'Save Name' }}
        </button>
      </div>

      <!-- Change password -->
      <div class="lf-card">
        <div class="card-title" style="margin-bottom:16px">Change Password</div>
        <FormGroup label="Current Password">
          <input v-model="pwForm.old_password" type="password" class="form-control" />
        </FormGroup>
        <FormGroup label="New Password">
          <input v-model="pwForm.password" type="password" class="form-control" placeholder="Min 6 characters" />
        </FormGroup>
        <FormGroup label="Confirm New Password">
          <input v-model="pwForm.confirm" type="password" class="form-control" />
        </FormGroup>
        <p v-if="pwError" style="color:#e53e3e;font-size:13px;margin-bottom:10px">{{ pwError }}</p>
        <button class="btn btn-primary" :disabled="savingPw" @click="savePassword">
          {{ savingPw ? 'Saving…' : 'Change Password' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useToast }      from 'primevue/usetoast'
import { useAuthStore }  from '@/stores/auth'
import FormGroup         from '@/components/ui/FormGroup.vue'

const auth  = useAuthStore()
const toast = useToast()

const savingName = ref(false)
const savingPw   = ref(false)
const pwError    = ref('')

const nameForm = reactive({ name: auth.user?.name ?? '' })
const pwForm   = reactive({ old_password: '', password: '', confirm: '' })

async function saveName() {
  if (!nameForm.name.trim()) return
  savingName.value = true
  try {
    await auth.updateMe({ name: nameForm.name })
    toast.add({ severity: 'success', summary: 'Name updated', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Failed to update name', life: 3000 })
  } finally {
    savingName.value = false
  }
}

async function savePassword() {
  pwError.value = ''
  if (!pwForm.old_password || !pwForm.password) { pwError.value = 'All fields are required.'; return }
  if (pwForm.password.length < 6)               { pwError.value = 'Password must be at least 6 characters.'; return }
  if (pwForm.password !== pwForm.confirm)        { pwError.value = 'New passwords do not match.'; return }

  savingPw.value = true
  try {
    await auth.updateMe({ old_password: pwForm.old_password, password: pwForm.password })
    Object.assign(pwForm, { old_password: '', password: '', confirm: '' })
    toast.add({ severity: 'success', summary: 'Password changed', life: 3000 })
  } catch (e) {
    const msg = e.response?.data?.old_password?.[0] ?? 'Failed to change password.'
    pwError.value = msg
  } finally {
    savingPw.value = false
  }
}
</script>

<style scoped>
.big-avatar { width: 56px; height: 56px; background: var(--lf-orange); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 24px; flex-shrink: 0; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: all .18s; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.form-control { width: 100%; padding: 10px 14px; border: 2px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; outline: none; transition: border-color .15s; }
.form-control:focus { border-color: var(--lf-orange); }
</style>
