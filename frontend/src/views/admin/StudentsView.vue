<template>
  <div>
    <AppTopbar>
      <template #actions>
        <button class="btn btn-primary btn-sm" @click="showAdd = true">+ Add Student</button>
      </template>
    </AppTopbar>

    <div class="page-content">
      <div class="lf-card">
        <EmptyState v-if="!students.length" icon="👥" title="No students yet" message="Add your first student above." />
        <div v-else class="table-wrap">
          <table class="lf-table">
            <thead>
              <tr>
                <th>Name</th><th>Type</th><th>Email</th>
                <th>Enrolled In</th><th>Certs</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in students" :key="s.id">
                <td>
                  <div style="display:flex;align-items:center;gap:10px">
                    <div class="avatar">{{ s.name.charAt(0) }}</div>
                    <strong>{{ s.name }}</strong>
                  </div>
                </td>
                <td><span :class="['type-pill', `type-${s.student_type}`]">{{ s.student_type === 'online' ? '💻 Online' : '🏫 On-site' }}</span></td>
                <td class="text-muted">{{ s.email }}</td>
                <td>
                  <span v-if="!enrolledCourses(s.id).length" class="text-muted text-sm">None</span>
                  <span v-for="c in enrolledCourses(s.id)" :key="c.id" class="badge badge-gray" style="margin-right:4px">{{ c.course_title }}</span>
                </td>
                <td>
                  <span v-if="!studentCerts(s.id).length" class="text-muted text-sm">—</span>
                  <button
                    v-for="cert in studentCerts(s.id)"
                    :key="cert.id"
                    class="cert-badge"
                    @click="openCert(cert)"
                  >🎓 {{ cert.course_title }}</button>
                </td>
                <td>
                  <div style="display:flex;gap:6px">
                    <button class="btn btn-ghost btn-sm" @click="openEnroll(s)">Enroll</button>
                    <button class="btn btn-ghost btn-sm" @click="openReset(s)">Reset PW</button>
                    <button class="btn btn-danger btn-sm" @click="handleDelete(s.id)">Remove</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add student modal -->
    <BaseModal v-model="showAdd" title="Add New Student">
      <FormGroup label="Full Name"><input v-model="form.name" class="form-control" placeholder="Jane Doe" /></FormGroup>
      <FormGroup label="Email"><input v-model="form.email" type="email" class="form-control" placeholder="jane@example.com" /></FormGroup>
      <FormGroup label="Password"><input v-model="form.password" type="password" class="form-control" /></FormGroup>
      <FormGroup label="Student Type">
        <select v-model="form.student_type" class="form-control">
          <option value="online">💻 Online</option>
          <option value="onsite">🏫 On-site</option>
        </select>
      </FormGroup>
      <template #footer>
        <button class="btn btn-ghost" @click="showAdd = false">Cancel</button>
        <button class="btn btn-primary" :disabled="saving" @click="handleAdd">Create Account</button>
      </template>
    </BaseModal>

    <!-- Enroll modal -->
    <BaseModal v-model="showEnroll" :title="`Enroll ${selectedStudent?.name}`">
      <FormGroup label="Select Course">
        <select v-model="enrollCourseId" class="form-control">
          <option v-for="c in availableCourses" :key="c.id" :value="c.id">{{ c.title }}</option>
        </select>
      </FormGroup>
      <template #footer>
        <button class="btn btn-ghost" @click="showEnroll = false">Cancel</button>
        <button class="btn btn-primary" @click="handleEnroll">Enroll →</button>
      </template>
    </BaseModal>

    <!-- Reset password modal -->
    <BaseModal v-model="showReset" :title="`Reset Password — ${selectedStudent?.name}`">
      <FormGroup label="New Password">
        <input v-model="newPassword" type="password" class="form-control" placeholder="Min 6 characters" />
      </FormGroup>
      <template #footer>
        <button class="btn btn-ghost" @click="showReset = false">Cancel</button>
        <button class="btn btn-primary" @click="handleReset">Reset Password</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useToast }          from 'primevue/usetoast'
import AppTopbar             from '@/components/layout/AppTopbar.vue'
import BaseModal             from '@/components/ui/BaseModal.vue'
import FormGroup             from '@/components/ui/FormGroup.vue'
import EmptyState            from '@/components/ui/EmptyState.vue'
import { useStudentsStore }  from '@/stores/students'
import { useCoursesStore }   from '@/stores/courses'
import { useCertificatesStore } from '@/stores/certificates'

const studentsStore  = useStudentsStore()
const coursesStore   = useCoursesStore()
const certsStore     = useCertificatesStore()
const toast          = useToast()

const students    = computed(() => studentsStore.students)
const enrollments = ref([])
const showAdd     = ref(false)
const showEnroll  = ref(false)
const showReset   = ref(false)
const saving      = ref(false)

const selectedStudent = ref(null)
const enrollCourseId  = ref('')
const newPassword     = ref('')

const form = reactive({ name: '', email: '', password: '', student_type: 'online' })

function enrolledCourses(studentId) {
  return enrollments.value.filter(e => e.student === studentId)
}
function studentCerts(studentId) {
  return certsStore.certificates.filter(c => c.student === studentId)
}
function availableCourses() {
  if (!selectedStudent.value) return []
  const enrolled = enrolledCourses(selectedStudent.value.id).map(e => e.course)
  return coursesStore.courses.filter(c => !enrolled.includes(c.id))
}

async function handleAdd() {
  if (!form.name || !form.email || !form.password) return
  saving.value = true
  try {
    await studentsStore.createStudent({ ...form })
    Object.assign(form, { name: '', email: '', password: '', student_type: 'online' })
    showAdd.value = false
    toast.add({ severity: 'success', summary: 'Student created', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: e.response?.data?.email?.[0] ?? 'Error', life: 4000 })
  } finally { saving.value = false }
}

async function handleDelete(id) {
  if (!confirm('Remove this student?')) return
  await studentsStore.deleteStudent(id)
  enrollments.value = enrollments.value.filter(e => e.student !== id)
  toast.add({ severity: 'info', summary: 'Student removed', life: 3000 })
}

function openEnroll(student) {
  selectedStudent.value = student
  enrollCourseId.value  = availableCourses()[0]?.id ?? ''
  showEnroll.value      = true
}

async function handleEnroll() {
  if (!enrollCourseId.value) return
  const enroll = await coursesStore.createEnrollment(selectedStudent.value.id, enrollCourseId.value)
  enrollments.value.push(enroll)
  showEnroll.value = false
  toast.add({ severity: 'success', summary: 'Student enrolled', life: 3000 })
}

function openReset(student) {
  selectedStudent.value = student
  newPassword.value     = ''
  showReset.value       = true
}

async function handleReset() {
  if (!newPassword.value || newPassword.value.length < 6) return
  await studentsStore.resetPassword(selectedStudent.value.id, newPassword.value)
  showReset.value = false
  toast.add({ severity: 'success', summary: 'Password reset', life: 3000 })
}

function openCert(cert) {
  const student = students.value.find(s => s.id === cert.student)
  const course  = coursesStore.courses.find(c => c.id === cert.course)
  if (!student || !course) return
  const issued = new Date(cert.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  const html = buildCertHtml(student, course, cert, issued)
  const blob = new Blob([html], { type: 'text/html' })
  window.open(URL.createObjectURL(blob), '_blank')
}

function buildCertHtml(student, course, cert, issued) {
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Certificate</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&family=DM+Serif+Display:ital@1&display=swap" rel="stylesheet"/>
  <style>*{box-sizing:border-box;margin:0;padding:0}@page{size:A4 landscape;margin:0}body{width:297mm;height:210mm;display:flex;align-items:center;justify-content:center;background:#fff;font-family:'DM Sans',sans-serif;-webkit-print-color-adjust:exact}
  .cert{width:270mm;height:190mm;position:relative;border:1px solid #e8e8e8;border-radius:4px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 28mm;text-align:center;overflow:hidden}
  .cert::before{content:'';position:absolute;top:0;left:0;width:18mm;height:5px;background:#FF6B00}
  .cert::after{content:'';position:absolute;bottom:0;right:0;width:18mm;height:5px;background:#FF6B00}
  .wm{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-family:'Bebas Neue',sans-serif;font-size:140pt;color:#f5f5f5;letter-spacing:8px;pointer-events:none}
  .logo{font-family:'Bebas Neue',sans-serif;font-size:22pt;letter-spacing:3px;color:#0a0a0a;margin-bottom:10mm}.logo span{color:#FF6B00}
  .presents{font-size:9pt;letter-spacing:2px;text-transform:uppercase;color:#a0a0a0;margin-bottom:6mm}
  .title{font-family:'DM Serif Display',serif;font-style:italic;font-size:32pt;color:#0a0a0a;margin-bottom:8mm}
  .name{font-family:'Bebas Neue',sans-serif;font-size:44pt;letter-spacing:4px;border-bottom:3px solid #FF6B00;padding-bottom:4mm;margin-bottom:8mm}
  .course{font-family:'Bebas Neue',sans-serif;font-size:22pt;color:#FF6B00;margin-bottom:8mm}
  .meta{display:flex;gap:16mm;font-size:8pt;color:#a0a0a0;text-transform:uppercase;letter-spacing:.8px}
  .meta-val{color:#0a0a0a;font-weight:600;font-size:9pt}
  .no-print{position:fixed;bottom:20px;right:20px} @media print{.no-print{display:none}}</style></head>
  <body><div class="cert"><div class="wm">LF</div>
  <div style="position:relative;z-index:1;display:flex;flex-direction:column;align-items:center">
  <div class="logo">LEARN<span>FORGE</span></div>
  <div class="presents">This certificate is presented to</div>
  <div class="name">${student.name}</div>
  <div style="font-size:10pt;color:#555;margin-bottom:5mm">for successfully completing</div>
  <div class="course">${course.title}</div>
  <div class="meta">
    <div><div>Issued</div><div class="meta-val">${issued}</div></div>
    <div><div>Certificate ID</div><div class="meta-val">${cert.cert_code}</div></div>
  </div></div></div>
  <div class="no-print"><button onclick="window.print()" style="padding:10px 24px;background:#FF6B00;color:#fff;border:none;border-radius:4px;font-size:14px;font-weight:600;cursor:pointer">🖨 Print</button></div>
  </body></html>`
}

onMounted(async () => {
  await Promise.all([
    studentsStore.fetchStudents(),
    coursesStore.fetchCourses(),
    certsStore.fetchCertificates(),
    coursesStore.fetchEnrollments().then(e => { enrollments.value = e }),
  ])
})
</script>

<style scoped>
.lf-table { width: 100%; border-collapse: collapse; }
.lf-table th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; letter-spacing: .7px; text-transform: uppercase; color: var(--lf-gray-600); border-bottom: 2px solid var(--lf-gray-200); }
.lf-table td { padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--lf-gray-200); vertical-align: middle; }
.lf-table tr:last-child td { border-bottom: none; }
.lf-table tr:hover td { background: var(--lf-gray-100); }
.table-wrap { overflow-x: auto; }
.avatar { width: 30px; height: 30px; background: var(--lf-orange); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 12px; flex-shrink: 0; }
.btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; border: none; border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; white-space: nowrap; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary { background: var(--lf-orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--lf-orange-dark); }
.btn-ghost  { background: transparent; color: var(--lf-gray-600); border: 1px solid var(--lf-gray-200); }
.btn-ghost:hover { border-color: var(--lf-black); color: var(--lf-black); }
.btn-danger { background: #e53e3e; color: #fff; }
.btn-danger:hover { background: #c53030; }
.form-control { width: 100%; padding: 10px 14px; border: 2px solid var(--lf-gray-200); border-radius: var(--lf-radius); font-family: var(--lf-font-body); font-size: 14px; outline: none; }
.form-control:focus { border-color: var(--lf-orange); }
</style>
