import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useNotesStore = defineStore('notes', () => {
  /**
   * In-memory cache of notes keyed by lessonId.
   * Shape: { [lessonId]: { id, student, lesson, body, updated_at } }
   */
  const notes = ref({})

  /**
   * Fetch (or create blank) the current student's note for a lesson.
   * GET /api/courses/{courseId}/lessons/{lessonId}/note/
   * The backend does get_or_create, so this never 404s for enrolled students.
   *
   * @returns {Object} note object { body, updated_at, ... }
   */
  async function fetchNote(courseId, lessonId) {
    try {
      const { data } = await api.get(`/courses/${courseId}/lessons/${lessonId}/note/`)
      notes.value[lessonId] = data
      return data
    } catch {
      // Graceful fallback — treat as blank note so the UI still renders
      const blank = { body: '', updated_at: null }
      notes.value[lessonId] = blank
      return blank
    }
  }

  /**
   * Upsert the note body for a lesson.
   * PATCH /api/courses/{courseId}/lessons/{lessonId}/note/
   *
   * @returns {Object} updated note object
   */
  async function saveNote(courseId, lessonId, body) {
    const { data } = await api.patch(
      `/courses/${courseId}/lessons/${lessonId}/note/`,
      { body },
    )
    notes.value[lessonId] = data
    return data
  }

  /**
   * Return the cached note body for a lesson, or '' if not yet fetched.
   */
  function getNoteBody(lessonId) {
    return notes.value[lessonId]?.body ?? ''
  }

  /**
   * Clear all cached notes (e.g. on logout).
   */
  function clearNotes() {
    notes.value = {}
  }

  return { notes, fetchNote, saveNote, getNoteBody, clearNotes }
})
