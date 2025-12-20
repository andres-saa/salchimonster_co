<template>
  <Dialog
    style="max-width: 30rem; margin: .5rem; width: 90%;"
    modal
    v-model:visible="store.visibles.currentSite"
  >
    <div>
      <div class="modal-body">
        <!-- ================== CIUDAD ================== -->
        <div class="form-group">
          <label>¿En qué ciudad te encuentras?</label>

          <div class="custom-select">
            <Select
              v-model="currenCity"
              :options="cityOptions"
              optionLabel="city_name"
              placeholder="Selecciona una ciudad"
              filter
              filterPlaceholder="Buscar ciudad..."
              :loading="spinnersView.ciudad"
              class="pv-select"
            />
          </div>

          <span v-if="spinnersView.ciudad" class="loader-mini-external"></span>
        </div>

        <!-- ================== GOOGLE AUTOCOMPLETE (ANTES ERA EL MENSAJE) ================== -->
        <template v-if="isGoogleMapsCity">
          <div v-if="currenCity" class="form-group fade-in">
            <label>¿Cuál es tu dirección?</label>

            <AutoComplete
              v-model="addressQuery"
              :suggestions="dirOptions"
              optionLabel="description"
              :completeOnFocus="true"
              :delay="150"
              class="pv-ac"
              inputClass="pv-ac-input"
              placeholder="Buscar dirección (Ej: Calle 123...)"
              @complete="onGoogleComplete"
              @item-select="onGoogleSelect"
            >
              <template #option="{ option }">
                <div style="display:flex; gap:.6rem; align-items:flex-start;">
                  <div style="margin-top:2px; opacity:.7;">
                    <Icon name="mdi:map-marker-outline" />
                  </div>
                  <div style="display:flex; flex-direction:column;">
                    <span style="font-weight:800; font-size:.9rem;">
                      {{ option.structured_formatting?.main_text || option.description }}
                    </span>
                    <span style="font-size:.8rem; opacity:.7;">
                      {{ option.structured_formatting?.secondary_text || '' }}
                    </span>
                  </div>
                </div>
              </template>
            </AutoComplete>

            <div v-if="isValidating" class="google-loading">
              <Icon name="svg-spinners:90-ring-with-bg" size="18" />
              <span>Verificando cobertura...</span>
            </div>

            <div
              v-if="tempGoogleSite?.status === 'checked' && !isValidating"
              class="result-card"
              :class="tempGoogleSite.in_coverage ? 'is-success' : 'is-error'"
            >
              <div class="result-header">
                <div class="status-icon">
                  <Icon :name="tempGoogleSite.in_coverage ? 'mdi:check-bold' : 'mdi:map-marker-off'" />
                </div>
                <div class="status-text">
                  <h4 style="margin:0;">
                    {{ tempGoogleSite.in_coverage ? '¡Estás en cobertura!' : 'Fuera de cobertura' }}
                  </h4>
                  <p style="margin:0; font-size:.85rem; opacity:.85;">
                    {{ tempGoogleSite.formatted_address }}
                  </p>
                </div>
              </div>

              <div v-if="tempGoogleSite.in_coverage" class="result-details">
                <div class="detail-row">
                  <span>Domicilio</span>
                  <strong>${{ formatPrice(tempGoogleSite.delivery_cost_cop) }}</strong>
                </div>

                <div class="detail-row full" v-if="tempGoogleSite.nearest?.site?.site_name">
                  <span>Te enviamos desde</span>
                  <strong>{{ tempGoogleSite.nearest.site.site_name }}</strong>
                </div>
              </div>

              <div v-else class="error-message">
                <p style="margin:0;">
                  {{ tempGoogleSite.error?.message_es || 'Fuera de cobertura' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Preview de sede si ya hay site -->
          <div
            class="image-preview fade-in"
            v-if="currenCity && currentSite?.site_id && tempGoogleSite?.in_coverage"
          >
            <div style="padding: 1rem;" class="image-overlay">
              <p class="site-info">
                <span class="brand">SALCHIMONSTER - </span>
                <span class="site">{{ currentSite?.site_name || 'Cargando...' }}</span>
              </p>
              <p class="delivery-info">
                Domicilio: ${{ formatPrice(tempGoogleSite?.delivery_cost_cop) }}
              </p>
            </div>

            <img
              :src="`${URI}/read-product-image/600/site-${currentSite?.site_id}`"
              class="site-img"
              style="aspect-ratio: 5/3; object-fit: cover;"
              @error="handleImageError"
            />
          </div>
        </template>

        <!-- ================== BARRIO (SIN GOOGLE) ================== -->
        <template v-else>
          <div v-if="currenCity" class="form-group fade-in">
            <label>¿Cuál es tu barrio?</label>

            <div class="custom-select">
              <Select
                v-model="currenNeigborhood"
                :options="possibleNeigborhoods"
                optionLabel="name"
                placeholder="Selecciona tu barrio"
                filter
                filterPlaceholder="Buscar barrio..."
                :disabled="!possibleNeigborhoods.length"
                :loading="spinnersView.barrio"
                class="pv-select"
              />
            </div>

            <span v-if="spinnersView.barrio" class="loader-mini-external"></span>
          </div>

          <div
            class="image-preview fade-in"
            v-if="currenCity && currenNeigborhood?.site_id"
          >
            <div style="padding: 1rem;" class="image-overlay">
              <p class="site-info">
                <span class="brand">SALCHIMONSTER - </span>
                <span class="site">{{ currentSite?.site_name || 'Cargando...' }}</span>
              </p>
              <p class="delivery-info">
                Domicilio: ${{ formatPrice(currenNeigborhood?.delivery_price) }}
              </p>
            </div>

            <img
              :src="`${URI}/read-product-image/600/site-${currenNeigborhood?.site_id}`"
              class="site-img"
              style="aspect-ratio: 5/3; object-fit: cover;"
              @error="handleImageError"
            />
          </div>
        </template>
      </div>
    </div>

    <template #footer>
      <button
        @click="confirmLocation"
        :disabled="!canSave"
        class="native-btn"
        :class="{ 'btn-disabled': !canSave }"
      >
        Confirmar Ubicación
      </button>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'

import { useSitesStore } from '@/stores/site'
import { URI } from '@/service/conection'

const store = useSitesStore()

// ================== GOOGLE API ==================
const uri_api_google = 'https://api.locations.salchimonster.com'
const googleSessionToken = ref('')

// ================== ESTADOS ==================
const spinnersView = ref({ ciudad: false, barrio: false })
const cities = ref([])
const city_disponibilidad = ref([])
const currenCity = ref(null)

const currenNeigborhood = ref(null)
const possibleNeigborhoods = ref([])
const currentSite = ref({})

const isReady = ref(false)
const skipCityWatch = ref(false)

// ================== GOOGLE AUTOCOMPLETE STATE ==================
const addressQuery = ref('')
const dirOptions = ref([])
const isValidating = ref(false)
const tempGoogleSite = ref(null)

// ================== COMPUTED ==================
const cityOptions = computed(() => {
  return [...cities.value]
    .filter(c => c.city_id != 15 && c.city_id != 18)
    .sort((a, b) => (a.city_name || '').localeCompare(b.city_name || ''))
})

const isGoogleMapsCity = computed(() => {
return true
})

const canSave = computed(() => {
  if (!currenCity.value) return false

  // ✅ GOOGLE: solo si ya seleccionó dirección y está en cobertura
  if (isGoogleMapsCity.value) {
    return !!tempGoogleSite.value?.in_coverage && !!tempGoogleSite.value?.nearest?.site?.site_id
  }

  // ✅ BARRIOS: como estaba
  const nb = currenNeigborhood.value
  if (!nb) return false
  return !!(nb.neighborhood_id || nb.id)
})

// ================== HELPERS ==================
const handleImageError = (e) => { e.target.style.display = 'none' }
const formatPrice = (v) => new Intl.NumberFormat('es-CO').format(v || 0)

const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// ================== CONFIRM ==================
const confirmLocation = () => {
  if (!canSave.value) return

  // ✅ GOOGLE MODE
  if (isGoogleMapsCity.value) {
    const site = tempGoogleSite.value?.nearest?.site
    const delivery = tempGoogleSite.value?.delivery_cost_cop || 0

    // Actualiza location (esto debería disparar tu watcher en checkout para hash redirect)
store.updateLocation(
  {
    city: currenCity.value,
    neigborhood: { name: 'Dirección (Google)', delivery_price: delivery },
    site
  },
  delivery
)

    // Guardar data google si luego la quieres usar (opcional)
    try {
      store.location.address_details = tempGoogleSite.value
      store.location.formatted_address = tempGoogleSite.value?.formatted_address || ''
      store.location.place_id = tempGoogleSite.value?.place_id || ''
      store.location.lat = tempGoogleSite.value?.lat
      store.location.lng = tempGoogleSite.value?.lng
    } catch {}

    store.setVisible('currentSite', false)
    return
  }

  // ✅ BARRIOS MODE (igual)
  store.updateLocation(
    { city: currenCity.value, neigborhood: currenNeigborhood.value, site: currentSite.value },
    currenNeigborhood.value?.delivery_price || 0
  )
  store.setVisible('currentSite', false)
}

// ================== APIs ==================
const getCities = async () => {
  spinnersView.value.ciudad = true
  try {
    cities.value = await (await fetch(`${URI}/cities`)).json()
  } finally {
    spinnersView.value.ciudad = false
  }
}

const getGoogleMapStatus = async () => {
  try {
    city_disponibilidad.value =
      (await (await fetch('https://api.locations.salchimonster.com/data/cities_google_map_status')).json()).data.cities
  } catch {}
}

const changePossiblesNeigborhoods = async () => {
  if (!currenCity.value?.city_id) { possibleNeigborhoods.value = []; return }
  spinnersView.value.barrio = true
  try {
    possibleNeigborhoods.value = await (await fetch(`${URI}/neighborhoods/by-city/${currenCity.value.city_id}`)).json()
  } finally {
    spinnersView.value.barrio = false
  }
}

// ================== GOOGLE AUTOCOMPLETE API ==================
const onGoogleComplete = async (event) => {
  const q = (event?.query || '').toString().trim()
  tempGoogleSite.value = null
  currentSite.value = {}

  if (!q) {
    dirOptions.value = []
    return
  }

  if (!googleSessionToken.value) googleSessionToken.value = generateUUID()

  const city = currenCity.value?.city_name || ''
  const params = new URLSearchParams({
    input: q,
    session_token: googleSessionToken.value,
    language: 'es',
    city,
    limit: '6'
  })

  try {
    const res = await (await fetch(`${uri_api_google}/co/places/autocomplete?${params}`)).json()
    const predictions = (res?.predictions || res || []).filter(p => p?.place_id)

    dirOptions.value = predictions.map(p => ({
      ...p,
      description: p.description || p.structured_formatting?.main_text || ''
    }))
  } catch {
    dirOptions.value = []
  }
}

const onGoogleSelect = async (event) => {
  const item = event?.value
  if (!item?.place_id) return

  isValidating.value = true
  currentSite.value = {}

  try {
    if (!googleSessionToken.value) googleSessionToken.value = generateUUID()

    const params = new URLSearchParams({
      place_id: item.place_id,
      session_token: googleSessionToken.value,
      language: 'es'
    })

    const details = await (await fetch(`${uri_api_google}/co/places/coverage-details?${params}`)).json()

    tempGoogleSite.value = {
      ...details,
      formatted_address: details.formatted_address || item.description,
      place_id: details.place_id || item.place_id,
      status: 'checked',
      in_coverage: !details.error && !!details.nearest?.in_coverage
    }

    // Si hay sede, la ponemos como preview
    if (tempGoogleSite.value?.nearest?.site?.site_id) {
      currentSite.value = tempGoogleSite.value.nearest.site
    }
  } catch {
    tempGoogleSite.value = {
      status: 'checked',
      in_coverage: false,
      formatted_address: item.description,
      error: { message_es: 'Error de conexión' }
    }
  } finally {
    isValidating.value = false
  }
}

// ================== LIFECYCLE + RESTORE ==================
onMounted(async () => {
  await Promise.all([getCities(), getGoogleMapStatus()])
  isReady.value = true

  if (store.location.city) {
    skipCityWatch.value = true
    currenCity.value = store.location.city
    skipCityWatch.value = false

    // Restore barrios
    if (!isGoogleMapsCity.value) {
      await changePossiblesNeigborhoods()
      if (store.location.neigborhood) {
        const wantedId = store.location.neigborhood.neighborhood_id || store.location.neigborhood.id
        const match = possibleNeigborhoods.value.find(n => (n.neighborhood_id || n.id) === wantedId)
        if (match) currenNeigborhood.value = match
      }
    } else {
      // Restore google (si existe)
      if (store.location.address_details?.formatted_address) {
        tempGoogleSite.value = {
          ...store.location.address_details,
          status: 'checked'
        }
        addressQuery.value = store.location.address_details.formatted_address
        if (store.location.site?.site_id) currentSite.value = store.location.site
      }
    }
  }
})

// Cuando cambia la ciudad, resetea barrio o google según aplique
watch(currenCity, async () => {
  if (!isReady.value || skipCityWatch.value) return

  // reset general
  currenNeigborhood.value = null
  currentSite.value = {}

  // reset google
  addressQuery.value = ''
  dirOptions.value = []
  tempGoogleSite.value = null
  googleSessionToken.value = ''

  if (isGoogleMapsCity.value) {
    possibleNeigborhoods.value = []
    return
  }

  await changePossiblesNeigborhoods()
})

// Cuando cambia el barrio, trae la sede
watch(currenNeigborhood, async (newVal) => {
  if (!newVal || isGoogleMapsCity.value || !newVal.site_id) {
    currentSite.value = {}
    return
  }

  try {
    const allSites = await (await fetch(`${URI}/sites`)).json()
    currentSite.value = allSites.find(s => s.site_id === newVal.site_id) || {}
  } catch {
    currentSite.value = { site_name: 'Sede' }
  }
})
</script>

<style scoped>
/* =========================
   Mantengo tus estilos y agrego los del AutoComplete
   ========================= */

.custom-select {
  position: relative;
  width: 100%;
  font-family: inherit;
  user-select: none;
}

/* PrimeVue Select look (igual que ya lo tienes) */
.custom-select :deep(.p-select) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  font-size: 0.95rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: #1f2937;
  width: 100%;
}

.custom-select :deep(.p-select:hover) {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.custom-select :deep(.p-select[aria-expanded="true"]) {
  border-color: #000;
  background: #fff;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.custom-select :deep(.p-select-overlay) {
  border: 1px solid #000;
  border-top: none;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
  overflow: hidden;
}

/* ✅ AutoComplete look similar */
.pv-ac { width: 100%; }
.pv-ac :deep(.p-autocomplete) { width: 100%; }
.pv-ac :deep(.p-autocomplete-input) {
  width: 100%;
  padding: 0.8rem 1rem;
  font-size: 0.95rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  color: #1f2937;
  outline: none;
}
.pv-ac :deep(.p-autocomplete-input:focus) {
  border-color: #000;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
}
.pv-ac :deep(.p-autocomplete-panel) {
  border: 1px solid #000;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
}
.pv-ac :deep(.p-autocomplete-items) { padding: 0; margin: 0; }
.pv-ac :deep(.p-autocomplete-item) {
  padding: .8rem 1rem;
  border-bottom: 1px solid #f3f4f6;
}
.pv-ac :deep(.p-autocomplete-item:hover) { background: #f3f4f6; }

/* Result card (compacto) */
.result-card { border: 1px solid #eee; border-radius: 10px; overflow: hidden; margin-top: .75rem; }
.result-card.is-success { border-color: #d1fae5; }
.result-card.is-error { border-color: #fee2e2; }
.result-header { padding: 1rem; display: flex; gap: 1rem; align-items: center; background: #f9fafb; }
.result-details { padding: 1rem; background: #fff; }
.detail-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.95rem; }
.detail-row.full { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed #eee; display: block; }
.error-message { padding: 1rem; color: #b91c1c; font-size: 0.9rem; background: #fff; }
.status-icon { width: 32px; height: 32px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; }

.google-loading {
  margin-top: .75rem;
  display: flex;
  align-items: center;
  gap: .5rem;
  opacity: .85;
}

.modal-body { padding: 0; display: flex; flex-direction: column; gap: 1.2rem; overflow-y: visible; }
.form-group label { font-weight: 700; font-size: 0.85rem; color: #374151; margin-bottom: 0.5rem; display: block; text-transform: uppercase; letter-spacing: 0.05em; }
.loader-mini-external { display: inline-block; width: 12px; height: 12px; border: 2px solid #ccc; border-top-color: #000; border-radius: 50%; animation: spin 1s infinite linear; margin-left: 5px; }

.image-preview { position: relative; width: 100%; border-radius: 12px; overflow: hidden; background: #eee; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
.image-preview img { width: 100%; height: 100%; object-fit: cover; }

.site-info { font-weight: 800; font-size: 1rem; margin: 0; text-transform: uppercase; }
.delivery-info { font-size: 0.85rem; margin: 0; opacity: 0.9; margin-top: 2px; }

.native-btn { background: #000; color: #fff; width: 100%; padding: 1rem; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; margin-top: 0.5rem; font-size: 1rem; transition: transform 0.1s; }
.native-btn:active { transform: scale(0.98); }
.native-btn.btn-disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

* { text-transform: uppercase; }
</style>
