// composables/useToast.js
export function useToast () {
  // State global (compartido en toda la app)
  const toasts = useState('toasts', () => [])

  const removeToast = (id) => {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx !== -1) {
      toasts.value.splice(idx, 1)
    }
  }

  /**
   * showToast({
   *   title: 'Listo',
   *   message: 'Producto agregado al carrito',
   *   severity: 'success' | 'info' | 'warn' | 'error',
   *   duration: 3000,
   *   closable: true
   * })
   */
  const showToast = ({
    title = '',
    message = '',
    severity = 'info',
    duration = 3000,
    closable = true
  } = {}) => {
    const id = Date.now() + Math.random()

    const toast = {
      id,
      title,
      message,
      severity,   // 'success', 'info', 'warn', 'error'
      closable,
      createdAt: Date.now()
    }

    toasts.value.push(toast)

    // Autocerrar
    if (duration && duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }

    return id
  }

  const clearToasts = () => {
    toasts.value = []
  }

  return {
    toasts,
    showToast,
    removeToast,
    clearToasts
  }
}
