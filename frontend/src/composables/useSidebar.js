/**
 * useSidebar
 *
 * A module-level shared ref so AppTopbar and AppSidebar
 * stay in sync without a full Pinia store.
 *
 * The ref lives outside the function so all callers share
 * the exact same reactive value — standard Vue composable pattern.
 */
import { ref } from 'vue'

const isOpen = ref(false)

export function useSidebar() {
  function open()   { isOpen.value = true  }
  function close()  { isOpen.value = false }
  function toggle() { isOpen.value = !isOpen.value }

  return { isOpen, open, close, toggle }
}
