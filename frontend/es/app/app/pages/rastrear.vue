<template>
  <div class="track-page">
    <main class="track-main">
      <section class="track-card animate-entry">
        <header class="track-card__header">
          <h1 class="track-title">Rastrea tu pedido</h1>
          <p class="track-subtitle">
            Ingresa el ID de tu pedido para ver su estado actual y el historial.
          </p>
        </header>

        <form @submit.prevent="getStatusHistory" class="search-wrapper">
          <div class="search-input-wrapper">
            <Icon name="mdi:tag-outline" class="search-input-icon" />
            <input
              v-model="orderId"
              type="text"
              class="search-input"
              placeholder="Ejemplo: MOD-0054..."
            />
          </div>

          <button type="submit" class="search-button" :disabled="loading">
            <Transition name="rotate" mode="out-in">
              <Icon
                v-if="loading"
                name="mdi:loading"
                class="search-icon spin-animation"
              />
              <Icon
                v-else
                name="mdi:magnify"
                class="search-icon"
              />
            </Transition>
          </button>
        </form>

        <div class="track-messages">
          <Transition name="fade" mode="out-in">
            <div v-if="loading" class="alert alert--info" key="loading">
              <Icon name="mdi:clock-outline" class="alert__icon" />
              <span>Buscando tu pedido...</span>
            </div>

            <div v-else-if="error" class="alert alert--error" key="error">
              <Icon name="mdi:alert-circle-outline" class="alert__icon" />
              <span>{{ error }}</span>
            </div>
          </Transition>
        </div>

        <Transition name="slide-up">
          <section
            v-if="!loading && !error && currentStatus"
            class="current-status"
          >
            <h2 class="current-status__title">
              ¡Gracias por tu compra!
            </h2>

            <p v-if="currentStatus.status === 'generada'" class="current-status__text">
              Tu pedido ha sido recibido y está en proceso de ser atendido.
            </p>
            <p v-else-if="currentStatus.status === 'en preparacion'" class="current-status__text">
              Tu pedido se encuentra en preparación y en breve estará listo para enviarse.
            </p>
            <p v-else-if="currentStatus.status === 'enviada'" class="current-status__text">
              ¡Tu pedido está en camino!
            </p>
            <p v-else class="current-status__text">
              Estado actual: <strong>{{ currentStatus.status }}</strong>
            </p>

            <div
              v-if="currentStatus.status === 'enviada'"
              class="current-status__badge pulse-badge"
            >
              <Icon name="mdi:truck-delivery-outline" class="current-status__badge-icon" />
              <span>Tu pedido está en camino</span>
            </div>
          </section>
        </Transition>

        <section
          v-if="!loading && !error && currentStatus && firstHistory && firstHistory.status_history"
          class="history"
        >
          <h3 class="history__title">Historial de estado</h3>
          
          <TransitionGroup name="list" tag="ul" class="status-timeline">
            <li
              v-for="(stat, index) in firstHistory.status_history"
              :key="stat.timestamp"
              class="status-timeline__item"
              :style="{ transitionDelay: `${index * 100}ms` }"
            >
              <div class="status-timeline__marker"></div>
              <div class="status-timeline__content">
                <p class="status-timeline__status">
                  {{ stat.status }}
                </p>
                <p class="status-timeline__timestamp">
                  {{ stat.timestamp }}
                </p>
              </div>
            </li>
          </TransitionGroup>
        </section>

        <Transition name="fade">
          <section
            v-if="!loading && !error && !currentStatus && !firstHistory"
            class="empty-state"
          >
            <Icon name="mdi:clipboard-text-search-outline" class="empty-state__icon float-animation" />
            <p class="empty-state__text">
              Ingresa el ID de tu pedido para ver su estado.
            </p>
          </section>
        </Transition>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue' // 1. Agregamos onMounted
import { useRoute } from 'vue-router' // 2. Agregamos useRoute
import { URI } from '@/service/conection'

const route = useRoute() // 3. Inicializamos route
const orderId = ref('')
const history = ref([])
const currentStatus = ref(null)
const loading = ref(false)
const error = ref(null)

const firstHistory = computed(() => {
  return Array.isArray(history.value) && history.value.length > 0
    ? history.value[0]
    : null
})

const getStatusHistory = async () => {
  if (!orderId.value) {
    error.value = 'Por favor ingresa el ID de tu pedido.'
    currentStatus.value = null
    history.value = []
    return
  }

  loading.value = true
  error.value = null
  currentStatus.value = null 
  history.value = []

  try {
    // Nota: Mantengo tu $fetch nativo de Nuxt
    const result = await $fetch(`${URI}/history-my-orden/${orderId.value}`)
    
    // Timeout estético opcional
    await new Promise(resolve => setTimeout(resolve, 500))

    history.value = Array.isArray(result) ? result : []
    currentStatus.value = history.value[0]?.current_status || null

    if (!currentStatus.value) {
      error.value = 'No encontramos el estado actual de tu pedido.'
    }
  } catch (err) {
    console.error('Error al obtener el historial de estado:', err)
    error.value = 'No pudimos encontrar tu pedido. Verifica el ID e inténtalo de nuevo.'
    history.value = []
    currentStatus.value = null
  } finally {
    loading.value = false
  }
}

// 4. Lógica automática al cargar la página
onMounted(() => {
  // Busca si existe 'order_id' en la URL (ej: ?order_id=123)
  const idFromUrl = route.query.order_id || route.query.id

  if (idFromUrl) {
    orderId.value = idFromUrl
    // Ejecuta la búsqueda automáticamente
    getStatusHistory()
  }
})
</script>

<style scoped>
/* TUS MISMOS ESTILOS - NO ES NECESARIO CAMBIARLOS */
:root {
  --primary-color: #d60000;
}

.track-page {
  min-height: 80vh;
  display: flex;
  justify-content: center;
  padding: 2rem 1rem 3rem;
  background: radial-gradient(circle at top, #f8fafc, #f1f5f9);
}

.track-main {
  width: 100%;
  max-width: 720px;
  margin: auto;
}

.animate-entry {
  animation: cardEnter 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  opacity: 0;
  transform: translateY(30px);
}

@keyframes cardEnter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.track-card {
  background-color: #ffffff;
  border-radius: 1.5rem;
  padding: 2rem 1.75rem 2.5rem;
  box-shadow: 0 22px 45px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.track-card:hover {
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.12);
}

.track-card__header {
  text-align: center;
  margin-bottom: 2rem;
}

.track-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--primary-color);
}

.track-subtitle {
  margin-top: 0.5rem;
  margin-bottom: 0;
  font-size: 0.95rem;
  color: #6b7280;
}

.search-wrapper {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: nowrap;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
}

.search-input-icon {
  position: absolute;
  left: 0.9rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.1rem;
  color: #9ca3af;
  transition: color 0.3s ease;
}

.search-input:focus ~ .search-input-icon,
.search-input:focus + .search-input-icon {
    color: var(--primary-color);
}

.search-input-wrapper:focus-within .search-input-icon {
    color: var(--primary-color);
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background-color: #ffffff;
  font-size: 0.95rem;
  color: #111827;
  outline: none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(214, 0, 0, 0.08);
  background-color: #fff;
  transform: scale(1.01);
}

.search-button {
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  background: var(--primary-color);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  overflow: hidden; 
}

.search-button:disabled {
  opacity: 0.8;
  cursor: wait;
  transform: scale(0.95);
}

.search-button:not(:disabled):hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(214, 0, 0, 0.3);
}

.search-button:not(:disabled):active {
  transform: translateY(0);
}

.search-icon {
  font-size: 1.4rem;
  color: #ffffff;
}

.spin-animation {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.track-messages {
  min-height: 2.5rem; 
  margin-bottom: 0.5rem;
  overflow: hidden;
}

.alert {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  border-radius: 999px;
  padding: 0.5rem 0.9rem;
}

.alert__icon {
  font-size: 1.1rem;
}

.alert--info {
  background-color: #e0f2fe;
  color: #0369a1;
}

.alert--error {
  background-color: #fee2e2;
  color: #b91c1c;
}

.current-status {
  margin-top: 1.2rem;
  padding: 1.5rem 1rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, #fff1f2, #fff7ed);
  border: 1px solid rgba(252, 165, 165, 0.4);
  text-align: center;
  box-shadow: inset 0 0 20px rgba(255,255,255,0.5);
}

.current-status__title {
  margin: 0 0 0.4rem;
  font-size: 1.4rem;
  font-weight: 700;
  color: #b91c1c;
}

.current-status__text {
  margin: 0;
  font-size: 0.95rem;
  color: #4b5563;
}

.current-status__badge {
  margin-top: 1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 1rem;
  border-radius: 999px;
  background-color: #dcfce7;
  color: #15803d;
  font-size: 0.85rem;
  font-weight: 600;
  border: 1px solid #86efac;
}

.pulse-badge {
  animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
  0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
  100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
}

.history {
  margin-top: 2rem;
}

.history__title {
  margin: 0 0 1rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: #111827;
}

.status-timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}

.status-timeline__item {
  display: flex;
  gap: 0.75rem;
  position: relative;
  padding-bottom: 1.5rem;
}

.status-timeline__item:last-child {
  padding-bottom: 0;
}

.status-timeline__item::before {
  content: '';
  position: absolute;
  left: 0.5rem;
  top: 0.7rem;
  width: 2px;
  height: calc(100% - 0.7rem);
  background: linear-gradient(to bottom, #fca5a5, rgba(254, 202, 202, 0.2));
  opacity: 0.8;
  z-index: 0;
}

.status-timeline__item:last-child::before {
  display: none;
}

.status-timeline__marker {
  width: 0.9rem;
  height: 0.9rem;
  border-radius: 999px;
  background: #ef4444;
  margin-top: 0.3rem;
  box-shadow: 0 0 0 4px rgba(254, 226, 226, 1);
  flex-shrink: 0;
  z-index: 1;
  position: relative;
  transition: transform 0.3s ease;
}

.status-timeline__item:hover .status-timeline__marker {
  transform: scale(1.2);
  background: #dc2626;
}

.status-timeline__content {
  flex: 1;
}

.status-timeline__status {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: capitalize;
  color: #111827;
}

.status-timeline__timestamp {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: #6b7280;
}

.empty-state {
  margin-top: 1.5rem;
  padding: 2rem 1rem;
  border-radius: 1rem;
  background-color: #f8fafc;
  border: 2px dashed #e2e8f0;
  text-align: center;
}

.empty-state__icon {
  font-size: 2.5rem;
  color: #cbd5e1;
  display: inline-block;
}

.float-animation {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.empty-state__text {
  margin-top: 0.8rem;
  font-size: 0.9rem;
  color: #64748b;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active {
  transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.rotate-enter-active,
.rotate-leave-active {
  transition: all 0.3s ease;
}
.rotate-enter-from,
.rotate-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.5);
}

.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

@media (max-width: 640px) {
  .track-card {
    padding: 1.5rem 1.25rem 2rem;
  }
}
</style>