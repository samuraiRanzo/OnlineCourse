/**
 * useTeleportReady — returns a ref that flips true after onMounted.
 *
 * Use case: Teleport targets rendered by sibling components in the same
 * render cycle. Vue 3.4 has no <Teleport defer> (added in 3.5), so we
 * guard the Teleport with v-if="teleportReady" to let the DOM settle first.
 *
 * Usage in a view:
 *   const teleportReady = useTeleportReady()
 *   <Teleport v-if="teleportReady" to="#topbar-actions"> ... </Teleport>
 */
import { ref, onMounted } from 'vue'

export function useTeleportReady() {
  const ready = ref(false)
  onMounted(() => { ready.value = true })
  return ready
}