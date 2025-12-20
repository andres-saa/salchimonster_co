<template>
  <Dialog style="width: 30rem;" modal v-model:visible="store.visibles.currentSite">
    <div class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h3>Selecciona tu ubicación</h3>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>

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

          <div v-if="isGoogleMapsCity" class="google-maps-msg fade-in">
            <div class="map-icon-container">📍</div>
            <p>
              Para <strong>{{ currenCity?.city_name }}</strong> usaremos el mapa para ubicarte con precisión.
            </p>
          </div>

          <!-- ================== BARRIO ================== -->
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
              <img
                :src="`${URI}/read-product-image/600/site-${currenNeigborhood?.site_id}`"
                class="site-img"
                @error="handleImageError"
              />
              <div class="image-overlay">
                <p class="site-info">
                  <span class="brand">SALCHIMONSTER - </span>
                  <span class="site">{{ currentSite?.site_name || 'Cargando...' }}</span>
                </p>
                <p class="delivery-info">
                  Domicilio: ${{ formatPrice(currenNeigborhood?.delivery_price) }}
                </p>
              </div>
            </div>
          </template>

          <button
            @click="confirmLocation"
            :disabled="!canSave"
            class="native-btn"
            :class="{ 'btn-disabled': !canSave, 'btn-google': isGoogleMapsCity }"
          >
            {{ isGoogleMapsCity ? 'Ir al Mapa 🗺️' : 'Confirmar Ubicación' }}
          </button>
        </div>
      </div>
    </div>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import Select from 'primevue/select'
import { useSitesStore } from '@/stores/site'
import { URI } from '@/service/conection'

const store = useSitesStore()

// === ESTADOS ===
const spinnersView = ref({ ciudad: false, barrio: false })
const cities = ref([])
const city_disponibilidad = ref([])
const currenCity = ref(null)

const currenNeigborhood = ref(null)
const possibleNeigborhoods = ref([])
const currentSite = ref({})

const isReady = ref(false)
const skipCityWatch = ref(false)

// === COMPUTED ===
const cityOptions = computed(() => {
  return [...cities.value]
    .filter(c => c.city_id != 15 && c.city_id != 18)
    .sort((a, b) => (a.city_name || '').localeCompare(b.city_name || ''))
})

const isGoogleMapsCity = computed(() => {
  const city_id = currenCity.value?.city_id
  if (!city_id) return false
  const status = city_disponibilidad.value?.find(s => Number(s.city_id) === Number(city_id))
  return status ? !!status.user_google_map_status : false
})

const canSave = computed(() => {
  if (!currenCity.value) return false
  if (isGoogleMapsCity.value) return true
  const nb = currenNeigborhood.value
  if (!nb) return false
  return !!(nb.neighborhood_id || nb.id)
})

// === ACCIONES ===
const closeModal = () => store.setVisible('currentSite', false)
const handleImageError = (e) => { e.target.style.display = 'none' }
const formatPrice = (v) => new Intl.NumberFormat('es-CO').format(v || 0)

const confirmLocation = () => {
  if (!canSave.value) return

  if (isGoogleMapsCity.value) {
    store.updateLocation({ city: currenCity.value, neigborhood: null, site: null }, 0)
    store.setVisible('currentSite', false)
    return
  }

  store.updateLocation(
    { city: currenCity.value, neigborhood: currenNeigborhood.value, site: currentSite.value },
    currenNeigborhood.value?.delivery_price || 0
  )
  store.setVisible('currentSite', false)
}

// === APIs ===
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
    city_disponibilidad.value = (await (await fetch('https://api.locations.salchimonster.com/data/cities_google_map_status')).json()).data.cities
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

// === LIFECYCLE + RESTORE ===
onMounted(async () => {
  await Promise.all([getCities(), getGoogleMapStatus()])
  isReady.value = true

  if (store.location.city) {
    skipCityWatch.value = true
    currenCity.value = store.location.city
    skipCityWatch.value = false

    if (!isGoogleMapsCity.value) {
      await changePossiblesNeigborhoods()
      if (store.location.neigborhood) {
        const wantedId = store.location.neigborhood.neighborhood_id || store.location.neigborhood.id
        const match = possibleNeigborhoods.value.find(n => (n.neighborhood_id || n.id) === wantedId)
        if (match) currenNeigborhood.value = match
      }
    }
  }
})

// Cuando cambia la ciudad, resetea barrio y recarga si aplica
watch(currenCity, async () => {
  if (!isReady.value || skipCityWatch.value) return

  currenNeigborhood.value = null
  currentSite.value = {}

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
/* =========================================
   PRIMEVUE SELECT (Mismo look de tu custom)
   Usa clases oficiales de Select v4.
   ========================================= */

/* wrapper */
.custom-select {
  position: relative;
  width: 100%;
  font-family: inherit;
  user-select: none;
}

/* root */
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

/* abierto (Select usa aria-expanded según docs de accesibilidad) */
.custom-select :deep(.p-select[aria-expanded="true"]) {
  border-color: #000;
  background: #fff;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

/* label dentro */
.custom-select :deep(.p-select-label) {
  padding: 0;
  margin: 0;
  color: inherit;
}

/* icono flecha */
.custom-select :deep(.p-select-dropdown) {
  color: #6b7280;
  transition: transform 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.custom-select :deep(.p-select[aria-expanded="true"] .p-select-dropdown) {
  transform: rotate(180deg);
}

/* disabled */
.custom-select :deep(.p-select.p-disabled) {
  opacity: 0.6;
  pointer-events: none;
}

/* overlay panel */
.custom-select :deep(.p-select-overlay) {
  border: 1px solid #000;
  border-top: none;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
  overflow: hidden;
}

/* header (donde vive el filtro) */
.custom-select :deep(.p-select-header) {
  padding: 0.5rem;
  background: #fff;
  border-bottom: 1px solid #f3f4f6;
}

/* input filtro */
.custom-select :deep(.p-select-filter) {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  background: #f9fafb;
}

.custom-select :deep(.p-select-filter:focus) {
  border-color: #d1d5db;
  background: #fff;
}

/* lista */
.custom-select :deep(.p-select-list-container) {
  max-height: 200px;
  overflow-y: auto;
}

.custom-select :deep(.p-select-list) {
  padding: 0;
  margin: 0;
}

/* opciones */
.custom-select :deep(.p-select-option) {
  padding: 0.7rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #374151;
  border-bottom: 1px solid #f9fafb;
  transition: background 0.1s;
}

.custom-select :deep(.p-select-option:hover) {
  background-color: #f3f4f6;
}

/* seleccionado */
.custom-select :deep(.p-select-option[aria-selected="true"]),
.custom-select :deep(.p-select-option.p-highlight) {
  background-color: #f0fdf4;
  color: #166534;
  font-weight: 600;
}

/* empty message */
.custom-select :deep(.p-select-empty-message) {
  padding: 1rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.85rem;
  font-style: italic;
}

/* =========================================
   ESTILOS GENERALES MODAL (tus estilos)
   ========================================= */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(3px); }
.modal-container { background: white; width: 90%; max-width: 450px; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); display: flex; flex-direction: column; overflow: visible; max-height: 90vh; }
.modal-header { padding: 1.25rem 1.5rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; }
.modal-header h3 { margin: 0; font-size: 1.1rem; font-weight: 700; color: #111; }
.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.2rem; overflow-y: visible; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; line-height: 1; }
.form-group label { font-weight: 700; font-size: 0.85rem; color: #374151; margin-bottom: 0.5rem; display: block; text-transform: uppercase; letter-spacing: 0.05em; }

.loader-mini-external { display: inline-block; width: 12px; height: 12px; border: 2px solid #ccc; border-top-color: #000; border-radius: 50%; animation: spin 1s infinite linear; margin-left: 5px; }

.image-preview { position: relative; width: 100%; height: 140px; border-radius: 12px; overflow: hidden; background: #eee; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
.image-preview img { width: 100%; height: 100%; object-fit: cover; }
.image-overlay { position: absolute; bottom: 0; left: 0; width: 100%; background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); color: white; padding: 2rem 1rem 0.75rem; }
.site-info { font-weight: 800; font-size: 1rem; margin: 0; text-transform: uppercase; }
.delivery-info { font-size: 0.85rem; margin: 0; opacity: 0.9; margin-top: 2px; }

.google-maps-msg { text-align: center; padding: 1rem; background: #f0fdf4; border: 1px dashed #16a34a; border-radius: 8px; color: #166534; }
.map-icon-container { font-size: 2rem; margin-bottom: 0.5rem; }
.google-maps-msg p { margin: 0; font-size: 0.9rem; line-height: 1.4; }

.native-btn { background: #000; color: #fff; width: 100%; padding: 1rem; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; margin-top: 0.5rem; font-size: 1rem; transition: transform 0.1s; }
.native-btn:active { transform: scale(0.98); }
.native-btn.btn-disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
</style>
