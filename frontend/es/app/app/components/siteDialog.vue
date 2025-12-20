<template>
  <div v-if="store.visibles.currentSite" class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">

      <div class="modal-header">
        <h3>Selecciona tu ubicación</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <div class="modal-body">

        <!-- CIUDAD -->
        <div class="form-group">
          <label>¿En qué ciudad te encuentras?</label>

          <div class="select-wrapper">
            <USelectMenu
              v-model="currentCity"
              :items="cities"
              :loading="cityStatus === 'pending'"
              label-key="city_name"
              placeholder="Selecciona una ciudad"
              :search-input="{ placeholder: 'Buscar ciudad...' }"
              :filter-fields="['city_name']"
              size="lg"
              class="w-full"
              :ui="{ trigger: 'min-h-[42px]' }"
              @update:open="onOpenCityMenu"
            >
              <!-- Trigger (lo que se ve cuando está cerrado) -->
              <template #default="{ modelValue }">
                <span v-if="modelValue" class="truncate">{{ modelValue.city_name }}</span>
                <span v-else class="text-gray-500">Selecciona una ciudad</span>
              </template>

              <!-- Label dentro del menú -->
              <template #item-label="{ item }">
                <span class="truncate">{{ item.city_name }}</span>
              </template>

              <template #empty="{ searchTerm }">
                <span class="text-sm text-gray-500">
                  {{ searchTerm ? 'No hay coincidencias.' : 'No hay ciudades disponibles.' }}
                </span>
              </template>
            </USelectMenu>

            <span v-if="cityStatus === 'pending'" class="loader-mini-external"></span>
          </div>
        </div>

        <!-- Mensaje Google Maps -->
        <div v-if="isGoogleMapsCity" class="google-maps-msg fade-in">
          <div class="map-icon-container">📍</div>
          <p>Para <strong>{{ currentCity?.city_name }}</strong> usaremos el mapa para ubicarte con precisión.</p>
        </div>

        <!-- BARRIO -->
        <template v-else>
          <div v-if="currentCity" class="form-group fade-in">
            <label>¿Cuál es tu barrio?</label>

            <div class="select-wrapper">
              <USelectMenu
                v-model="currentNeighborhood"
                :items="neighborhoods"
                :loading="neigStatus === 'pending'"
                label-key="name"
                placeholder="Selecciona tu barrio"
                :search-input="{ placeholder: 'Buscar barrio...' }"
                :filter-fields="['name']"
                :disabled="!neighborhoods.length || neigStatus === 'pending'"
                size="lg"
                class="w-full"
                :ui="{ trigger: 'min-h-[42px]' }"
              >
                <template #default="{ modelValue }">
                  <span v-if="modelValue" class="truncate">{{ modelValue.name }}</span>
                  <span v-else class="text-gray-500">Selecciona tu barrio</span>
                </template>

                <template #item-label="{ item }">
                  <span class="truncate">{{ item.name }}</span>
                </template>

                <template #empty="{ searchTerm }">
                  <span class="text-sm text-gray-500">
                    {{ searchTerm ? 'No hay coincidencias.' : 'No hay barrios disponibles.' }}
                  </span>
                </template>
              </USelectMenu>

              <span v-if="neigStatus === 'pending'" class="loader-mini-external"></span>
            </div>
          </div>

          <!-- Preview sede -->
          <div class="image-preview fade-in" v-if="showSitePreview">
            <img
              :src="`${URI}/read-product-image/600/site-${currentNeighborhood?.site_id}`"
              class="site-img"
              @error="handleImageError"
            />
            <div class="image-overlay">
              <p class="site-info">
                <span class="brand">SALCHIMONSTER - </span>
                <span class="site">{{ currentSite?.site_name || (sitesStatus === 'pending' ? 'Cargando...' : 'Sede') }}</span>
              </p>
              <p class="delivery-info">
                Domicilio: ${{ formatPrice(currentNeighborhood?.delivery_price) }}
              </p>
            </div>
          </div>
        </template>

        <!-- Confirmar -->
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
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { useSitesStore } from '@/stores/site'
import { URI } from '@/service/conection'

const store = useSitesStore()

// ===== STATE =====
const currentCity = ref(null)
const currentNeighborhood = ref(null)

const ensureBaseDataLoaded = async () => {
  if (!cities.value?.length && cityStatus.value !== 'pending') await fetchCities()
  if (!googleMapConfig.value?.length && gmStatus.value !== 'pending') await fetchGoogleConfig()
  // sites los cargamos solo si se necesita (cuando el usuario elige barrio)
}
// ===== Helpers =====
const formatPrice = (v) => new Intl.NumberFormat('es-CO').format(v || 0)
const handleImageError = (e) => { e.target.style.display = 'none' }
const closeModal = () => store.setVisible('currentSite', false)

// =======================================================
// CARGAS (Lazy) — se ejecutan cuando abres el modal
// =======================================================

const { data: cities, status: cityStatus, execute: fetchCities } = await useLazyFetch(
  () => `${URI}/cities`,
  {
    server: false,
    immediate: false,
    default: () => [],
    transform: (res) => {
      const raw = Array.isArray(res) ? res : (res?.data || [])
      return raw
        .filter(c => Number(c.city_id) !== 15 && Number(c.city_id) !== 18)
        .sort((a, b) => (a.city_name || '').localeCompare(b.city_name || ''))
    }
  }
)

const { data: googleMapConfig, status: gmStatus, execute: fetchGoogleConfig } = await useLazyFetch(
  () => `https://api.locations.salchimonster.com/data/cities_google_map_status`,
  {
    server: false,
    immediate: false,
    default: () => [],
    transform: (res) => res?.data?.cities || []
  }
)

const { data: sites, status: sitesStatus, execute: fetchSites } = await useLazyFetch(
  () => `${URI}/sites`,
  {
    server: false,
    immediate: false,
    default: () => [],
    transform: (res) => {
      const raw = Array.isArray(res) ? res : (res?.data || res?.sites || [])
      return raw
    }
  }
)

// Barrios dependen de la ciudad => useFetch reactivo
const { data: neighborhoods, status: neigStatus } = useFetch(
  () => {
    if (!currentCity.value?.city_id) return null
    if (isGoogleMapsCity.value) return null
    return `${URI}/neighborhoods/by-city/${currentCity.value.city_id}`
  },
  {
    server: false,
    lazy: true,
    default: () => [],
    watch: [currentCity, () => isGoogleMapsCity.value],
    transform: (res) => {
      const raw = Array.isArray(res) ? res : (res?.data || [])
      // Normaliza ID por si tu backend a veces manda neighborhood_id
      const mapped = raw.map(n => ({
        ...n,
        id: n.id ?? n.neighborhood_id
      }))
      return mapped.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    }
  }
)

// =======================================================
// COMPUTEDS
// =======================================================

const isGoogleMapsCity = false

const showSitePreview = computed(() => {
  return !!(currentCity.value && currentNeighborhood.value?.site_id)
})

const currentSite = computed(() => {
  const sid = currentNeighborhood.value?.site_id
  if (!sid || !sites.value?.length) return null
  return sites.value.find(s => Number(s.site_id) === Number(sid)) || null
})

const canSave = computed(() => {
  if (!currentCity.value) return false
  if (isGoogleMapsCity.value) return true
  return !!currentNeighborhood.value?.id
})

// =======================================================
// EVENTOS / WATCHERS
// =======================================================

// Cuando se abre el menú de ciudad, si no hay data, la trae
const onOpenCityMenu = async (open) => {
  if (!open) return
  await ensureBaseDataLoaded()
}

// Cuando ABRES el modal, también asegura data (esto es lo que te faltaba)
watch(
  () => store.visibles.currentSite,
  async (open) => {
    if (!open) return
    await ensureBaseDataLoaded()

    // Restaurar desde store si existe
    if (store.location?.city?.city_id && cities.value?.length && !currentCity.value) {
      const found = cities.value.find(c => Number(c.city_id) === Number(store.location.city.city_id))
      if (found) currentCity.value = found
    }

    // Restaurar barrio (si aplica y si existe)
    if (store.location?.neigborhood?.id && neighborhoods.value?.length && !isGoogleMapsCity.value) {
      const nb = neighborhoods.value.find(n => Number(n.id) === Number(store.location.neigborhood.id))
      if (nb) currentNeighborhood.value = nb
    }
  },
  { immediate: true }
)

// Cuando cambia la ciudad, limpia barrio
watch(currentCity, async (n, o) => {
  if (n?.city_id !== o?.city_id) {
    currentNeighborhood.value = null
  }
})

// Si se selecciona un barrio y aún no hemos cargado sedes, las cargamos para el preview
watch(currentNeighborhood, async (nb) => {
  if (nb?.site_id && !sites.value?.length && sitesStatus.value !== 'pending') {
    await fetchSites()
  }
})

// =======================================================
// FUNCIONES
// =======================================================
 
const confirmLocation = async () => {
  if (!canSave.value) return

  if (isGoogleMapsCity.value) {
    store.updateLocation({ city: currentCity.value, neigborhood: null, site: null }, 0)
    closeModal()
    return
  }

  // Asegura sites para guardar site completo
  if (currentNeighborhood.value?.site_id && !sites.value?.length) {
    await fetchSites()
  }

  store.updateLocation(
    {
      city: currentCity.value,
      neigborhood: currentNeighborhood.value,
      site: currentSite.value || null
    },
    currentNeighborhood.value?.delivery_price || 0
  )
  closeModal()
}
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(3px); }
.modal-container { background: white; width: 90%; max-width: 450px; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); display: flex; flex-direction: column; max-height: 90vh; }
.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.2rem; overflow-y: auto; overflow-x: visible; min-height: 300px; }
.modal-header { padding: 1.25rem 1.5rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; }
.modal-header h3 { margin: 0; font-size: 1.1rem; font-weight: 700; color: #111; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; line-height: 1; }

.form-group label { font-weight: 700; font-size: 0.85rem; color: #374151; margin-bottom: 0.5rem; display: block; text-transform: uppercase; letter-spacing: 0.05em; }
.select-wrapper { display: flex; align-items: center; gap: 8px; position: relative; }
.loader-mini-external { display: inline-block; width: 12px; height: 12px; border: 2px solid #ccc; border-top-color: #000; border-radius: 50%; animation: spin 1s infinite linear; flex-shrink: 0; }

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
