<template>
  <div class="monster-ayuda-page">
    <Transition name="dialog">
      <div v-if="visibleDialog" class="dialog-overlay">
        <div class="dialog-custom">
          <div class="dialog-header">
            <Icon name="mdi:check-circle" class="dialog-header-icon" />
            <h3 class="dialog-header-title">Solicitud recibida</h3>
          </div>
          <div class="dialog-content">
            <p class="dialog-text">
              Hemos recibido tu solicitud y ha quedado registrada con el ID:
            </p>
            <p class="last-id">{{ last_id }}</p>

            <NuxtLink to="/" class="dialog-link">
              <button class="btn btn-primary">
                <Icon name="mdi:check-circle-outline" class="btn-icon" />
                Listo
              </button>
            </NuxtLink>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="dialog">
      <div v-if="visibleDialogGRacias" class="dialog-overlay">
        <div class="dialog-custom">
          <div class="dialog-header dialog-header--success">
            <Icon name="mdi:emoticon-happy-outline" class="dialog-header-icon" />
            <h3 class="dialog-header-title">¡Gracias por tu calificación!</h3>
          </div>
          <div class="dialog-content">
            <p class="gracias-message">Muchas gracias 💛</p>

            <NuxtLink to="/" class="dialog-link">
              <button class="btn btn-primary">
                <Icon name="mdi:check-circle-outline" class="btn-icon" />
                Listo
              </button>
            </NuxtLink>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="dialog">
      <div v-if="visibleErrorDialog" class="dialog-overlay">
        <div class="dialog-custom">
          <div class="dialog-header dialog-header--error">
            <Icon name="mdi:alert-circle-outline" class="dialog-header-icon" />
            <h3 class="dialog-header-title">Revisa tu información</h3>
          </div>
          <div class="dialog-content">
            <p class="dialog-text">
              {{ errorMessage }}
            </p>

            <button
              class="btn btn-primary"
              type="button"
              @click="visibleErrorDialog = false"
            >
              <Icon name="mdi:close" class="btn-icon" />
              Entendido
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <main class="main-wrapper">
      <section class="card animate-entry">
        <header class="card-header">
          <div class="card-title-group">
            <h1 class="title">
              🔥 <b>MONSTER AYUDA</b> 🔥
            </h1>
            <p class="subtitle">
              Cada día trabajamos para darte una mejor experiencia.
            </p>
          </div>

          <img
            src="https://www.salchimonster.com/images/kids/3.png"
            alt="Monster Ayuda"
            class="main-image"
          />
        </header>

        <div v-if="pending" class="form-skeleton">
          <div class="skeleton skeleton-text" style="width: 40%"></div>
          <div class="skeleton skeleton-input"></div>
          
          <div class="skeleton skeleton-text" style="width: 30%; margin-top: 1rem"></div>
          <div class="skeleton skeleton-input"></div>

          <div class="skeleton skeleton-text" style="width: 20%; margin-top: 1rem"></div>
          <div class="skeleton skeleton-input" style="height: 100px"></div>
          
          <div class="form-grid" style="margin-top: 1rem">
             <div class="skeleton skeleton-input"></div>
             <div class="skeleton skeleton-input"></div>
             <div class="skeleton skeleton-input"></div>
             <div class="skeleton skeleton-input"></div>
          </div>
        </div>

        <div v-else class="form-container fade-in">
          <div class="form-group">
            <label class="field-label">
              ¿Cómo te podemos ayudar?
              <span class="field-required">*</span>
            </label>
            <select
              class="input input-select input-uppercase"
              v-model.number="selectedType"
            >
              <option value="" disabled>Selecciona una opción</option>
              <option
                v-for="t in apiData.types.filter(t => t.show_on_web)"
                :key="t.id"
                :value="t.id"
              >
                {{ t.name }}
              </option>
            </select>
          </div>

          <Transition name="slide-fade">
            <div class="form-group" v-if="selectedType && selectedType !== 8">
              <label class="field-label">
                Clasifica tu inconveniente
                <span class="field-required">*</span>
              </label>
              <select
                class="input input-select"
                v-model.number="selectedTagId"
              >
                <option value="" disabled>Selecciona una opción</option>
                <option v-for="tag in apiData.tags" :key="tag.id" :value="tag.id">
                  {{ tag.name }}
                </option>
              </select>

              <div v-if="currentTag" class="tag-preview">
                <span
                  class="tag-circle"
                  :style="{ backgroundColor: currentTag.color }"
                ></span>
                <span class="tag-name">{{ currentTag.name }}</span>
              </div>
            </div>
          </Transition>

          <Transition name="slide-fade">
            <div class="form-group" v-if="selectedType">
              <label class="field-label">
                Sede
                <span class="field-required">*</span>
              </label>
              <select
                class="input input-select"
                v-model.number="selecteSite"
              >
                <option value="" disabled>Selecciona una sede</option>
                <option
                  v-for="s in apiData.sites.filter(s => s.show_on_web && s.time_zone == 'America/Bogota')"
                  :key="s.site_id"
                  :value="s.site_id"
                >
                  {{ s.site_name }}
                </option>
              </select>
            </div>
          </Transition>

          <div class="form-group" v-if="selectedType === 9">
            <label class="field-label">
              ID de la orden
              <span class="field-hint">Ejemplo: <b>BRE-0554</b></span>
              <span class="field-required">*</span>
            </label>
            <input
              v-model="orderId"
              class="input"
              type="text"
              placeholder="Escribe el número de la orden"
            />
          </div>

          <div
            class="form-group rating-section"
            v-if="selectedType === 8"
          >
            <label class="field-label">
              Califícanos
              <span class="field-required">*</span>
            </label>
            <div class="rating-stars">
              <button
                v-for="star in 5"
                :key="star"
                type="button"
                class="star-button"
                :class="{ active: rating >= star }"
                @click="rating = star"
              >
                <Icon
                  :name="rating >= star ? 'mdi:star' : 'mdi:star-outline'"
                  class="star-icon"
                />
              </button>
            </div>
          </div>

          <Transition name="slide-fade">
            <div class="form-group" v-if="selectedType">
              <label class="field-label">
                Comentarios
                <span v-if="selectedType !== 8" class="field-required">*</span>
              </label>
              <textarea
                v-model="comments"
                rows="4"
                class="input textarea"
                placeholder="Cuéntanos qué sucedió o cómo fue tu experiencia"
              ></textarea>
            </div>
          </Transition>

          <Transition name="slide-fade">
            <div
              class="form-grid"
              v-if="selectedType"
            >
              <div class="form-group">
                <label class="field-label">
                  Nombre
                  <span v-if="selectedType !== 8" class="field-required">*</span>
                </label>
                <input
                  v-model="userName"
                  class="input"
                  type="text"
                  placeholder="Escribe tu nombre"
                />
              </div>

              <div class="form-group">
                <label class="field-label">
                  Número de teléfono
                  <span v-if="selectedType !== 8" class="field-required">*</span>
                </label>
                <input
                  v-model="userPhone"
                  class="input"
                  type="tel"
                  placeholder="Celular o número de contacto"
                />
              </div>

              <div class="form-group">
                <label class="field-label">
                  Correo electrónico
                  <span v-if="selectedType !== 8" class="field-required">*</span>
                </label>
                <input
                  v-model="userEmail"
                  class="input"
                  type="email"
                  placeholder="Escribe tu correo"
                />
              </div>

              <div class="form-group">
                <label class="field-label">
                  Dirección
                  <span v-if="selectedType !== 8" class="field-required">*</span>
                </label>
                <input
                  v-model="userAddress"
                  class="input"
                  type="text"
                  placeholder="Dirección donde ocurrió el servicio"
                />
              </div>
            </div>
          </Transition>

          <div class="form-footer">
            <p class="form-note">
              <span class="field-required">*</span> Campos obligatorios
            </p>
            <button
              class="btn btn-primary"
              type="button"
              @click="handleSubmit"
              :disabled="sending"
            >
              <Icon v-if="sending" name="mdi:loading" class="btn-icon spin" />
              <Icon v-else name="mdi:send" class="btn-icon" />
              {{ sending ? 'Enviando...' : 'Enviar solicitud' }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { URI } from '~/service/conection'

/* --- STATE UI --- */
const visibleDialog = ref(false)
const visibleDialogGRacias = ref(false)
const visibleErrorDialog = ref(false)
const errorMessage = ref('')
const sending = ref(false) // Estado de carga del envío
const last_id = ref('')

/* --- STATE FORM --- */
const selectedType = ref(null)
const selecteSite = ref(null)
const selectedTagId = ref(null)
const orderId = ref('')
const userName = ref('')
const userPhone = ref('')
const userEmail = ref('')
const userAddress = ref('')
const comments = ref('')
const rating = ref(0)

/* --- DATA FETCHING OPTIMIZADO (SSR + CACHE) --- */
// Usamos useAsyncData para cargar todo en paralelo antes del render
// Si configuras ISR en nuxt.config, esto se revalida cada hora
const { data: apiData, pending, error: fetchError } = await useAsyncData(
  'monster-help-data', 
  async () => {
    const [types, sites, tags] = await Promise.all([
      $fetch(`${URI}/get-all-pqrs-types`),
      $fetch(`${URI}/sites`),
      $fetch(`${URI}/get-all-pqr-tags`)
    ])
    return { 
      types: types || [], 
      sites: sites || [], 
      tags: tags || [] 
    }
  },
  {
    lazy: true, // Permite cargar la UI (Skeletons) mientras llega la data
    server: true, // Habilita SSR
    default: () => ({ types: [], sites: [], tags: [] }) // Valor inicial para evitar crash
  }
)

/* --- COMPUTED --- */
// Tag actual seleccionado
const currentTag = computed(() => {
  if (!apiData.value?.tags) return null
  return apiData.value.tags.find(t => t.id === selectedTagId.value) || null
})

// Inicialización de valores por defecto cuando llega la data
// Watcher opcional si necesitas setear un valor por defecto apenas cargue
// En este caso, si types carga, seteamos el 9 por defecto
if (!pending.value && apiData.value?.types?.length) {
    selectedType.value = 9
} 
// O usamos watch para cuando lazy termine
import { watch } from 'vue'
watch(pending, (newVal) => {
    if (!newVal && apiData.value?.types) {
         selectedType.value = 9
    }
})

/* --- ACTIONS --- */
const showError = (msg) => {
  errorMessage.value = msg
  visibleErrorDialog.value = true
}

const handleSubmit = async () => {
  if (sending.value) return // Evitar doble click

  // VALIDACIONES
  if (!selectedType.value) return showError('Por favor, selecciona un tipo de requerimiento.')
  if (selectedType.value === 9 && !orderId.value) return showError('Por favor, ingresa el ID de la orden.')
  if (selectedType.value !== 8 && !selectedTagId.value) return showError('Por favor, clasifica tu inconveniente.')
  if (selectedType.value !== 8 && !comments.value) return showError('Por favor, cuéntanos lo sucedido.')
  
  if (selectedType.value !== 8 && (!userName.value || !userPhone.value || !userAddress.value || !userEmail.value)) {
    return showError('Por favor, completa los campos obligatorios: nombre, teléfono, dirección y correo electrónico.')
  }

  if (!selecteSite.value) return showError('Por favor, selecciona la sede.')
  if (selectedType.value === 8 && !rating.value) return showError('Por favor, selecciona una calificación.')

  sending.value = true

  const data = {
    data: {
      reques_type_id: selectedType.value,
      content: comments.value || 'Sin comentarios',
      channel_id: 1,
      rating: rating.value || null,
      site_id: selecteSite.value || null,
      order_id: orderId.value || null,
      network_id: 4,
      tag_id: selectedTagId.value || 7,
      restaurant_id: 1
    },
    user: {
      user_name: userName.value || '',
      user_phone: userPhone.value?.toString() || '',
      user_address: userAddress.value || '',
      site_id: selecteSite.value || null,
      email: userEmail.value || ''
    }
  }

  try {
    const res = await $fetch(`${URI}/create-pqr`, {
      method: 'POST',
      body: data
    })
    
    // Asumiendo que $fetch lanza error si falla, o validamos respuesta
    last_id.value = res?.pqr_id?.[0]?.id || ''

    if (selectedType.value === 8) {
      visibleDialogGRacias.value = true
    } else {
      visibleDialog.value = true
    }
    
    // Reset form opcional
    // comments.value = ''
    // rating.value = 0
  } catch (error) {
    console.error('Error al enviar:', error)
    showError('Hubo un error al enviar tu solicitud. Inténtalo de nuevo.')
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
:root {
  --monster-primary: #ffca28;
  --monster-primary-strong: #ff9800;
  --monster-bg: #f5f5f7;
  --monster-text: #222;
  --monster-muted: #6b7280;
}

/* LAYOUT GENERAL */
.monster-ayuda-page {
  position: relative;
  min-height: 100vh;
  background: var(--monster-bg);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 3rem 1rem;
  box-sizing: border-box;
}

.main-wrapper {
  width: 100%;
  max-width: 900px;
}

/* ANIMACIÓN ENTRADA CARD */
.animate-entry {
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* CARD PRINCIPAL */
.card {
  background-color: #ffffff;
  border-radius: .3rem;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.17), 0 0 0 1px rgba(148, 163, 184, 0.12);
  padding: 2rem;
  backdrop-filter: blur(6px);
  min-height: 400px; /* Evita colapso visual */
}

/* SKELETON LOADER STYLES */
.form-skeleton {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding-top: 1rem;
}

.skeleton {
    background: #e2e8f0;
    background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 6px;
}

.skeleton-text {
    height: 1.2rem;
    margin-bottom: 0.5rem;
}

.skeleton-input {
    height: 42px;
    width: 100%;
}

@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* HEADER CARD */
.card-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.75rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
  padding-bottom: 1.5rem;
}

.title {
  margin: 0;
  font-size: 1.8rem;
  line-height: 1.2;
  color: #111827;
}

.subtitle {
  margin-top: 0.4rem;
  font-size: 0.98rem;
  color: var(--monster-muted);
}

.main-image {
  width: 160px;
  max-width: 40%;
}

/* FORMULARIO */
.form-container {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* TRANSICIÓN DE APARICIÓN SUAVE DEL FORM */
.fade-in {
    animation: fadeIn 0.4s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* TRANSICIONES VUE (SLIDE FADE) */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
}

.field-required {
  color: #ef4444;
  font-size: 0.8rem;
}

.field-hint {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--monster-muted);
}

/* INPUTS GENERALES */
.input {
  width: 100%;
  padding: 0.55rem 0.75rem;
  border-radius: 0.55rem;
  border: 1px solid rgba(148, 163, 184, 0.7);
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
  background-color: #f9fafb;
}

.input:focus {
  border-color: var(--monster-primary-strong);
  box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.3);
  background-color: #ffffff;
}

.input-select {
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, #9ca3af 50%), linear-gradient(135deg, #9ca3af 50%, transparent 50%);
  background-position: calc(100% - 14px) calc(50% - 3px), calc(100% - 8px) calc(50% - 3px);
  background-size: 6px 6px, 6px 6px;
  background-repeat: no-repeat;
}

.input-uppercase { text-transform: uppercase; }
.textarea { min-height: 100px; resize: vertical; }

/* GRID DATOS PERSONALES */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem 1.25rem;
}

/* TAG PREVIEW */
.tag-preview {
  margin-top: 0.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background-color: rgba(15, 23, 42, 0.03);
}

.tag-circle {
  height: 0.9rem;
  width: 0.9rem;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.7);
}

.tag-name { font-size: 0.8rem; color: #4b5563; }

/* RATING */
.rating-section {
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.06), rgba(56, 189, 248, 0.08));
  border: 1px dashed rgba(148, 163, 184, 0.7);
}

.rating-stars { display: flex; gap: 0.35rem; margin-top: 0.4rem; }

.star-button {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0.15rem;
  transition: transform 0.1s ease;
}

.star-button:hover { transform: translateY(-1px) scale(1.03); }
.star-icon { font-size: 1.8rem; color: #d1d5db; }
.star-button.active .star-icon { color: #f59e0b; }

/* PIE DE FORMULARIO */
.form-footer {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.form-note { font-size: 0.8rem; color: var(--monster-muted); }

/* BOTONES */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  border-radius: 999px;
  padding: 0.5rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 700;
  border: none;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  transition: transform 0.1s ease, box-shadow 0.15s ease, filter 0.1s ease;
  white-space: nowrap;
}

.btn-primary {
  background: var(--primary-color);
  color: #ffffff;
  border-radius: 0.3rem;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.03);
  transform: translateY(-1px);
}

.btn-primary:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

.btn-icon { font-size: 1.1rem; }

/* DIÁLOGOS Y TRANSICIONES */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.55);
  z-index: 50;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
}

.dialog-enter-active, .dialog-leave-active { transition: opacity 0.3s ease; }
.dialog-enter-from, .dialog-leave-to { opacity: 0; }

.dialog-custom {
  width: 100%;
  max-width: 420px;
  background-color: #ffffff;
  border-radius: .3rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 1.4rem;
  background: linear-gradient(135deg, #0f172a, #1f2937);
  color: #f9fafb;
}

.dialog-header--success { background: linear-gradient(135deg, #16a34a, #22c55e); }
.dialog-header--error { background: linear-gradient(135deg, #b91c1c, #ef4444); }

.dialog-header-icon { font-size: 1.6rem; }
.dialog-header-title { font-size: 1rem; font-weight: 600; }

.dialog-content { padding: 1.4rem 1.6rem 1.2rem 1.6rem; text-align: center; }
.dialog-text { margin: 0 0 0.75rem 0; font-size: 0.95rem; color: #374151; }

.last-id {
  font-size: 2.4rem;
  font-weight: 800;
  color: #111827;
  letter-spacing: 0.08em;
  margin: 0.3rem 0 0.4rem 0;
}

.gracias-message {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 0.8rem;
  color: #111827;
}

.dialog-link { text-decoration: none; }

/* RESET LOCAL */
h1, h2, h3, p { margin: 0; padding: 0; }

/* RESPONSIVE */
@media (max-width: 768px) {
  .monster-ayuda-page { padding: 2rem 1rem; }
  .card { padding: 1.5rem 1.3rem; }
  .card-header { flex-direction: column; align-items: flex-start; }
  .main-image { align-self: center; }
  .form-grid { grid-template-columns: 1fr; }
  .form-footer { flex-direction: column-reverse; align-items: flex-start; }
}
</style>