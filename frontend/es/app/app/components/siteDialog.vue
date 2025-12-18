<template>
  <Teleport to="body">
    <div v-if="store.visibles.currentSite" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        
        <div class="modal-header">
          <h3>Selecciona tu ubicación</h3>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>

        <div class="modal-body">
          
          <div class="form-group">
            <label>¿En qué ciudad te encuentras?</label>
            
            <div class="custom-select" :class="{ 'is-open': showCityMenu }" ref="citySelectRef">
              <div class="select-trigger" @click="toggleCityMenu">
                <span>{{ currenCity ? currenCity.city_name : 'Selecciona una ciudad' }}</span>
                <span class="arrow-icon">▼</span>
              </div>

              <transition name="dropdown-fade">
                <div v-show="showCityMenu" class="select-dropdown">
                  <div class="dropdown-search-wrapper">
                    <input 
                      ref="cityInputRef"
                      v-model="cityQuery" 
                      type="text" 
                      class="dropdown-search-input" 
                      placeholder="Buscar ciudad..." 
                      @click.stop
                    />
                  </div>
                  
                  <ul class="dropdown-options">
                    <li 
                      v-for="city in filteredCities" 
                      :key="city.city_id" 
                      @click="selectCity(city)"
                      :class="{ 'selected': currenCity?.city_id === city.city_id }"
                    >
                      {{ city.city_name }}
                    </li>
                    <li v-if="filteredCities.length === 0" class="no-results">
                      No encontramos "{{ cityQuery }}"
                    </li>
                  </ul>
                </div>
              </transition>
            </div>
            <span v-if="spinnersView.ciudad" class="loader-mini-external"></span>
          </div>

          <div v-if="isGoogleMapsCity" class="google-maps-msg fade-in">
            <div class="map-icon-container">📍</div>
            <p>
              Para <strong>{{ currenCity?.city_name }}</strong> usaremos el mapa para ubicarte con precisión.
            </p>
          </div>

          <template v-else>
            <div v-if="currenCity" class="form-group fade-in">
              <label>¿Cuál es tu barrio?</label>

              <div class="custom-select" :class="{ 'is-open': showNbMenu, 'disabled': !possibleNeigborhoods.length }" ref="nbSelectRef">
                <div class="select-trigger" @click="toggleNbMenu">
                  <span>{{ getNbLabel() }}</span>
                  <span class="arrow-icon">▼</span>
                </div>

                <transition name="dropdown-fade">
                  <div v-show="showNbMenu && possibleNeigborhoods.length" class="select-dropdown">
                    <div class="dropdown-search-wrapper">
                      <input 
                        ref="nbInputRef"
                        v-model="nbQuery" 
                        type="text" 
                        class="dropdown-search-input" 
                        placeholder="Buscar barrio..." 
                        @click.stop
                      />
                    </div>

                    <ul class="dropdown-options">
                      <li 
                        v-for="nb in filteredNeighborhoods" 
                        :key="nb.neighborhood_id || nb.id" 
                        @click="selectNeighborhood(nb)"
                        :class="{ 'selected': isNbSelected(nb) }"
                      >
                        {{ nb.name }}
                      </li>
                      <li v-if="filteredNeighborhoods.length === 0" class="no-results">
                        No encontramos "{{ nbQuery }}"
                      </li>
                    </ul>
                  </div>
                </transition>
              </div>
               <span v-if="spinnersView.barrio" class="loader-mini-external"></span>
            </div>

            <div class="image-preview fade-in" v-if="currenCity && currenNeigborhood?.site_id && !currenNeigborhood._isDefault">
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
                  Domicilio: ${{ formatPrice(currenNeigborhood.delivery_price) }}
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
  </Teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { useSitesStore } from '@/stores/site'
import { URI } from '@/service/conection'

const store = useSitesStore()

// === ESTADOS ===
const spinnersView = ref({ ciudad: false, barrio: false })
const cities = ref([])
const city_disponibilidad = ref([])
const currenCity = ref(null)

const defaultNeighborhood = { _isDefault: true, name: 'Selecciona tu barrio' }
const currenNeigborhood = ref(defaultNeighborhood)
const possibleNeigborhoods = ref([])
const currentSite = ref({})

// === ESTADOS DEL CUSTOM SELECT ===
const showCityMenu = ref(false)
const showNbMenu = ref(false)
const cityQuery = ref('')
const nbQuery = ref('')

// Refs para el focus automático y click outside
const cityInputRef = ref(null)
const nbInputRef = ref(null)
const citySelectRef = ref(null)
const nbSelectRef = ref(null)

// === LOGICA DE APERTURA/CIERRE MENUS ===
const toggleCityMenu = () => {
  if (showCityMenu.value) {
    showCityMenu.value = false
  } else {
    showCityMenu.value = true
    showNbMenu.value = false // Cerrar el otro
    cityQuery.value = '' // Limpiar busqueda al abrir
    nextTick(() => cityInputRef.value?.focus())
  }
}

const toggleNbMenu = () => {
  if (!possibleNeigborhoods.value.length) return
  if (showNbMenu.value) {
    showNbMenu.value = false
  } else {
    showNbMenu.value = true
    showCityMenu.value = false // Cerrar el otro
    nbQuery.value = '' // Limpiar busqueda al abrir
    nextTick(() => nbInputRef.value?.focus())
  }
}

// Click Outside para cerrar los dropdowns
const handleClickOutside = (event) => {
  if (citySelectRef.value && !citySelectRef.value.contains(event.target)) {
    showCityMenu.value = false
  }
  if (nbSelectRef.value && !nbSelectRef.value.contains(event.target)) {
    showNbMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  Promise.all([getCities(), getGoogleMapStatus()])
  // Recuperar estado
  if (store.location.city) {
    currenCity.value = store.location.city
    if (!isGoogleMapsCity.value) {
      changePossiblesNeigborhoods().then(() => {
        if (store.location.neigborhood) {
          const match = possibleNeigborhoods.value.find(n => 
             (n.neighborhood_id && n.neighborhood_id === store.location.neigborhood.neighborhood_id) ||
             (n.id && n.id === store.location.neigborhood.id)
          )
          if (match) currenNeigborhood.value = match
        }
      })
    }
  }
})
onUnmounted(() => document.removeEventListener('click', handleClickOutside))


// === SELECCION ===
const selectCity = (city) => {
  currenCity.value = city
  showCityMenu.value = false
  onCityChange()
}

const selectNeighborhood = (nb) => {
  currenNeigborhood.value = nb
  showNbMenu.value = false
}

const getNbLabel = () => {
  if (!currenNeigborhood.value || currenNeigborhood.value._isDefault) return 'Selecciona tu barrio'
  return currenNeigborhood.value.name
}

const isNbSelected = (nb) => {
  if(currenNeigborhood.value._isDefault) return false
  return (nb.id || nb.neighborhood_id) === (currenNeigborhood.value.id || currenNeigborhood.value.neighborhood_id)
}

// === COMPUTED FILTROS ===
const norm = (s) => (s || '').toString().normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()

const filteredCities = computed(() => {
  const q = norm(cityQuery.value)
  const list = [...cities.value.filter(c => c.city_id != 15 && c.city_id != 18)].sort((a,b) => a.city_name.localeCompare(b.city_name))
  if (!q) return list
  return list.filter(c => norm(c.city_name).includes(q))
})

const filteredNeighborhoods = computed(() => {
  const q = norm(nbQuery.value)
  const list = [...possibleNeigborhoods.value].sort((a,b) => a.name.localeCompare(b.name))
  if (!q) return list
  return list.filter(n => norm(n.name).includes(q))
})

// === LOGICA NEGOCIO ===
const isGoogleMapsCity = computed(() => {
  const city_id = currenCity.value?.city_id
  if (!city_id) return false
  const status = city_disponibilidad.value?.find(s => Number(s.city_id) === Number(city_id))
  return status ? status.user_google_map_status : false
})

const canSave = computed(() => {
  if (!currenCity.value) return false
  if (isGoogleMapsCity.value) return true
  const nb = currenNeigborhood.value
  if (!nb || nb._isDefault) return false
  return !!(nb.neighborhood_id || nb.id)
})

const onCityChange = () => {
  currenNeigborhood.value = defaultNeighborhood
  currentSite.value = {}
  if (!isGoogleMapsCity.value) changePossiblesNeigborhoods()
}

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
  store.updateLocation({ city: currenCity.value, neigborhood: currenNeigborhood.value, site: currentSite.value }, currenNeigborhood.value.delivery_price || 0)
  store.setVisible('currentSite', false)
}

// APIs (Simplificadas)
const getCities = async () => {
  spinnersView.value.ciudad = true
  try { cities.value = await (await fetch(`${URI}/cities`)).json() } finally { spinnersView.value.ciudad = false }
}
const getGoogleMapStatus = async () => {
  try { city_disponibilidad.value = (await (await fetch('https://api.locations.salchimonster.com/data/cities_google_map_status')).json()).data.cities } catch {}
}
const changePossiblesNeigborhoods = async () => {
  if (!currenCity.value?.city_id) { possibleNeigborhoods.value = []; return }
  spinnersView.value.barrio = true
  try { possibleNeigborhoods.value = await (await fetch(`${URI}/neighborhoods/by-city/${currenCity.value.city_id}`)).json() } finally { spinnersView.value.barrio = false }
}

watch(currenNeigborhood, async (newVal) => {
  if (!isGoogleMapsCity.value && newVal && !newVal._isDefault && newVal.site_id) {
    try {
      const allSites = await (await fetch(`${URI}/sites`)).json()
      currentSite.value = allSites.find(s => s.site_id === newVal.site_id) || {}
    } catch { currentSite.value = { site_name: 'Sede' } }
  } else { currentSite.value = {} }
})
</script>

<style scoped>
/* =========================================
   CUSTOM SELECT STYLES (Bonitos)
   ========================================= */
.custom-select {
  position: relative;
  width: 100%;
  font-family: inherit;
  user-select: none;
}
.custom-select.disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* TRIGGER (El botón que se ve siempre) */
.select-trigger {
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
}
.select-trigger:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}
.is-open .select-trigger {
  border-color: #000;
  background: #fff;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}
.arrow-icon {
  font-size: 0.7rem;
  color: #6b7280;
  transition: transform 0.2s;
}
.is-open .arrow-icon {
  transform: rotate(180deg);
}

/* DROPDOWN (El contenedor que se abre) */
.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background: #ffffff;
  border: 1px solid #000;
  border-top: none;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
  z-index: 50;
  overflow: hidden;
}

/* BUSCADOR DENTRO DEL DROPDOWN */
.dropdown-search-wrapper {
  padding: 0.5rem;
  background: #fff;
  border-bottom: 1px solid #f3f4f6;
}
.dropdown-search-input {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  background: #f9fafb;
}
.dropdown-search-input:focus {
  border-color: #d1d5db;
  background: #fff;
}

/* LISTA DE OPCIONES */
.dropdown-options {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}
.dropdown-options li {
  padding: 0.7rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #374151;
  border-bottom: 1px solid #f9fafb;
  transition: background 0.1s;
}
.dropdown-options li:hover {
  background-color: #f3f4f6;
}
.dropdown-options li.selected {
  background-color: #f0fdf4; /* Verde muy claro */
  color: #166534;
  font-weight: 600;
}
.no-results {
  padding: 1rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.85rem;
  font-style: italic;
}

/* TRANSICIONES */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* =========================================
   ESTILOS GENERALES MODAL
   ========================================= */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(3px); }
.modal-container { background: white; width: 90%; max-width: 450px; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); display: flex; flex-direction: column; overflow: visible; /* Importante para que el dropdown salga si quiere */ max-height: 90vh; }
.modal-header { padding: 1.25rem 1.5rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; }
.modal-header h3 { margin: 0; font-size: 1.1rem; font-weight: 700; color: #111; }
.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.2rem; overflow-y: visible; /* Para que el dropdown no se corte */ }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; line-height: 1; }
.form-group label { font-weight: 700; font-size: 0.85rem; color: #374151; margin-bottom: 0.5rem; display: block; text-transform: uppercase; letter-spacing: 0.05em; }

/* Loader externo */
.loader-mini-external { display: inline-block; width: 12px; height: 12px; border: 2px solid #ccc; border-top-color: #000; border-radius: 50%; animation: spin 1s infinite linear; margin-left: 5px; }

/* Image Preview */
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