<template>
  <!-- Contenedor fijo (esquina superior izquierda) -->
  <div class="toast-container">
    <TransitionGroup name="toast-list" tag="div">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="`toast--${toast.severity}`"
      >
        <div class="toast__icon" :class="`toast__icon--${toast.severity}`">
          <Icon
            v-if="toast.severity === 'success'"
            name="mdi:check-circle-outline"
            class="toast__icon-svg"
          />
          <Icon
            v-else-if="toast.severity === 'info'"
            name="mdi:information-outline"
            class="toast__icon-svg"
          />
          <Icon
            v-else-if="toast.severity === 'warn'"
            name="mdi:alert-circle-outline"
            class="toast__icon-svg"
          />
          <Icon
            v-else-if="toast.severity === 'error'"
            name="mdi:close-circle-outline"
            class="toast__icon-svg"
          />
          <Icon
            v-else
            name="mdi:bell-outline"
            class="toast__icon-svg"
          />
        </div>

        <div class="toast__content">
          <p v-if="toast.title" class="toast__title">
            {{ toast.title }}
          </p>
          <p class="toast__message">
            {{ toast.message }}
          </p>
        </div>

        <button
          v-if="toast.closable"
          class="toast__close-btn"
          type="button"
          @click="removeToast(toast.id)"
        >
          ✕
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

// Usamos el mismo state global
const { toasts, removeToast } = useToast()
</script>

<style scoped>
.toast-container {
  position: fixed;
  right: 1rem;      /* esquina superior izquierda */
  top: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: min(360px, 95vw);
}

/* Animaciones de entrada/salida */
.toast-list-enter-active,
.toast-list-leave-active {
  transition: all 0.25s ease-out;
}

.toast-list-enter-from,
.toast-list-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

/* Card base (tema claro) */
.toast {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
}

/* Severities (fondo + borde + tono) */
.toast--success {
  background: #ecfdf3;
  border-color: #4ade80;
}

.toast--info {
  background: #eff6ff;
  border-color: #60a5fa;
}

.toast--warn {
  background: #fffbeb;
  border-color: #facc15;
}

.toast--error {
  background: #fef2f2;
  border-color: #f87171;
}

/* Icono */
.toast__icon {
  flex: 0 0 auto;
  margin-top: 0.1rem;
}

.toast__icon-svg {
  width: 1.3rem;
  height: 1.3rem;
}

/* Colores del icono según severidad */
.toast__icon--success .toast__icon-svg {
  color: #16a34a;
}

.toast__icon--info .toast__icon-svg {
  color: #2563eb;
}

.toast__icon--warn .toast__icon-svg {
  color: #d97706;
}

.toast__icon--error .toast__icon-svg {
  color: #b91c1c;
}

/* Contenido */
.toast__content {
  flex: 1 1 auto;
  min-width: 0;
}

.toast__title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
}

.toast__message {
  margin: 0.15rem 0 0 0;
  font-size: 0.85rem;
  line-height: 1.3;
  color: #374151;
}

/* Botón cerrar */
.toast__close-btn {
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.9rem;
  flex: 0 0 auto;
  margin-left: 0.25rem;
  padding: 0;
}

.toast__close-btn:hover {
  color: #4b5563;
}

/* Mobile */
@media (max-width: 640px) {
  .toast-container {
    left: 0.5rem;
    right: 0.5rem;
    top: 0.75rem;
    max-width: none;
  }
}
</style>
