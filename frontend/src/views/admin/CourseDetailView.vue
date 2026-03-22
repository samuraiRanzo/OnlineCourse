<template>
  <div class="page-content" v-if="course">
    <!-- Page actions bar — replaces the old Teleport-injected topbar buttons -->
    <div class="page-actions-bar">
      <div style="display:flex;align-items:center;gap:10px;min-width:0">
        <button class="btn btn-ghost btn-sm" @click="$router.push('/courses')">← Back</button>
        <div class="course-actions-title display" :title="course.title">{{ course.title }}</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
        <div class="course-status-pill" :class="course.status">
          {{ course.status === 'published' ? '✓ Published' : '✎ Draft' }}
        </div>
        <button
            class="btn btn-sm"
            :class="course.status==='published' ? 'btn-ghost' : 'btn-primary'"
            :disabled="togglingCourse"
            @click="handleToggleCourseStatus"
        >
          {{ togglingCourse ? '…' : course.status === 'published' ? 'Unpublish' : '🚀 Publish' }}
        </button>
        <button class="btn btn-danger btn-sm" @click="handleDelete">Delete</button>
      </div>
    </div>

    <div class="tabs">
      <div v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab===tab.key }"
           @click="activeTab=tab.key">
        {{ tab.label }}
        <span v-if="tab.key==='qa' && unresolvedQaCount>0" class="tab-badge">{{ unresolvedQaCount }}</span>
        <span v-if="tab.key==='grading' && pendingGradingCount>0" class="tab-badge"
              style="background:#e53e3e">{{ pendingGradingCount }}</span>
        <span v-if="tab.key==='students' && studentsCount>0" class="tab-badge"
              style="background:var(--lf-gray-400)">{{ studentsCount }}</span>
      </div>
    </div>

    <!-- ── LESSONS ── -->
    <div v-if="activeTab==='lessons'">
      <div class="section-header">
        <div class="section-title">
          Lessons ({{ course.lessons?.length ?? 0 }})
          <span class="text-muted text-sm" style="font-weight:400;margin-left:8px">{{
              publishedLessonCount
            }}/{{ course.lessons?.length ?? 0 }} published</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <button v-if="orderChanged" class="btn btn-secondary btn-sm" :disabled="reordering" @click="saveOrder">
            {{ reordering ? 'Saving…' : '💾 Save Order' }}
          </button>
          <button class="btn btn-primary btn-sm" @click="showAddLesson=true">+ Add Lesson</button>
        </div>
      </div>
      <EmptyState v-if="!localLessons.length" icon="📝" title="No lessons yet" message="Add your first lesson."/>
      <div v-else>
        <p class="text-muted text-sm" style="margin-bottom:10px">☰ Drag rows to reorder.</p>
        <div class="lesson-list">
          <div v-for="(l,i) in localLessons" :key="l.id" class="lesson-item"
               :class="{'drag-over':dragOverId===l.id,dragging:draggingId===l.id}" draggable="true"
               @dragstart="onDragStart($event,l.id)" @dragover.prevent="onDragOver($event,l.id)"
               @dragleave="onDragLeave" @drop.prevent="onDrop" @dragend="onDragEnd">
            <div class="drag-handle">☰</div>
            <div class="lesson-num">{{ i + 1 }}</div>
            <div class="lesson-item-info">
              <div class="lesson-item-title">{{ l.title }}</div>
              <div class="lesson-item-type" style="display:flex;align-items:center;gap:6px">
                {{ l.type === 'video' ? '🎬 Video' : '📄 Text' }}
                <span v-if="l.type==='video'&&l.video_file&&!l.hls_ready" class="badge badge-orange"
                      style="font-size:10px">⏳ Processing</span>
                <span v-else-if="l.type==='video'&&l.hls_ready" class="badge badge-green"
                      style="font-size:10px">✓ Ready</span>
              </div>
            </div>
            <div style="display:flex;gap:6px;align-items:center">
              <button class="lesson-status-btn" :class="l.status" :disabled="togglingLesson===l.id"
                      @click="handleToggleLessonStatus(l)">
                {{ togglingLesson === l.id ? '…' : l.status === 'published' ? '✓ Live' : '✎ Draft' }}
              </button>
              <button class="btn btn-ghost btn-sm" @click="openEditLesson(l)">Edit</button>
              <button class="btn btn-danger btn-sm" @click="handleDeleteLesson(l.id)">Del</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── EXAM BUILDER ── -->
    <div v-if="activeTab==='exam'">
      <div class="section-header">
        <div class="section-title">Exam Builder</div>
        <button class="btn btn-primary btn-sm" @click="saveExam">💾 Save Exam</button>
      </div>

      <!-- Settings card -->
      <div class="lf-card" style="margin-bottom:20px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <FormGroup label="Exam Title" style="grid-column:1/-1">
            <input v-model="examDraft.title" class="form-control"/>
          </FormGroup>
          <FormGroup label="Time Limit (minutes)">
            <input v-model.number="examDraft.time_limit_minutes" type="number" min="1" class="form-control"
                   placeholder="Leave blank for no limit"/>
            <p class="text-muted text-sm" style="margin-top:4px">When time runs out, exam auto-submits.</p>
          </FormGroup>
          <FormGroup label="Max Retakes">
            <select v-model.number="examDraft.max_retakes" class="form-control">
              <option :value="0">Unlimited</option>
              <option :value="1">1 attempt only</option>
              <option :value="2">2 attempts</option>
              <option :value="3">3 attempts</option>
              <option :value="5">5 attempts</option>
            </select>
          </FormGroup>
          <FormGroup label="Passing Score (%)">
            <input v-model.number="examDraft.passing_score" type="number" min="1" max="100" class="form-control"/>
          </FormGroup>
        </div>

        <!-- Grading weights -->
        <div class="weights-section">
          <div class="weights-label">
            <strong>Final Grade Weights</strong>
            <span class="text-muted text-sm" style="margin-left:8px">Must sum to 100%</span>
            <span v-if="weightsValid" class="badge badge-green" style="margin-left:8px;font-size:11px">✓ Valid</span>
            <span v-else class="badge badge-red" style="margin-left:8px;font-size:11px">⚠ Must sum to 100</span>
          </div>
          <div class="weights-row">
            <div class="weight-item">
              <label class="form-label">Exam Weight (%)</label>
              <input v-model.number="examDraft.exam_weight" type="number" min="0" max="100" class="form-control"
                     @input="syncAssignmentWeight"/>
            </div>
            <div class="weight-plus">+</div>
            <div class="weight-item">
              <label class="form-label">Assignments Weight (%)</label>
              <input v-model.number="examDraft.assignment_weight" type="number" min="0" max="100" class="form-control"
                     @input="syncExamWeight"/>
            </div>
            <div class="weight-equals">= {{ examDraft.exam_weight + examDraft.assignment_weight }}%</div>
          </div>
          <div class="weights-bar">
            <div class="weights-bar-exam" :style="{width: examDraft.exam_weight + '%'}"/>
            <div class="weights-bar-assign" :style="{width: examDraft.assignment_weight + '%'}"/>
          </div>
          <div
              style="display:flex;justify-content:space-between;font-size:11px;color:var(--lf-gray-400);margin-top:4px">
            <span>🎓 Exam: {{ examDraft.exam_weight }}%</span>
            <span>📋 Assignments: {{ examDraft.assignment_weight }}%</span>
          </div>
        </div>
      </div>

      <!-- Questions -->
      <div v-for="(q,qi) in examDraft.questions" :key="qi" class="question-builder">
        <div style="display:flex;justify-content:space-between;margin-bottom:12px">
          <strong>Q{{ qi + 1 }} — {{ q.type === 'mcq' ? 'Multiple Choice' : 'Open Answer' }}</strong>
          <button class="btn btn-danger btn-sm" @click="removeQuestion(qi)">Remove</button>
        </div>
        <FormGroup label="Question Text"><input v-model="q.text" class="form-control"/></FormGroup>
        <div v-if="q.type==='mcq'">
          <label class="form-label">Options (select correct)</label>
          <div v-for="(opt,oi) in q.options" :key="oi"
               style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
            <input type="radio" :name="`correct_${qi}`" :checked="q.correct_index===oi" @change="q.correct_index=oi"/>
            <input v-model="q.options[oi]" class="form-control" :placeholder="`Option ${oi+1}`"/>
            <button v-if="q.options.length>2" class="btn btn-ghost btn-sm" @click="q.options.splice(oi,1)">✕</button>
          </div>
          <button v-if="q.options.length<6" class="btn btn-ghost btn-sm" @click="q.options.push('')">+ Add Option
          </button>
        </div>
        <p v-else class="text-muted text-sm">Students type a free-form answer — reviewed manually in the Grading
          tab.</p>
      </div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button class="btn btn-secondary btn-sm" @click="addQuestion('mcq')">+ Multiple Choice</button>
        <button class="btn btn-outline btn-sm" @click="addQuestion('open')">+ Open Answer</button>
      </div>
    </div>

    <!-- ── SESSIONS ── -->
    <div v-if="activeTab==='sessions'">
      <div class="section-header">
        <div class="section-title">Sessions ({{ sessions.length }})</div>
        <button class="btn btn-primary btn-sm" @click="showAddSession=true">+ New Session</button>
      </div>
      <EmptyState v-if="!sessions.length" icon="📋" title="No sessions yet"
                  message="Create a session to track attendance."/>
      <div v-for="s in sessions" :key="s.id" class="session-item">
        <div class="session-date display">{{ formatDate(s.date) }}</div>
        <div class="session-info">
          <div class="session-label">{{ s.label }}</div>
          <div class="session-sub text-muted text-sm">{{ s.attendee_count }} attended · Code: <span
              class="session-code">{{ s.code }}</span></div>
        </div>
        <button class="btn btn-danger btn-sm" @click="handleDeleteSession(s.id)">Delete</button>
      </div>
    </div>

    <!-- ── ANNOUNCEMENTS ── -->
    <div v-if="activeTab==='announcements'">
      <div class="section-header">
        <div class="section-title">Announcements</div>
        <button class="btn btn-primary btn-sm" @click="showAddNotice=true">+ New Notice</button>
      </div>
      <EmptyState v-if="!announcements.length" icon="📣" title="No announcements"
                  message="Post a notice to enrolled students."/>
      <div v-for="n in announcements" :key="n.id" class="notice-card" :class="{pinned:n.pinned}">
        <div class="notice-card-header">
          <span>{{ n.pinned ? '📌' : '📣' }}</span>
          <div style="flex:1">
            <div style="font-weight:600">{{ n.title }}</div>
            <div class="text-muted text-sm">{{ formatDate(n.created_at) }}</div>
          </div>
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost btn-sm" @click="togglePin(n)">{{ n.pinned ? 'Unpin' : 'Pin' }}</button>
            <button class="btn btn-ghost btn-sm" @click="openEditNotice(n)">Edit</button>
            <button class="btn btn-danger btn-sm" @click="handleDeleteNotice(n.id)">Del</button>
          </div>
        </div>
        <div class="notice-card-body text-muted">{{ n.body }}</div>
      </div>
    </div>

    <!-- ── Q&A INBOX ── -->
    <div v-if="activeTab==='qa'">
      <div class="section-header">
        <div class="section-title">Q&amp;A Inbox <span v-if="unresolvedQaCount" class="badge badge-orange"
                                                       style="margin-left:10px">{{
            unresolvedQaCount
          }} unresolved</span></div>
        <div style="display:flex;gap:6px">
          <button v-for="f in qaFilters" :key="f.key" class="btn btn-sm"
                  :class="qaFilter===f.key?'btn-secondary':'btn-ghost'" @click="qaFilter=f.key">
            {{ f.label }}<span class="filter-count"
                               :class="qaFilter===f.key?'filter-count-active':''">{{ qaFilterCount(f.key) }}</span>
          </button>
        </div>
      </div>
      <div v-if="qaStore.loading" class="text-muted text-sm" style="padding:32px;text-align:center">Loading…</div>
      <EmptyState v-else-if="!filteredQaQuestions.length" icon="💬"
                  :title="qaFilter==='unresolved'?'No unresolved questions':'No questions'"
                  :message="qaFilter==='unresolved'?'All caught up!':'Questions from students will appear here.'"/>
      <div v-for="q in filteredQaQuestions" :key="q.id" class="qa-inbox-card" :class="{resolved:q.is_resolved}">
        <div class="qa-inbox-header" @click="toggleQaExpand(q.id)">
          <div class="qa-avatar">{{ q.author_name?.charAt(0).toUpperCase() }}</div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="font-size:14px;font-weight:600">{{ q.author_name }}</span>
              <span class="badge badge-gray" style="font-size:10px">{{ q.lesson_title }}</span>
              <span v-if="q.is_resolved" class="badge badge-green" style="font-size:10px">✓ Resolved</span>
            </div>
            <div class="text-muted text-sm"
                 style="margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ q.body }}
            </div>
          </div>
          <span class="text-muted text-sm">{{ formatDate(q.created_at) }}</span>
          <span style="color:var(--lf-gray-400);font-size:14px;transition:transform .15s"
                :style="expandedQaIds.has(q.id)?'transform:rotate(180deg)':''">▼</span>
        </div>
        <div v-if="expandedQaIds.has(q.id)" class="qa-inbox-body">
          <div class="qa-inbox-question-text">{{ q.body }}</div>
          <div v-if="q.answers?.length" class="qa-inbox-answers">
            <div v-for="a in q.answers" :key="a.id" class="qa-inbox-answer" :class="{'is-teacher':a.is_teacher}">
              <div class="qa-inbox-answer-header">
                <div class="qa-avatar sm" :style="a.is_teacher?'background:var(--lf-black)':''">
                  {{ a.author_name?.charAt(0).toUpperCase() }}
                </div>
                <span style="font-size:13px;font-weight:600">{{ a.author_name }}</span>
                <span v-if="a.is_teacher" class="badge badge-black" style="font-size:9px">Teacher</span>
                <button class="btn btn-ghost btn-sm" @click="handleQaDeleteAnswer(q,a.id)">✕</button>
              </div>
              <div class="qa-inbox-answer-body">{{ a.body }}</div>
            </div>
          </div>
          <div class="qa-inbox-compose">
            <textarea v-model="qaReplyText[q.id]" class="form-control" rows="3" placeholder="Write your answer…"
                      style="resize:vertical;font-size:14px;line-height:1.6"/>
            <div style="display:flex;justify-content:space-between;margin-top:10px;gap:8px;flex-wrap:wrap">
              <button class="btn btn-sm" :class="q.is_resolved?'btn-ghost':'btn-secondary'"
                      @click="handleQaToggleResolve(q)">{{ q.is_resolved ? '↩ Mark Unresolved' : '✓ Mark Resolved' }}
              </button>
              <button class="btn btn-primary btn-sm" :disabled="!qaReplyText[q.id]?.trim()"
                      @click="handleQaPostAnswer(q)">✓ Post Answer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── ANALYTICS ── -->
    <div v-if="activeTab==='analytics'">
      <div v-if="analyticsLoading" class="analytics-loading">
        <div class="spinner"/>
      </div>
      <div v-else-if="!analyticsData" class="empty-state"><span class="empty-icon">📊</span>
        <h3>No data yet</h3></div>
      <template v-else>
        <div class="stats-grid" style="margin-bottom:28px">
          <div class="stat-card accent">
            <div class="stat-label">Enrolled</div>
            <div class="stat-value">{{ analyticsData.enrolled_count }}</div>
            <div class="stat-sub">{{ analyticsData.online_count }} online · {{ analyticsData.onsite_count }} on-site
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Avg Score</div>
            <div class="stat-value">{{ analyticsData.avg_score !== null ? analyticsData.avg_score + '%' : '—' }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value">{{
                analyticsData.student_scores.length ? analyticsData.pass_rate + '%' : '—'
              }}
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Avg Completion</div>
            <div class="stat-value">{{ avgLessonCompletion }}%</div>
          </div>
        </div>
        <div class="analytics-charts-row">
          <div class="lf-card" v-if="analyticsData.student_scores.length">
            <div class="analytics-card-title">Score Distribution</div>
            <div class="chart-wrap" style="height:220px;margin-top:16px">
              <canvas ref="scoreChartEl"/>
            </div>
          </div>
          <div class="lf-card" v-if="analyticsData.attempts_over_time.length">
            <div class="analytics-card-title">Exam Activity</div>
            <div class="chart-wrap" style="height:220px;margin-top:16px">
              <canvas ref="activityChartEl"/>
            </div>
          </div>
        </div>
        <div class="lf-card" style="margin-top:20px" v-if="analyticsData.lesson_completion.length">
          <div class="analytics-card-title" style="margin-bottom:14px">Lesson Completion</div>
          <div class="lesson-completion-list">
            <div v-for="(l,i) in analyticsData.lesson_completion" :key="i" class="lc-row">
              <div class="lc-label text-sm">{{ l.lesson_title }}</div>
              <div class="lc-bar-wrap">
                <div class="lc-bar-fill"
                     :style="{width:l.pct+'%',background:l.pct>=75?'#25a244':l.pct>=40?'var(--lf-orange)':'#e53e3e'}"/>
              </div>
              <div class="lc-pct text-sm font-600">{{ l.pct }}%</div>
              <div class="lc-count text-muted text-sm">{{ l.completed }}/{{ l.total }}</div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ── ASSIGNMENTS ── -->
    <div v-if="activeTab==='assignments'">
      <div class="section-header">
        <div class="section-title">Assignments <span class="text-muted text-sm" style="font-weight:400;margin-left:8px">{{
            assignmentsStore.getByCourse(route.params.id).length
          }} total</span></div>
        <button class="btn btn-primary btn-sm" @click="openAddAssignment">+ New Assignment</button>
      </div>
      <EmptyState v-if="!assignmentsStore.getByCourse(route.params.id).length" icon="📋" title="No assignments yet"
                  message="Create assignments for any lesson in this course."/>
      <template v-else>
        <div v-for="lesson in lessonsWithAssignments" :key="lesson.id" style="margin-bottom:24px">
          <div class="assignment-lesson-label">📄 {{ lesson.title }}</div>
          <div v-for="a in assignmentsByLesson(lesson.id)" :key="a.id" class="assignment-card">
            <div class="assignment-card-header" @click="toggleAssignmentExpand(a.id)">
              <div style="flex:1;min-width:0">
                <div style="font-size:15px;font-weight:600">{{ a.title }}</div>
                <div class="text-muted text-sm"
                     style="margin-top:2px;display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                  <span>Max: {{ a.max_score }} pts</span>
                  <span v-if="a.due_date">· Due {{ formatDateTime(a.due_date) }}</span>
                  <span class="badge" :class="a.submission_count?'badge-orange':'badge-gray'">{{ a.submission_count }} submission{{
                      a.submission_count === 1 ? '' : 's'
                    }}</span>
                </div>
              </div>
              <div style="display:flex;gap:6px;align-items:center;flex-shrink:0">
                <button class="btn btn-ghost btn-sm" @click.stop="openEditAssignment(a)">Edit</button>
                <button class="btn btn-danger btn-sm" @click.stop="handleDeleteAssignment(a.id)">Del</button>
                <span class="expand-chevron" :class="{open:expandedAssignmentIds.has(a.id)}">▼</span>
              </div>
            </div>
            <div v-if="expandedAssignmentIds.has(a.id)" class="assignment-card-body">
              <p v-if="a.description" class="text-muted text-sm" style="margin-bottom:14px;white-space:pre-wrap">
                {{ a.description }}</p>
              <div class="submissions-sub-header">
                <span
                    style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--lf-gray-600)">Submissions</span>
                <button class="btn btn-ghost btn-sm" @click="loadSubmissions(a.id)">↻ Refresh</button>
              </div>
              <div v-if="submissionsLoading[a.id]" class="text-muted text-sm" style="padding:12px">Loading…</div>
              <div v-else-if="!assignmentsStore.getSubmissions(a.id).length" class="submissions-empty">No submissions
                yet.
              </div>
              <div v-else class="submissions-table-wrap">
                <table class="lf-table">
                  <thead>
                  <tr>
                    <th>Student</th>
                    <th>Answer</th>
                    <th>Submitted</th>
                    <th>Grade</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="sub in assignmentsStore.getSubmissions(a.id)" :key="sub.id">
                    <td><strong>{{ sub.student_name }}</strong><br><span class="text-muted text-sm">{{
                        sub.student_email
                      }}</span></td>
                    <td>
                      <div style="display:flex;gap:6px;flex-wrap:wrap"><a v-if="sub.file_url" :href="sub.file_url"
                                                                          target="_blank" class="btn btn-ghost btn-sm"
                                                                          style="text-decoration:none">⬇ File</a><span
                          v-if="sub.text_answer" class="badge badge-blue">Text</span></div>
                      <div v-if="sub.text_answer" class="sub-text-preview">{{
                          sub.text_answer.slice(0, 120)
                        }}{{ sub.text_answer.length > 120 ? '…' : '' }}
                      </div>
                    </td>
                    <td class="text-muted text-sm">{{ formatDate(sub.updated_at) }}</td>
                    <td>
                      <div v-if="sub.is_graded" style="margin-bottom:6px"><span class="display" style="font-size:18px"
                                                                                :style="sub.score>=(a.max_score*0.6)?'color:#25a244':'color:#e53e3e'">{{
                          sub.score
                        }}/{{ a.max_score }}</span><span class="badge badge-green" style="margin-left:6px">Graded</span>
                      </div>
                      <div style="display:flex;flex-direction:column;gap:4px">
                        <div style="display:flex;gap:6px"><input v-model.number="gradeInputs[sub.id]" type="number"
                                                                 :min="0" :max="a.max_score" class="grade-input"
                                                                 :placeholder="`0–${a.max_score}`"/>
                          <button class="btn btn-primary btn-sm" @click="handleGrade(sub.id,a.id,a.max_score)">
                            {{ sub.is_graded ? 'Update' : 'Grade' }}
                          </button>
                        </div>
                        <textarea v-model="feedbackInputs[sub.id]" class="form-control" rows="2"
                                  placeholder="Feedback (optional)…" style="font-size:12px;resize:vertical"/>
                      </div>
                    </td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ── GRADING TAB ── -->
    <div v-if="activeTab==='grading'">
      <div class="section-header">
        <div class="section-title">
          Grading
          <span v-if="pendingGradingCount" class="badge badge-red" style="margin-left:10px">{{ pendingGradingCount }} pending</span>
        </div>
        <button class="btn btn-ghost btn-sm" @click="loadGradingTab">↻ Refresh</button>
      </div>

      <div v-if="gradingLoading" class="text-muted text-sm" style="padding:32px;text-align:center">
        <div class="spinner" style="margin:0 auto 12px"/>
        Loading…
      </div>

      <template v-else>
        <!-- Final grade summary table -->
        <div class="lf-card" style="margin-bottom:24px" v-if="exStore.allFinalGrades">
          <div class="analytics-card-title" style="margin-bottom:14px">
            Final Grades
            <span class="text-muted text-sm" style="font-weight:400;margin-left:8px;font-size:13px">
              Exam {{ exStore.allFinalGrades.exam_weight }}% + Assignments {{
                exStore.allFinalGrades.assignment_weight
              }}%
              · Passing: {{ exStore.allFinalGrades.passing_score }}%
            </span>
          </div>
          <table class="lf-table">
            <thead>
            <tr>
              <th>#</th>
              <th>Student</th>
              <th>Exam Score</th>
              <th>Assignment Avg</th>
              <th>Final Grade</th>
              <th>Status</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="(s,i) in exStore.allFinalGrades.students" :key="s.student_id">
              <td class="text-muted text-sm">{{ i + 1 }}</td>
              <td><strong>{{ s.student_name }}</strong><br><span class="text-muted text-sm">{{ s.student_email }}</span>
              </td>
              <td>{{ s.exam_score !== null ? s.exam_score + '%' : '—' }}</td>
              <td>
                {{ s.assignment_avg !== null ? s.assignment_avg + '%' : '—' }}
                <div class="text-muted text-sm">{{ s.graded_submissions }}/{{ s.total_assignments }} graded</div>
              </td>
              <td>
                  <span class="display" style="font-size:22px"
                        :style="s.final_grade>=exStore.allFinalGrades.passing_score?'color:#25a244':'color:#e53e3e'">
                    {{ s.final_grade !== null ? s.final_grade + '%' : '—' }}
                  </span>
              </td>
              <td>
                <span v-if="s.passed===true" class="badge badge-green">✓ Passed</span>
                <span v-else-if="s.passed===false" class="badge badge-red">✗ Failed</span>
                <span v-else class="badge badge-gray">Incomplete</span>
              </td>
            </tr>
            </tbody>
          </table>
        </div>

        <!-- Open question responses to grade -->
        <div v-if="exStore.exam">
          <div class="section-title" style="margin-bottom:16px">Open Question Responses — Pending Review</div>

          <div v-if="!pendingOpenResponses.length" class="lf-card" style="padding:32px;text-align:center">
            <div style="font-size:40px;margin-bottom:10px">✅</div>
            <p class="text-muted text-sm">All open-answer questions have been graded.</p>
          </div>

          <div v-for="resp in pendingOpenResponses" :key="resp.id" class="open-response-card">
            <div class="open-response-header">
              <div class="qa-avatar">{{ resp.student_name?.charAt(0).toUpperCase() }}</div>
              <div style="flex:1">
                <div style="font-size:14px;font-weight:600">{{ resp.student_name }}</div>
                <div class="text-muted text-sm">{{ resp.exam_title }} · Q{{ resp.question_index + 1 }} ·
                  {{ resp.max_points.toFixed(1) }} pts max
                </div>
              </div>
              <span class="badge badge-orange">Pending</span>
            </div>

            <div class="open-response-question">{{ resp.question_text }}</div>
            <div class="open-response-answer">
              <div class="text-muted text-sm" style="margin-bottom:4px;font-weight:600">Student's answer:</div>
              <div class="open-response-text">{{ resp.text_answer || '(No answer provided)' }}</div>
            </div>

            <div class="open-response-grade-row">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <input
                    v-model.number="openGradeInputs[resp.id]"
                    type="number" :min="0" :max="resp.max_points"
                    class="grade-input"
                    :placeholder="`0–${resp.max_points.toFixed(1)}`"
                />
                <span class="text-muted text-sm">/ {{ resp.max_points.toFixed(1) }} pts</span>
              </div>
              <textarea
                  v-model="openFeedbackInputs[resp.id]"
                  class="form-control"
                  rows="2"
                  placeholder="Feedback for student (optional)…"
                  style="font-size:13px;resize:vertical;flex:1;min-width:200px"
              />
              <button
                  class="btn btn-primary btn-sm"
                  :disabled="openGradeInputs[resp.id]===undefined||openGradeInputs[resp.id]===null||openGradeInputs[resp.id]===''"
                  @click="handleGradeResponse(resp)"
              >
                ✓ Save Grade
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
    <!-- end grading tab -->

    <!-- ── STUDENTS TAB ── -->
    <div v-if="activeTab==='students'">
      <div class="section-header">
        <div class="section-title">
          Students
          <span class="text-muted text-sm" style="font-weight:400;margin-left:8px">{{ studentsCount }} enrolled</span>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <input
              v-model="studentsSearch"
              class="form-control"
              style="width:220px;padding:7px 12px;font-size:13px"
              placeholder="Search by name or email…"
          />
          <button class="btn btn-ghost btn-sm" @click="loadStudentsTab">↻ Refresh</button>
        </div>
      </div>

      <div v-if="studentsLoading" class="text-muted text-sm" style="padding:40px;text-align:center">
        <div class="spinner" style="margin:0 auto 12px"/>
        Loading…
      </div>

      <div v-else-if="!exStore.allFinalGrades?.students?.length" class="lf-card" style="padding:40px;text-align:center">
        <div style="font-size:40px;margin-bottom:10px">👥</div>
        <p class="text-muted text-sm">No students enrolled yet.</p>
      </div>

      <template v-else>
        <!-- Summary KPIs -->
        <div class="stats-grid" style="margin-bottom:20px">
          <div class="stat-card accent">
            <div class="stat-label">Enrolled</div>
            <div class="stat-value">{{ studentsCount }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Passed</div>
            <div class="stat-value" style="color:#25a244">{{ passedCount }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Failed</div>
            <div class="stat-value" style="color:#e53e3e">{{ failedCount }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Avg Grade</div>
            <div class="stat-value">{{ avgFinalGrade !== null ? avgFinalGrade + '%' : '—' }}</div>
          </div>
        </div>

        <!-- Students table -->
        <div class="lf-card" style="padding:0;overflow:hidden">
          <table class="lf-table">
            <thead>
            <tr>
              <th>#</th>
              <th>Student</th>
              <th>Type</th>
              <th>Exam Score</th>
              <th>Assignment Avg</th>
              <th>Final Grade</th>
              <th>Status</th>
              <th></th>
            </tr>
            </thead>
            <tbody>
            <tr
                v-for="(s, i) in filteredStudents"
                :key="s.student_id"
                class="student-row"
                @click="openStudentDrawer(s)"
            >
              <td class="text-muted text-sm">{{ i + 1 }}</td>
              <td>
                <div style="display:flex;align-items:center;gap:10px">
                  <div class="qa-avatar" style="width:30px;height:30px;font-size:12px">
                    {{ s.student_name?.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <div style="font-weight:600;font-size:14px">{{ s.student_name }}</div>
                    <div class="text-muted text-sm">{{ s.student_email }}</div>
                  </div>
                </div>
              </td>
              <td>
                  <span class="badge badge-gray" style="font-size:10px">
                    {{ s.student_type === 'online' ? '💻 Online' : '🏫 On-site' }}
                  </span>
              </td>
              <td>
                  <span v-if="s.exam_score !== null" class="display" style="font-size:18px"
                        :style="s.exam_score>=exStore.allFinalGrades.passing_score?'color:#25a244':'color:#e53e3e'">
                    {{ s.exam_score }}%
                  </span>
                <span v-else class="text-muted text-sm">—</span>
              </td>
              <td>
                <span v-if="s.assignment_avg !== null" class="text-sm">{{ s.assignment_avg }}%</span>
                <span v-else class="text-muted text-sm">—</span>
                <div class="text-muted text-sm">{{ s.graded_submissions }}/{{ s.total_assignments }}</div>
              </td>
              <td>
                  <span
                      v-if="s.final_grade !== null"
                      class="display"
                      style="font-size:22px"
                      :style="s.passed?'color:#25a244':'color:#e53e3e'"
                  >{{ s.final_grade }}%</span>
                <span v-else class="text-muted text-sm">—</span>
              </td>
              <td>
                <span v-if="s.passed === true" class="badge badge-green">✓ Passed</span>
                <span v-else-if="s.passed === false" class="badge badge-red">✗ Failed</span>
                <span v-else class="badge badge-gray">Incomplete</span>
              </td>
              <td>
                <button class="btn btn-ghost btn-sm" @click.stop="openStudentDrawer(s)">Details →</button>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
    <!-- end Students tab -->

  </div>
  <!-- end page-content -->

  <!--
    Student Grade Drawer — position:fixed overlay, no Teleport needed.
    Vue 3 supports multiple fragment root nodes so these sit as
    plain siblings of page-content without any wrapper.
  -->
  <div v-if="drawerStudent" class="drawer-backdrop" @click="drawerStudent=null"/>
  <div class="student-drawer" :class="{open: !!drawerStudent}">
    <template v-if="drawerStudent">
      <div class="drawer-header">
        <div class="qa-avatar" style="width:44px;height:44px;font-size:18px;flex-shrink:0">
          {{ drawerStudent.student_name?.charAt(0).toUpperCase() }}
        </div>
        <div style="flex:1">
          <div class="display" style="font-size:22px">{{ drawerStudent.student_name }}</div>
          <div class="text-muted text-sm">{{ drawerStudent.student_email }}</div>
        </div>
        <button class="btn btn-ghost btn-sm" @click="drawerStudent=null">✕ Close</button>
      </div>

      <!-- Final grade hero -->
      <div class="drawer-grade-hero" :class="drawerStudent.passed?'passed':'failed'">
        <div class="text-muted text-sm"
             style="margin-bottom:4px;text-transform:uppercase;letter-spacing:.6px;font-size:11px;font-weight:700">Final
          Grade
        </div>
        <div class="display" style="font-size:54px">
          {{ drawerStudent.final_grade !== null ? drawerStudent.final_grade + '%' : '—' }}
        </div>
        <div style="margin-top:6px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
          <span v-if="drawerStudent.passed===true" class="badge badge-green">✓ Passed</span>
          <span v-else-if="drawerStudent.passed===false" class="badge badge-red">✗ Failed</span>
          <span v-else class="badge badge-gray">Incomplete</span>
          <span class="badge badge-gray" style="font-size:11px">Passing: {{
              exStore.allFinalGrades?.passing_score
            }}%</span>
        </div>
      </div>

      <!-- Formula breakdown -->
      <div class="drawer-formula">
        <div class="drawer-formula-item">
          <div class="drawer-formula-label">Exam ({{ exStore.allFinalGrades?.exam_weight }}%)</div>
          <div class="drawer-formula-val display"
               :style="drawerStudent.exam_score!==null?(drawerStudent.exam_score>=exStore.allFinalGrades?.passing_score?'color:#25a244':'color:#e53e3e'):''">
            {{ drawerStudent.exam_score !== null ? drawerStudent.exam_score + '%' : 'Not taken' }}
          </div>
        </div>
        <div class="drawer-formula-op">+</div>
        <div class="drawer-formula-item">
          <div class="drawer-formula-label">Assignments ({{ exStore.allFinalGrades?.assignment_weight }}%)</div>
          <div class="drawer-formula-val display">
            {{ drawerStudent.assignment_avg !== null ? drawerStudent.assignment_avg + '%' : 'No grades yet' }}
          </div>
          <div class="text-muted text-sm">{{ drawerStudent.graded_submissions }}/{{ drawerStudent.total_assignments }}
            graded
          </div>
        </div>
      </div>

      <!-- Exam attempts (loaded lazily) -->
      <div class="drawer-section">
        <div style="font-size:15px;font-weight:700;margin-bottom:12px">Exam Attempts</div>
        <div v-if="drawerExamLoading" class="text-muted text-sm">Loading…</div>
        <div v-else-if="!drawerExamAttempts.length" class="text-muted text-sm">No attempts yet.</div>
        <table v-else class="lf-table">
          <thead>
          <tr>
            <th>#</th>
            <th>Score</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(a, i) in drawerExamAttempts" :key="a.id">
            <td class="text-muted text-sm">{{ i + 1 }}</td>
            <td>
                <span class="display" style="font-size:18px"
                      :style="a.score>=exStore.allFinalGrades?.passing_score?'color:#25a244':'color:#e53e3e'">
                  {{ a.score !== null ? a.score + '%' : '—' }}
                </span>
            </td>
            <td>
              <span v-if="a.passed===true" class="badge badge-green">✓ Passed</span>
              <span v-else-if="a.passed===false" class="badge badge-red">✗ Failed</span>
              <span v-if="a.auto_submitted" class="badge badge-orange" style="font-size:10px">Auto-submitted</span>
            </td>
            <td class="text-muted text-sm">{{ formatDate(a.submitted_at) }}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>

  <!-- ── Modals ── -->
  <BaseModal v-model="showAddLesson" :title="editLesson?'Edit Lesson':'Add Lesson'" width="600px">
    <FormGroup label="Title"><input v-model="lessonForm.title" class="form-control" placeholder="Lesson title"/>
    </FormGroup>
    <FormGroup label="Type"><select v-model="lessonForm.type" class="form-control">
      <option value="text">📄 Text</option>
      <option value="video">🎬 Video</option>
    </select></FormGroup>
    <template v-if="lessonForm.type==='video'">
      <FormGroup label="Video Source">
        <div style="display:flex;border:2px solid var(--lf-gray-200);border-radius:var(--lf-radius);overflow:hidden">
          <button type="button" :style="lessonForm.videoSource==='upload'?activeSourceStyle:inactiveSourceStyle"
                  @click="lessonForm.videoSource='upload'">⬆ Upload File
          </button>
          <button type="button"
                  :style="lessonForm.videoSource==='youtube'?activeSourceStyle+';border-left:2px solid var(--lf-gray-200)':inactiveSourceStyle+';border-left:2px solid var(--lf-gray-200)'"
                  @click="lessonForm.videoSource='youtube'">▶ YouTube URL
          </button>
        </div>
      </FormGroup>
      <FormGroup v-if="lessonForm.videoSource==='upload'" label="Video File">
        <div class="drop-zone" :class="{'drop-active':isDragging}" @dragover.prevent="isDragging=true"
             @dragleave="isDragging=false" @drop.prevent="onFileDrop" @click="$refs.fileInput.click()">
          <input ref="fileInput" type="file" accept="video/*" style="display:none" @change="onFileSelect"/>
          <template v-if="!lessonForm.video_file">
            <div style="font-size:32px;margin-bottom:8px">🎬</div>
            <div style="font-weight:600;font-size:14px">Click or drag &amp; drop</div>
          </template>
          <template v-else>
            <div style="font-size:28px;margin-bottom:6px">✅</div>
            <div style="font-weight:600;font-size:14px">{{ lessonForm.video_file.name }}</div>
            <button type="button" class="btn btn-ghost btn-sm" style="margin-top:10px"
                    @click.stop="lessonForm.video_file=null">✕ Remove
            </button>
          </template>
        </div>
      </FormGroup>
      <FormGroup v-if="lessonForm.videoSource==='youtube'" label="YouTube Embed URL"><input
          v-model="lessonForm.video_url" class="form-control" placeholder="https://www.youtube.com/embed/VIDEO_ID"/>
      </FormGroup>
    </template>
    <FormGroup label="Content"><textarea v-model="lessonForm.content" class="form-control" rows="4"/></FormGroup>
    <div v-if="editLesson" class="attachments-section">
      <div class="attachments-header"><span
          style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--lf-gray-600)">📎 Attachments</span><label
          class="attach-upload-btn"><input type="file" multiple style="display:none" @change="handleAttachFiles"/>+ Add
        Files</label></div>
      <div v-if="editLesson.attachments?.length" class="attach-list">
        <div v-for="a in editLesson.attachments" :key="a.id" class="attach-item">
          <span class="attach-icon">{{ fileIcon(a.extension) }}</span>
          <div class="attach-info">
            <div class="attach-name">{{ a.name }}</div>
            <div class="attach-size text-muted text-sm">{{ formatBytes(a.file_size) }}</div>
          </div>
          <a :href="a.stream_url" target="_blank" class="btn btn-ghost btn-sm" style="text-decoration:none">↗</a>
          <button class="btn btn-danger btn-sm" @click="handleDeleteAttachment(a.id)">✕</button>
        </div>
      </div>
    </div>
    <template #footer>
      <button class="btn btn-ghost" @click="closeAddLesson">Cancel</button>
      <button class="btn btn-primary" :disabled="saving" @click="handleSaveLesson">
        {{ saving ? 'Saving…' : editLesson ? 'Save Changes' : 'Add Lesson' }}
      </button>
    </template>
  </BaseModal>

  <BaseModal v-model="showAddSession" title="Create Attendance Session">
    <FormGroup label="Label"><input v-model="sessionForm.label" class="form-control" placeholder="Week 3 — Monday"/>
    </FormGroup>
    <FormGroup label="Date"><input v-model="sessionForm.date" type="date" class="form-control"/></FormGroup>
    <template #footer>
      <button class="btn btn-ghost" @click="showAddSession=false">Cancel</button>
      <button class="btn btn-primary" @click="handleCreateSession">Create &amp; Get Code</button>
    </template>
  </BaseModal>

  <BaseModal v-model="showAddNotice" :title="editNotice?'Edit Announcement':'New Announcement'">
    <FormGroup label="Title"><input v-model="noticeForm.title" class="form-control"/></FormGroup>
    <FormGroup label="Message"><textarea v-model="noticeForm.body" class="form-control" rows="5"/></FormGroup>
    <div style="display:flex;align-items:center;gap:8px;margin-top:4px"><input type="checkbox" id="pin-check"
                                                                               v-model="noticeForm.pinned"/><label
        for="pin-check" style="font-size:14px;cursor:pointer">📌 Pin this</label></div>
    <template #footer>
      <button class="btn btn-ghost" @click="showAddNotice=false">Cancel</button>
      <button class="btn btn-primary" @click="handleSaveNotice">{{ editNotice ? 'Save' : 'Post' }}</button>
    </template>
  </BaseModal>

  <BaseModal v-model="showCode" title="Session Created">
    <div class="code-box">
      <div class="code-label">Attendance Code</div>
      <div class="code-val">{{ newSessionCode }}</div>
    </div>
    <template #footer>
      <button class="btn btn-primary" @click="showCode=false">Done</button>
    </template>
  </BaseModal>

  <BaseModal v-model="showAddAssignment" :title="editAssignment?'Edit Assignment':'New Assignment'">
    <FormGroup label="Lesson"><select v-model="assignmentForm.lesson" class="form-control">
      <option v-for="l in course?.lessons" :key="l.id" :value="l.id">{{ l.title }}</option>
    </select></FormGroup>
    <FormGroup label="Title"><input v-model="assignmentForm.title" class="form-control"/></FormGroup>
    <FormGroup label="Description"><textarea v-model="assignmentForm.description" class="form-control" rows="4"/>
    </FormGroup>
    <FormGroup label="Max Score"><input v-model.number="assignmentForm.max_score" type="number" min="1"
                                        class="form-control"/></FormGroup>
    <FormGroup label="Due Date (optional)"><input v-model="assignmentForm.due_date" type="datetime-local"
                                                  class="form-control"/></FormGroup>
    <template #footer>
      <button class="btn btn-ghost" @click="showAddAssignment=false">Cancel</button>
      <button class="btn btn-primary" :disabled="savingAssignment" @click="handleSaveAssignment">
        {{ savingAssignment ? 'Saving…' : editAssignment ? 'Save' : 'Create' }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import {ref, reactive, computed, onMounted, onUnmounted, watch, nextTick} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useToast} from 'primevue/usetoast'
import BaseModal from '@/components/ui/BaseModal.vue'
import FormGroup from '@/components/ui/FormGroup.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import {useCoursesStore} from '@/stores/courses'
import {useAttendanceStore} from '@/stores/attendance'
import {useAnnouncementsStore} from '@/stores/announcements'
import {useExamsStore} from '@/stores/exams'
import {useQaStore} from '@/stores/qa'
import {useAssignmentsStore} from '@/stores/assignments'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const courses = useCoursesStore()
const attStore = useAttendanceStore()
const annStore = useAnnouncementsStore()
const exStore = useExamsStore()
const qaStore = useQaStore()
const assignmentsStore = useAssignmentsStore()

const course = computed(() => courses.current)
const sessions = computed(() => attStore.sessions)
const announcements = computed(() => annStore.announcements)
const publishedLessonCount = computed(() => course.value?.lessons?.filter(l => l.status === 'published').length ?? 0)

// ── Style helpers ──────────────────────────────────────────────────────────────
const activeSourceStyle = 'flex:1;padding:9px;font-size:13px;font-weight:600;background:var(--lf-black);color:#fff;border:none;cursor:pointer'
const inactiveSourceStyle = 'flex:1;padding:9px;font-size:13px;font-weight:600;background:transparent;color:var(--lf-gray-600);border:none;cursor:pointer'

// ── Tabs ────────────────────────────────────────────────────────────────────
const activeTab = ref('lessons')
const tabs = [
  {key: 'lessons', label: 'Lessons'},
  {key: 'exam', label: 'Exam Builder'},
  {key: 'sessions', label: 'Sessions'},
  {key: 'announcements', label: 'Announcements'},
  {key: 'qa', label: 'Q&A Inbox'},
  {key: 'analytics', label: '📊 Analytics'},
  {key: 'assignments', label: '📋 Assignments'},
  {key: 'grading', label: '📝 Grading'},
  {key: 'students', label: '👥 Students'},
]

watch(activeTab, tab => {
  if (tab === 'qa') qaStore.fetchCourseQuestions(route.params.id)
  if (tab === 'analytics') loadAnalytics()
  if (tab === 'assignments') assignmentsStore.fetchByCourse(route.params.id)
  if (tab === 'grading') loadGradingTab()
  if (tab === 'students') loadStudentsTab()
})

// ── Course/Lesson publish ──────────────────────────────────────────────────────
const togglingCourse = ref(false), togglingLesson = ref(null)

async function handleToggleCourseStatus() {
  if (!course.value) return;
  togglingCourse.value = true
  try {
    if (course.value.status === 'published') {
      await courses.unpublishCourse(route.params.id);
      toast.add({severity: 'info', summary: 'Moved to draft', life: 4000})
    } else {
      await courses.publishCourse(route.params.id);
      toast.add({severity: 'success', summary: 'Course is now live', life: 4000})
    }
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000})
  } finally {
    togglingCourse.value = false
  }
}

async function handleToggleLessonStatus(lesson) {
  togglingLesson.value = lesson.id
  try {
    if (lesson.status === 'published') {
      await courses.unpublishLesson(route.params.id, lesson.id);
      toast.add({severity: 'info', summary: `"${lesson.title}" is now draft`, life: 3000})
    } else {
      await courses.publishLesson(route.params.id, lesson.id);
      toast.add({severity: 'success', summary: `"${lesson.title}" is live`, life: 3000})
    }
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000})
  } finally {
    togglingLesson.value = null
  }
}

// ── Analytics ──────────────────────────────────────────────────────────────────
const analyticsData = ref(null), analyticsLoading = ref(false)
const scoreChartEl = ref(null), activityChartEl = ref(null)
let scoreChart = null, activityChart = null
const avgLessonCompletion = computed(() => {
  const items = analyticsData.value?.lesson_completion ?? [];
  return !items.length ? 0 : Math.round(items.reduce((s, l) => s + l.pct, 0) / items.length)
})

async function loadAnalytics() {
  analyticsLoading.value = true
  try {
    const {data} = await api.get(`/courses/${route.params.id}/analytics/`);
    analyticsData.value = data;
    await nextTick();
    renderCharts(data)
  } catch {
    toast.add({severity: 'error', summary: 'Failed to load analytics', life: 3000})
  } finally {
    analyticsLoading.value = false
  }
}

function destroyCharts() {
  if (scoreChart) {
    scoreChart.destroy();
    scoreChart = null
  }
  if (activityChart) {
    activityChart.destroy();
    activityChart = null
  }
}

async function renderCharts(data) {
  const {Chart, registerables} = await import('chart.js');
  Chart.register(...registerables)
  const ORANGE = '#FF6B00', ORANGE_LIGHT = 'rgba(255,107,0,0.15)', GREEN = '#25a244', GRAY = '#e8e8e8'
  const font = {family: "'DM Sans', sans-serif", size: 12}
  if (scoreChartEl.value && data.student_scores.length) {
    destroyCharts();
    const colors = data.score_distribution.map((_, i) => i >= 6 ? GREEN : i >= 5 ? ORANGE : '#e53e3e');
    scoreChart = new Chart(scoreChartEl.value, {
      type: 'bar',
      data: {
        labels: ['0-9%', '10-19%', '20-29%', '30-39%', '40-49%', '50-59%', '60-69%', '70-79%', '80-89%', '90-100%'],
        datasets: [{label: 'Students', data: data.score_distribution, backgroundColor: colors, borderRadius: 4}]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {legend: {display: false}},
        scales: {
          x: {grid: {display: false}, ticks: {font}},
          y: {grid: {color: GRAY}, ticks: {font, stepSize: 1}, beginAtZero: true}
        }
      }
    })
  }
  if (activityChartEl.value && data.attempts_over_time.length) {
    activityChart = new Chart(activityChartEl.value, {
      type: 'line',
      data: {
        labels: data.attempts_over_time.map(d => d.date),
        datasets: [{
          label: 'Attempts',
          data: data.attempts_over_time.map(d => d.count),
          borderColor: ORANGE,
          backgroundColor: ORANGE_LIGHT,
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: ORANGE,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {legend: {display: false}},
        scales: {
          x: {grid: {display: false}, ticks: {font}},
          y: {grid: {color: GRAY}, ticks: {font, stepSize: 1}, beginAtZero: true}
        }
      }
    })
  }
}

onUnmounted(() => destroyCharts())

// ── Grading tab ────────────────────────────────────────────────────────────────
const gradingLoading = ref(false)
const openGradeInputs = reactive({})
const openFeedbackInputs = reactive({})

const pendingOpenResponses = computed(() => {
  return (exStore.allAttempts ?? []).flatMap(a =>
      (a.responses ?? []).filter(r => r.question_type === 'open' && r.points_earned === null)
  )
})
const pendingGradingCount = computed(() => pendingOpenResponses.value.length)

async function loadGradingTab() {
  gradingLoading.value = true
  try {
    if (exStore.exam?.id) {
      await exStore.fetchAllAttempts(exStore.exam.id)
    }
    await exStore.fetchAllFinalGrades(route.params.id)
  } finally {
    gradingLoading.value = false
  }
}

async function handleGradeResponse(resp) {
  const pts = openGradeInputs[resp.id]
  if (pts === undefined || pts === null || pts === '') return
  if (pts < 0 || pts > resp.max_points) {
    toast.add({severity: 'warn', summary: `Points must be 0–${resp.max_points.toFixed(1)}`, life: 3000})
    return
  }
  try {
    await exStore.gradeResponse(resp.id, Number(pts), openFeedbackInputs[resp.id] ?? '')
    await exStore.fetchAllFinalGrades(route.params.id)
    toast.add({severity: 'success', summary: 'Grade saved', life: 2500})
  } catch {
    toast.add({severity: 'error', summary: 'Failed to save grade', life: 3000})
  }
}

// ── Exam builder ───────────────────────────────────────────────────────────────
const examDraft = reactive({
  title: '', questions: [], max_retakes: 0,
  time_limit_minutes: null, exam_weight: 70, assignment_weight: 30, passing_score: 60,
})
const weightsValid = computed(() => examDraft.exam_weight + examDraft.assignment_weight === 100)

function syncAssignmentWeight() {
  examDraft.assignment_weight = Math.max(0, 100 - (examDraft.exam_weight || 0))
}

function syncExamWeight() {
  examDraft.exam_weight = Math.max(0, 100 - (examDraft.assignment_weight || 0))
}

function addQuestion(type) {
  examDraft.questions.push(type === 'mcq' ? {
    type: 'mcq',
    text: '',
    options: ['', '', '', ''],
    correct_index: 0
  } : {type: 'open', text: ''})
}

function removeQuestion(qi) {
  examDraft.questions.splice(qi, 1)
}

async function saveExam() {
  if (!weightsValid.value) {
    toast.add({severity: 'warn', summary: 'Weights must sum to 100%', life: 3000});
    return
  }
  const payload = {
    title: examDraft.title,
    questions: examDraft.questions,
    max_retakes: examDraft.max_retakes,
    time_limit_minutes: examDraft.time_limit_minutes || null,
    exam_weight: examDraft.exam_weight,
    assignment_weight: examDraft.assignment_weight,
    passing_score: examDraft.passing_score
  }
  await exStore.saveExam(route.params.id, payload)
  toast.add({severity: 'success', summary: 'Exam saved', life: 3000})
}

// ── Assignments tab ────────────────────────────────────────────────────────────
const showAddAssignment = ref(false), editAssignment = ref(null), savingAssignment = ref(false)
const expandedAssignmentIds = ref(new Set()), submissionsLoading = reactive({})
const gradeInputs = reactive({}), feedbackInputs = reactive({})
const assignmentForm = reactive({lesson: '', title: '', description: '', max_score: 100, due_date: ''})
const lessonsWithAssignments = computed(() => {
  const all = assignmentsStore.getByCourse(route.params.id);
  const ids = new Set(all.map(a => a.lesson));
  return (course.value?.lessons ?? []).filter(l => ids.has(l.id))
})

function assignmentsByLesson(lid) {
  return assignmentsStore.getByCourse(route.params.id).filter(a => a.lesson === lid)
}

function openAddAssignment() {
  editAssignment.value = null;
  Object.assign(assignmentForm, {
    lesson: course.value?.lessons?.[0]?.id ?? '',
    title: '',
    description: '',
    max_score: 100,
    due_date: ''
  });
  showAddAssignment.value = true
}

function openEditAssignment(a) {
  editAssignment.value = a;
  Object.assign(assignmentForm, {
    lesson: a.lesson,
    title: a.title,
    description: a.description,
    max_score: a.max_score,
    due_date: a.due_date ? a.due_date.slice(0, 16) : ''
  });
  showAddAssignment.value = true
}

async function handleSaveAssignment() {
  if (!assignmentForm.title.trim() || !assignmentForm.lesson) {
    toast.add({severity: 'warn', summary: 'Title and lesson required', life: 3000});
    return
  }
  savingAssignment.value = true;
  const p = {
    lesson: assignmentForm.lesson,
    title: assignmentForm.title,
    description: assignmentForm.description,
    max_score: assignmentForm.max_score,
    due_date: assignmentForm.due_date || null
  };
  try {
    if (editAssignment.value) {
      await assignmentsStore.updateAssignment(route.params.id, editAssignment.value.id, p);
      toast.add({severity: 'success', summary: 'Assignment updated', life: 3000})
    } else {
      await assignmentsStore.createAssignment(route.params.id, p);
      toast.add({severity: 'success', summary: 'Assignment created', life: 3000})
    }
    ;showAddAssignment.value = false
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000})
  } finally {
    savingAssignment.value = false
  }
}

async function handleDeleteAssignment(id) {
  if (!confirm('Delete this assignment?')) return;
  await assignmentsStore.deleteAssignment(route.params.id, id);
  expandedAssignmentIds.value.delete(id);
  toast.add({severity: 'info', summary: 'Deleted', life: 3000})
}

async function toggleAssignmentExpand(id) {
  const n = new Set(expandedAssignmentIds.value);
  if (n.has(id)) {
    n.delete(id)
  } else {
    n.add(id);
    await loadSubmissions(id)
  }
  ;expandedAssignmentIds.value = n
}

async function loadSubmissions(aid) {
  submissionsLoading[aid] = true;
  try {
    const subs = await assignmentsStore.fetchSubmissions(aid);
    subs.forEach(s => {
      if (gradeInputs[s.id] === undefined) gradeInputs[s.id] = s.score ?? '';
      if (feedbackInputs[s.id] === undefined) feedbackInputs[s.id] = s.feedback ?? ''
    })
  } finally {
    submissionsLoading[aid] = false
  }
}

async function handleGrade(submissionId, assignmentId, maxScore) {
  const score = gradeInputs[submissionId];
  if (score === '' || score === null || score === undefined) {
    toast.add({severity: 'warn', summary: 'Enter a score', life: 3000});
    return
  }
  if (score < 0 || score > maxScore) {
    toast.add({severity: 'warn', summary: `Score must be 0–${maxScore}`, life: 3000});
    return
  }
  try {
    await assignmentsStore.grade(submissionId, Number(score), feedbackInputs[submissionId] ?? '');
    await loadSubmissions(assignmentId);
    toast.add({severity: 'success', summary: 'Grade saved', life: 2500})
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000})
  }
}

// ── Q&A ────────────────────────────────────────────────────────────────────────
const qaFilters = [{key: 'all', label: 'All'}, {key: 'unresolved', label: 'Unresolved'}, {
  key: 'resolved',
  label: 'Resolved'
}]
const qaFilter = ref('unresolved'), qaReplyText = reactive({}), expandedQaIds = ref(new Set())
const filteredQaQuestions = computed(() => {
  const qs = qaStore.questions;
  if (qaFilter.value === 'unresolved') return qs.filter(q => !q.is_resolved);
  if (qaFilter.value === 'resolved') return qs.filter(q => q.is_resolved);
  return qs
})
const unresolvedQaCount = computed(() => qaStore.questions.filter(q => !q.is_resolved).length)

function qaFilterCount(key) {
  if (key === 'all') return qaStore.questions.length;
  if (key === 'unresolved') return qaStore.questions.filter(q => !q.is_resolved).length;
  return qaStore.questions.filter(q => q.is_resolved).length
}

function toggleQaExpand(id) {
  const n = new Set(expandedQaIds.value);
  n.has(id) ? n.delete(id) : n.add(id);
  expandedQaIds.value = n
}

async function handleQaPostAnswer(question) {
  const text = qaReplyText[question.id]?.trim();
  if (!text) return;
  try {
    await qaStore.postAnswer(route.params.id, question.lesson, question.id, text);
    qaReplyText[question.id] = '';
    if (!question.is_resolved) await qaStore.resolveQuestion(route.params.id, question.lesson, question.id, true);
    toast.add({severity: 'success', summary: 'Answer posted', life: 2500})
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000})
  }
}

async function handleQaToggleResolve(question) {
  try {
    await qaStore.resolveQuestion(route.params.id, question.lesson, question.id, !question.is_resolved)
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000})
  }
}

async function handleQaDeleteAnswer(question, answerId) {
  if (!confirm('Delete this answer?')) return;
  await qaStore.deleteAnswer(route.params.id, question.lesson, question.id, answerId)
}

// ── Drag reorder ───────────────────────────────────────────────────────────────
const localLessons = ref([]), draggingId = ref(null), dragOverId = ref(null), reordering = ref(false)
const orderChanged = computed(() => {
  if (!course.value?.lessons) return false;
  return localLessons.value.some((l, i) => l.id !== course.value.lessons[i]?.id)
})
watch(() => course.value?.lessons, (ls) => {
  if (ls) localLessons.value = [...ls]
}, {immediate: true})

function onDragStart(e, id) {
  draggingId.value = id;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', id)
}

function onDragOver(e, id) {
  if (draggingId.value === id) return;
  dragOverId.value = id;
  const from = localLessons.value.findIndex(l => l.id === draggingId.value),
      to = localLessons.value.findIndex(l => l.id === id);
  if (from === -1 || to === -1) return;
  const arr = [...localLessons.value];
  const [m] = arr.splice(from, 1);
  arr.splice(to, 0, m);
  localLessons.value = arr
}

function onDragLeave() {
  dragOverId.value = null
}

function onDrop() {
  dragOverId.value = null
}

function onDragEnd() {
  draggingId.value = null;
  dragOverId.value = null
}

async function saveOrder() {
  reordering.value = true;
  try {
    await courses.reorderLessons(route.params.id, localLessons.value.map(l => l.id));
    toast.add({severity: 'success', summary: 'Order saved', life: 2000})
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 3000});
    localLessons.value = [...(course.value?.lessons ?? [])]
  } finally {
    reordering.value = false
  }
}

// ── Lesson form ────────────────────────────────────────────────────────────────
const showAddLesson = ref(false), editLesson = ref(null), saving = ref(false), isDragging = ref(false),
    fileInput = ref(null)
const lessonForm = reactive({
  title: '',
  type: 'text',
  content: '',
  video_url: '',
  videoSource: 'upload',
  video_file: null
})

function resetLessonForm() {
  Object.assign(lessonForm, {
    title: '',
    type: 'text',
    content: '',
    video_url: '',
    videoSource: 'upload',
    video_file: null
  })
}

function closeAddLesson() {
  showAddLesson.value = false;
  editLesson.value = null;
  resetLessonForm()
}

function openEditLesson(l) {
  editLesson.value = l;
  Object.assign(lessonForm, {
    title: l.title,
    type: l.type,
    content: l.content ?? '',
    video_url: l.video_url ?? '',
    videoSource: l.hls_path ? 'upload' : (l.video_url ? 'youtube' : 'upload'),
    video_file: null
  });
  showAddLesson.value = true
}

function onFileSelect(e) {
  const f = e.target.files?.[0];
  if (f) lessonForm.video_file = f
}

function onFileDrop(e) {
  isDragging.value = false;
  const f = e.dataTransfer.files?.[0];
  if (f && f.type.startsWith('video/')) lessonForm.video_file = f; else toast.add({
    severity: 'warn',
    summary: 'Drop a video file',
    life: 3000
  })
}

async function handleSaveLesson() {
  if (!lessonForm.title.trim()) {
    toast.add({severity: 'warn', summary: 'Title required', life: 3000});
    return
  }
  saving.value = true;
  const id = route.params.id;
  const payload = {
    title: lessonForm.title,
    type: lessonForm.type,
    content: lessonForm.content,
    video_url: lessonForm.videoSource === 'youtube' ? lessonForm.video_url : ''
  };
  if (lessonForm.type === 'video' && lessonForm.videoSource === 'upload' && lessonForm.video_file) payload.video_file = lessonForm.video_file;
  try {
    if (editLesson.value) {
      await courses.updateLesson(id, editLesson.value.id, payload);
      toast.add({severity: 'success', summary: 'Lesson updated', life: 3000})
    } else {
      await courses.createLesson(id, payload);
      toast.add({severity: 'success', summary: 'Lesson added', life: 3000})
    }
    ;closeAddLesson()
  } catch {
    toast.add({severity: 'error', summary: 'Failed', life: 4000})
  } finally {
    saving.value = false
  }
}

async function handleDeleteLesson(lessonId) {
  if (!confirm('Delete this lesson?')) return;
  await courses.deleteLesson(route.params.id, lessonId);
  toast.add({severity: 'info', summary: 'Deleted', life: 3000})
}

// ── Attachments ────────────────────────────────────────────────────────────────
const ATTACHMENT_ICONS = {
  pdf: '📄',
  doc: '📝',
  docx: '📝',
  ppt: '📊',
  pptx: '📊',
  xls: '📈',
  xlsx: '📈',
  zip: '🗜️',
  txt: '📃',
  csv: '📋',
  mp3: '🎵',
  png: '🖼️',
  jpg: '🖼️',
  jpeg: '🖼️'
}

function fileIcon(ext) {
  return ATTACHMENT_ICONS[ext?.toLowerCase()] ?? '📎'
}

function formatBytes(b) {
  if (!b) return '—';
  if (b >= 1073741824) return (b / 1073741824).toFixed(1) + ' GB';
  if (b >= 1048576) return (b / 1048576).toFixed(1) + ' MB';
  if (b >= 1024) return (b / 1024).toFixed(0) + ' KB';
  return b + ' B'
}

const attachUploading = ref(false)

async function handleAttachFiles(e) {
  const files = Array.from(e.target.files ?? []);
  if (!files.length || !editLesson.value) return;
  attachUploading.value = true;
  try {
    for (const f of files) await courses.uploadAttachment(route.params.id, editLesson.value.id, f, f.name);
    editLesson.value = courses.current?.lessons?.find(l => l.id === editLesson.value.id) ?? editLesson.value;
    toast.add({severity: 'success', summary: `${files.length} file(s) uploaded`, life: 3000})
  } catch {
    toast.add({severity: 'error', summary: 'Upload failed', life: 3000})
  } finally {
    attachUploading.value = false;
    e.target.value = ''
  }
}

async function handleDeleteAttachment(attachmentId) {
  if (!editLesson.value) return;
  await courses.deleteAttachment(route.params.id, editLesson.value.id, attachmentId);
  editLesson.value = courses.current?.lessons?.find(l => l.id === editLesson.value.id) ?? editLesson.value
}

// ── Sessions ───────────────────────────────────────────────────────────────────
const showAddSession = ref(false), showCode = ref(false), newSessionCode = ref('')
const sessionForm = reactive({label: '', date: new Date().toISOString().split('T')[0]})

async function handleCreateSession() {
  const s = await attStore.createSession({course: route.params.id, ...sessionForm});
  newSessionCode.value = s.code;
  showAddSession.value = false;
  showCode.value = true;
  Object.assign(sessionForm, {label: '', date: new Date().toISOString().split('T')[0]})
}

async function handleDeleteSession(id) {
  if (!confirm('Delete session?')) return;
  await attStore.deleteSession(id)
}

// ── Announcements ──────────────────────────────────────────────────────────────
const showAddNotice = ref(false), editNotice = ref(null)
const noticeForm = reactive({title: '', body: '', pinned: false})

function openEditNotice(n) {
  editNotice.value = n;
  Object.assign(noticeForm, {title: n.title, body: n.body, pinned: n.pinned});
  showAddNotice.value = true
}

async function handleSaveNotice() {
  if (editNotice.value) await annStore.updateAnnouncement(editNotice.value.id, {...noticeForm}); else await annStore.createAnnouncement({course: route.params.id, ...noticeForm});
  showAddNotice.value = false;
  editNotice.value = null;
  Object.assign(noticeForm, {title: '', body: '', pinned: false})
}

async function handleDeleteNotice(id) {
  if (!confirm('Delete?')) return;
  await annStore.deleteAnnouncement(id)
}

async function togglePin(n) {
  await annStore.updateAnnouncement(n.id, {pinned: !n.pinned})
}

// ── Misc ───────────────────────────────────────────────────────────────────────
async function handleDelete() {
  if (!confirm('Delete this course?')) return;
  await courses.deleteCourse(route.params.id);
  router.push('/courses')
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-GB', {day: '2-digit', month: 'short', year: 'numeric'})
}

function formatDateTime(d) {
  return new Date(d).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ── Students tab ──────────────────────────────────────────────────────────────

const studentsLoading = ref(false)
const studentsSearch = ref('')
const drawerStudent = ref(null)
const drawerExamAttempts = ref([])
const drawerExamLoading = ref(false)

const studentsCount = computed(() => exStore.allFinalGrades?.students?.length ?? 0)
const passedCount = computed(() => (exStore.allFinalGrades?.students ?? []).filter(s => s.passed === true).length)
const failedCount = computed(() => (exStore.allFinalGrades?.students ?? []).filter(s => s.passed === false).length)
const avgFinalGrade = computed(() => {
  const list = (exStore.allFinalGrades?.students ?? []).filter(s => s.final_grade !== null)
  if (!list.length) return null
  return Math.round(list.reduce((sum, s) => sum + s.final_grade, 0) / list.length * 10) / 10
})
const filteredStudents = computed(() => {
  const q = studentsSearch.value.trim().toLowerCase()
  const all = exStore.allFinalGrades?.students ?? []
  if (!q) return all
  return all.filter(s =>
      s.student_name?.toLowerCase().includes(q) ||
      s.student_email?.toLowerCase().includes(q)
  )
})

async function loadStudentsTab() {
  studentsLoading.value = true
  try {
    await exStore.fetchAllFinalGrades(route.params.id)
  } finally {
    studentsLoading.value = false
  }
}

async function openStudentDrawer(student) {
  drawerStudent.value = student
  drawerExamAttempts.value = []

  if (!exStore.exam?.id) await exStore.fetchExamByCourse(route.params.id)

  if (exStore.exam?.id) {
    drawerExamLoading.value = true
    try {
      if (!exStore.allAttempts.length) await exStore.fetchAllAttempts(exStore.exam.id)
      // Match by student_id (UUID stored on attempt.student field)
      drawerExamAttempts.value = exStore.allAttempts.filter(a =>
          String(a.student) === student.student_id ||
          a.student_name === student.student_name
      )
    } finally {
      drawerExamLoading.value = false
    }
  }
}

onMounted(async () => {
  const id = router.params.id
  console.log(id)
  await courses.fetchCourse(id)
  await Promise.all([
    attStore.fetchSessions(id),
    annStore.fetchAnnouncements(id),
    exStore.fetchExamByCourse(id).then(exam => {
      if (exam) Object.assign(examDraft, {
        title: exam.title,
        questions: exam.questions.map(q => ({...q})),
        max_retakes: exam.max_retakes ?? 0,
        time_limit_minutes: exam.time_limit_minutes ?? null,
        exam_weight: exam.exam_weight ?? 70,
        assignment_weight: exam.assignment_weight ?? 30,
        passing_score: exam.passing_score ?? 60
      })
      else examDraft.title = (courses.current?.title ?? '') + ' Exam'
    }),
  ])
})
</script>

<style scoped>
/* ── Page actions bar ── */
.page-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 20px;
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 10px;
  flex-wrap: wrap;
}

.course-actions-title {
  font-size: 22px;
  letter-spacing: .3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}

.tabs {
  display: flex;
  border-bottom: 2px solid var(--lf-gray-200);
  margin-bottom: 24px;
  overflow-x: auto;
}

.tab {
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  color: var(--lf-gray-600);
  transition: all .15s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab:hover {
  color: var(--lf-black);
}

.tab.active {
  color: var(--lf-orange);
  border-bottom-color: var(--lf-orange);
}

.tab-badge {
  background: var(--lf-orange);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

.course-status-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .4px;
}

.course-status-pill.draft {
  background: var(--lf-gray-200);
  color: var(--lf-gray-600);
}

.course-status-pill.published {
  background: #e6f7ee;
  color: #25a244;
}

/* ── Weights ── */
.weights-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1.5px solid var(--lf-gray-200);
}

.weights-label {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.weights-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.weight-item {
  flex: 1;
  min-width: 140px;
}

.weight-plus {
  font-size: 20px;
  color: var(--lf-gray-400);
  padding-bottom: 10px;
  flex-shrink: 0;
}

.weight-equals {
  font-size: 20px;
  font-weight: 700;
  padding-bottom: 10px;
  flex-shrink: 0;
}

.weights-bar {
  display: flex;
  height: 10px;
  border-radius: 6px;
  overflow: hidden;
  margin-top: 12px;
}

.weights-bar-exam {
  background: var(--lf-orange);
  transition: width .3s;
}

.weights-bar-assign {
  background: #25a244;
  transition: width .3s;
}

/* ── Open response grading ── */
.open-response-card {
  border: 1.5px solid var(--lf-gray-200);
  border-left: 4px solid var(--lf-orange);
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 14px;
  background: var(--lf-white);
}

.open-response-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.open-response-question {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}

.open-response-answer {
  margin-bottom: 12px;
}

.open-response-text {
  background: var(--lf-gray-100);
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: var(--lf-gray-600);
  font-style: italic;
}

.open-response-grade-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.grade-input {
  width: 72px;
  padding: 6px 8px;
  border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 13px;
  outline: none;
}

.grade-input:focus {
  border-color: var(--lf-orange);
}

/* ── Lessons ── */
.lesson-status-btn {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  border: 1.5px solid;
  transition: all .15s;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: .3px;
}

.lesson-status-btn.draft {
  background: var(--lf-gray-100);
  border-color: var(--lf-gray-200);
  color: var(--lf-gray-600);
}

.lesson-status-btn.draft:hover:not(:disabled) {
  background: var(--lf-orange-light);
  border-color: var(--lf-orange);
  color: var(--lf-orange);
}

.lesson-status-btn.published {
  background: #e6f7ee;
  border-color: #25a244;
  color: #25a244;
}

.lesson-status-btn.published:hover:not(:disabled) {
  background: #fff5f5;
  border-color: #e53e3e;
  color: #e53e3e;
}

.lesson-status-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.lesson-list {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
  overflow: hidden;
}

.lesson-item {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--lf-gray-200);
}

.lesson-item:last-child {
  border-bottom: none;
}

.lesson-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--lf-gray-200);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.lesson-item-info {
  flex: 1;
}

.lesson-item-title {
  font-size: 14px;
  font-weight: 500;
}

.lesson-item-type {
  font-size: 12px;
  color: var(--lf-gray-400);
}

.drag-handle {
  cursor: grab;
  color: var(--lf-gray-400);
  font-size: 16px;
  padding: 0 6px;
  user-select: none;
  flex-shrink: 0;
}

.lesson-item:hover .drag-handle {
  color: var(--lf-gray-600);
}

.lesson-item.dragging {
  opacity: .4;
}

.lesson-item.drag-over {
  border-top: 2px solid var(--lf-orange);
  background: var(--lf-orange-light);
}

/* ── Assignments ── */
.assignment-lesson-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--lf-gray-400);
  padding: 4px 0 8px;
  border-bottom: 1px solid var(--lf-gray-200);
  margin-bottom: 10px;
}

.assignment-card {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 10px;
}

.assignment-card-header {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  background: var(--lf-white);
  transition: background .15s;
}

.assignment-card-header:hover {
  background: var(--lf-gray-100);
}

.assignment-card-body {
  padding: 16px 18px;
  border-top: 1px solid var(--lf-gray-200);
  background: var(--lf-gray-100);
}

.expand-chevron {
  color: var(--lf-gray-400);
  font-size: 14px;
  transition: transform .15s;
}

.expand-chevron.open {
  transform: rotate(180deg);
}

.submissions-sub-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.submissions-empty {
  padding: 16px;
  text-align: center;
  color: var(--lf-gray-400);
  font-size: 14px;
}

.submissions-table-wrap {
  overflow-x: auto;
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
}

.sub-text-preview {
  margin-top: 6px;
  font-size: 12px;
  color: var(--lf-gray-600);
  font-style: italic;
}

/* ── Q&A ── */
.qa-inbox-card {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.qa-inbox-card.resolved {
  border-color: #25a244;
}

.qa-inbox-header {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  background: var(--lf-white);
}

.qa-inbox-header:hover {
  background: var(--lf-gray-100);
}

.qa-inbox-body {
  padding: 16px 18px;
  border-top: 1px solid var(--lf-gray-200);
  background: var(--lf-gray-100);
}

.qa-inbox-question-text {
  font-size: 15px;
  line-height: 1.7;
  margin-bottom: 14px;
  white-space: pre-wrap;
}

.qa-inbox-answers {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.qa-inbox-answer {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
  padding: 12px 14px;
}

.qa-inbox-answer.is-teacher {
  border-color: var(--lf-orange);
  border-left-width: 3px;
}

.qa-inbox-answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.qa-inbox-answer-body {
  font-size: 14px;
  line-height: 1.6;
  color: var(--lf-gray-600);
  padding-left: 34px;
}

.qa-inbox-compose {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
  padding: 14px;
}

.qa-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--lf-orange);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.qa-avatar.sm {
  width: 26px;
  height: 26px;
  font-size: 11px;
}

.filter-count {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--lf-gray-200);
  color: var(--lf-gray-600);
  margin-left: 4px;
}

.filter-count-active {
  background: rgba(255, 255, 255, .2);
  color: #fff;
}

/* ── Analytics ── */
.analytics-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.spinner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid var(--lf-gray-200);
  border-top-color: var(--lf-orange);
  animation: spin .7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.analytics-charts-row {
  display: grid;
  grid-template-columns:1fr 1fr;
  gap: 20px;
}

@media (max-width: 760px) {
  .analytics-charts-row {
    grid-template-columns:1fr;
  }
}

.analytics-card-title {
  font-family: var(--lf-font-display);
  font-size: 20px;
}

.chart-wrap {
  position: relative;
}

.lesson-completion-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lc-row {
  display: grid;
  grid-template-columns:180px 1fr 48px 56px;
  align-items: center;
  gap: 12px;
}

.lc-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lc-bar-wrap {
  height: 8px;
  background: var(--lf-gray-200);
  border-radius: 4px;
  overflow: hidden;
}

.lc-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width .4s;
}

/* ── Misc ── */
.question-builder {
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: var(--lf-gray-100);
}

.session-item {
  padding: 16px 20px;
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  margin-bottom: 12px;
  background: var(--lf-white);
  display: flex;
  align-items: center;
  gap: 16px;
}

.session-date {
  font-size: 20px;
  min-width: 90px;
}

.session-info {
  flex: 1;
}

.session-label {
  font-size: 15px;
  font-weight: 600;
}

.session-code {
  font-family: monospace;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--lf-orange);
  background: var(--lf-orange-light);
  padding: 2px 8px;
  border-radius: 4px;
}

.notice-card {
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 14px;
}

.notice-card.pinned {
  border-color: var(--lf-orange);
}

.notice-card-header {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.notice-card-body {
  padding: 0 18px 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.code-box {
  background: var(--lf-black);
  border-radius: 8px;
  padding: 28px;
  text-align: center;
  border: 2px solid var(--lf-orange);
}

.code-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: #aaa;
  margin-bottom: 10px;
}

.code-val {
  font-family: var(--lf-font-display);
  font-size: 56px;
  color: var(--lf-orange);
  letter-spacing: 10px;
}

.drop-zone {
  border: 2px dashed var(--lf-gray-200);
  border-radius: 8px;
  padding: 28px 20px;
  text-align: center;
  cursor: pointer;
  background: var(--lf-gray-100);
  transition: all .2s;
}

.drop-zone:hover, .drop-zone.drop-active {
  border-color: var(--lf-orange);
  background: var(--lf-orange-light);
}

.attachments-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1.5px solid var(--lf-gray-200);
}

.attachments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.attach-upload-btn {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: var(--lf-radius);
  background: var(--lf-black);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.attach-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.attach-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 6px;
}

.attach-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.attach-info {
  flex: 1;
  overflow: hidden;
}

.attach-name {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attach-size {
  font-size: 11px;
}

/* ── Tables ── */
.lf-table {
  width: 100%;
  border-collapse: collapse;
}

.lf-table th {
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .7px;
  text-transform: uppercase;
  color: var(--lf-gray-600);
  border-bottom: 2px solid var(--lf-gray-200);
}

.lf-table td {
  padding: 12px 14px;
  font-size: 14px;
  border-bottom: 1px solid var(--lf-gray-200);
  vertical-align: top;
}

.lf-table tr:last-child td {
  border-bottom: none;
}

.lf-table tr:hover td {
  background: var(--lf-gray-100);
}

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: none;
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}

.btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--lf-orange);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--lf-orange-dark);
}

.btn-secondary {
  background: var(--lf-black);
  color: #fff;
}

.btn-secondary:hover:not(:disabled) {
  background: #222;
}

.btn-outline {
  background: transparent;
  color: var(--lf-black);
  border: 2px solid var(--lf-black);
}

.btn-outline:hover:not(:disabled) {
  background: var(--lf-black);
  color: #fff;
}

.btn-ghost {
  background: transparent;
  color: var(--lf-gray-600);
  border: 1px solid var(--lf-gray-200);
}

.btn-ghost:hover:not(:disabled) {
  border-color: var(--lf-black);
  color: var(--lf-black);
}

.btn-danger {
  background: #e53e3e;
  color: #fff;
}

.btn-danger:hover:not(:disabled) {
  background: #c53030;
}

.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
}

.form-control {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid var(--lf-gray-200);
  border-radius: var(--lf-radius);
  font-family: var(--lf-font-body);
  font-size: 14px;
  outline: none;
}

.form-control:focus {
  border-color: var(--lf-orange);
}

.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--lf-gray-600);
  margin-bottom: 6px;
}

.badge-blue {
  background: #e8f0fe;
  color: #2563eb;
}

/* ── Students tab ── */
.student-row {
  cursor: pointer;
}

.student-row:hover td {
  background: var(--lf-orange-light) !important;
}

/* ── Student grade drawer ── */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .35);
  z-index: 200;
  animation: fadeIn .15s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0
  }
  to {
    opacity: 1
  }
}

.student-drawer {
  position: fixed;
  top: 0;
  right: 0;
  height: 100vh;
  width: 460px;
  background: var(--lf-white);
  z-index: 201;
  box-shadow: -8px 0 40px rgba(0, 0, 0, .15);
  transform: translateX(100%);
  transition: transform .25s cubic-bezier(.4, 0, .2, 1);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.student-drawer.open {
  transform: translateX(0);
}

@media (max-width: 520px) {
  .student-drawer {
    width: 100vw;
  }
}

.drawer-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  border-bottom: 1.5px solid var(--lf-gray-200);
  position: sticky;
  top: 0;
  background: var(--lf-white);
  z-index: 1;
}

.drawer-grade-hero {
  margin: 20px 24px;
  border-radius: 10px;
  padding: 24px;
  text-align: center;
}

.drawer-grade-hero.passed {
  background: linear-gradient(135deg, #e6f7ee, #d4f4e4);
  border: 2px solid #25a244;
}

.drawer-grade-hero.failed {
  background: linear-gradient(135deg, #fff5f5, #ffe0e0);
  border: 2px solid #e53e3e;
}

.drawer-formula {
  margin: 0 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--lf-gray-100);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 10px;
  padding: 16px;
  flex-wrap: wrap;
}

.drawer-formula-item {
  flex: 1;
  text-align: center;
  min-width: 120px;
}

.drawer-formula-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: var(--lf-gray-400);
  margin-bottom: 6px;
}

.drawer-formula-val {
  font-size: 24px;
}

.drawer-formula-op {
  font-size: 24px;
  color: var(--lf-gray-400);
  flex-shrink: 0;
}

.drawer-section {
  margin: 0 24px 24px;
  padding: 16px;
  background: var(--lf-white);
  border: 1.5px solid var(--lf-gray-200);
  border-radius: 8px;
}
</style>
