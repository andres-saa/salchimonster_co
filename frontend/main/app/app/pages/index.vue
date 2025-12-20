<template>
  <div class="vicio-page">

    <Transition name="fade">
      <div v-if="isRedirecting" class="redirect-overlay">
        <div class="redirect-content">
          <div class="redirect-spinner">
            <Icon name="mdi:rocket-launch-outline" size="3em" class="rocket-icon" />
            <div class="pulse-ring"></div>
          </div>
          <h2 class="redirect-title">Te estamos llevando a</h2>
          <h3 class="redirect-store">{{ targetSiteName }}</h3>
          <p class="redirect-subtitle">Iniciando tu experiencia...</p>
        </div>
      </div>
    </Transition>

    <ClientOnly>
      <div id="vicio-map" class="vicio-map"></div>
    </ClientOnly>

    <div class="vicio-sidebar">
      <header class="sidebar-header">
        <h2 class="sidebar-title">
          ELIGE TU SALCHIMONSTER MÁS CERCANO
        </h2>

        <div class="city-select-wrapper">
          <label class="city-label" for="city-filter">Ciudad</label>

          <div class="filter-dd">
            <div class="filter-dd-control">
              <input
                id="city-filter"
                class="city-select-input"
                type="text"
                v-model="cityFilterText"
                :placeholder="'Todas las ciudades'"
                autocomplete="off"
                @focus="cityDdOpen = true"
                @input="cityDdOpen = true"
                @blur="closeCityDdSoon"
              />
              <button class="filter-dd-clear" v-if="selectedCityId" type="button" @mousedown.prevent @click="clearCity">
                <Icon name="mdi:close-circle" size="1.05em" />
              </button>
              <span class="city-select-arrow">
                <Icon name="mdi:chevron-down" size="1.2em" />
              </span>
            </div>

            <ul v-if="cityDdOpen" class="autocomplete-list dd-list">
              <li
                class="autocomplete-item"
                @mousedown.prevent
                @click="selectCity({ city_id: 0, city_name: 'Todas las ciudades' })"
              >
                <Icon name="mdi:earth" class="item-icon" />
                Todas las ciudades
              </li>

              <li
                v-for="city in filteredCities"
                :key="city.city_id"
                class="autocomplete-item"
                @mousedown.prevent
                @click="selectCity(city)"
              >
                <Icon name="mdi:city-variant-outline" class="item-icon" />
                {{ city.city_name }}
              </li>

              <li
                v-if="!filteredCities.length && cityFilterText.trim().length > 0"
                class="autocomplete-empty"
              >
                No se encontraron ciudades.
              </li>
            </ul>
          </div>
        </div>

        <div class="search-wrapper" v-if="selectedCityId && isGoogleCity">
          <input
            v-model="addressQuery"
            type="text"
            class="search-input"
            placeholder="Escribe tu dirección..."
            @input="onAddressInput"
            autocomplete="off"
          />
          <ul v-if="showSuggestions" class="autocomplete-list">
            <li
              v-for="s in suggestions"
              :key="s.place_id"
              class="autocomplete-item"
              @click="onSelectSuggestion(s)"
            >
              <Icon name="mdi:map-marker-outline" class="item-icon" />
              {{ s.description }}
            </li>
            <li
              v-if="!suggestions.length && addressQuery.trim().length > 0 && !loadingAutocomplete"
              class="autocomplete-empty"
            >
              No se encontraron resultados.
            </li>
            <li v-if="loadingAutocomplete" class="autocomplete-loading">
              Buscando…
            </li>
          </ul>
        </div>

        <div v-if="selectedCityId && isParamsCity" class="params-box">
          <div class="form-group">
            <label class="city-label">Barrio / Sector</label>

            <div class="filter-dd">
              <div class="filter-dd-control">
                <input
                  class="city-select-input"
                  type="text"
                  v-model="neighborhoodFilterText"
                  :placeholder="loadingNeighborhoods ? 'Cargando barrios...' : (neighborhoods.length ? 'Escribe para buscar...' : 'No hay barrios')"
                  autocomplete="off"
                  :disabled="loadingNeighborhoods || neighborhoods.length === 0"
                  @focus="nbDdOpen = true"
                  @input="nbDdOpen = true"
                  @blur="closeNbDdSoon"
                />
                <button
                  class="filter-dd-clear"
                  v-if="selectedNeighborhoodId"
                  type="button"
                  @mousedown.prevent
                  @click="clearNeighborhood"
                >
                  <Icon name="mdi:close-circle" size="1.05em" />
                </button>
                <span class="city-select-arrow">
                  <Icon name="mdi:chevron-down" size="1.2em" />
                </span>
              </div>

              <ul v-if="nbDdOpen" class="autocomplete-list dd-list">
                <li
                  v-for="nb in filteredNeighborhoods"
                  :key="String(nb.neighborhood_id || nb.id)"
                  class="autocomplete-item"
                  @mousedown.prevent
                  @click="selectNeighborhood(nb)"
                >
                  <Icon name="mdi:map-marker-radius-outline" class="item-icon" />
                  {{ nb.name }}
                </li>

                <li
                  v-if="!filteredNeighborhoods.length && neighborhoodFilterText.trim().length > 0 && !loadingNeighborhoods"
                  class="autocomplete-empty"
                >
                  No encontramos ese barrio.
                </li>

                <li v-if="loadingNeighborhoods" class="autocomplete-loading">
                  Cargando…
                </li>
              </ul>
            </div>
          </div>

          <div class="form-group" style="margin-top:.7rem;">
            <label class="city-label">Dirección exacta</label>
            <input
              v-model="paramExactAddress"
              type="text"
              class="search-input"
              placeholder="Ej: Calle 123 # 45 - 67..."
              autocomplete="off"
            />
          </div>
        </div>
      </header>

      <section v-if="coverageResult && isGoogleCity" class="coverage-card">
        <div class="coverage-header">
          <Icon name="mdi:map-marker-check" size="1.4em" class="coverage-icon" />
          <h3 class="coverage-title">Resultado de búsqueda</h3>
        </div>
        <div class="coverage-body">
          <div class="coverage-row">
            <span class="coverage-label">Dirección:</span>
            <span class="coverage-value address-text">{{ coverageResult.formatted_address }}</span>
          </div>
          <div class="coverage-row">
            <span class="coverage-label">Sede más cercana:</span>
            <span class="coverage-value">
              {{ coverageResult.nearest?.site?.site_name || 'N/A' }}
              <small v-if="coverageResult.nearest">
                ({{ coverageResult.nearest.distance_km.toFixed(1) }} km)
              </small>
            </span>
          </div>
          <div class="coverage-row highlight">
            <span class="coverage-label">Costo envío:</span>
            <span class="coverage-value price">{{ formatCOP(coverageResult.delivery_cost_cop) }}</span>
          </div>
          <div class="coverage-status-text" :class="coverageResult.nearest?.in_coverage ? 'text-ok' : 'text-fail'">
            {{ coverageResult.nearest?.in_coverage ? '✅ Cubrimos tu zona' : '❌ Fuera de zona de entrega' }}
          </div>
        </div>
        <div class="coverage-actions" v-if="coverageResult.nearest">
          <button
            v-if="coverageResult.nearest?.in_coverage && getExactOrderType(coverageResult.nearest.site.site_id, 3)"
            class="btn-action btn-delivery"
            @click="dispatchToSite(
              getStoreById(coverageResult.nearest.site.site_id) || coverageResult.nearest.site,
              getExactOrderType(coverageResult.nearest.site.site_id, 3),
              { mode: 'gmaps', coverageData: coverageResult, city: selectedCityObj }
            )"
          >
            <Icon name="mdi:moped" size="1.2em" />
            Domicilio
          </button>
        </div>
      </section>

      <section v-if="isParamsCity && selectedNeighborhoodObj" class="coverage-card">
        <div class="coverage-header">
          <Icon name="mdi:home-map-marker" size="1.4em" class="coverage-icon" />
          <h3 class="coverage-title">Tu zona (Por Barrios)</h3>
        </div>
        <div class="coverage-body">
          <div class="coverage-row">
            <span class="coverage-label">Barrio:</span>
            <span class="coverage-value">{{ selectedNeighborhoodObj?.name || '—' }}</span>
          </div>
          <div class="coverage-row highlight">
            <span class="coverage-label">Costo envío:</span>
            <span class="coverage-value price">{{ formatCOP(paramDeliveryPrice) }}</span>
          </div>
          <div class="coverage-status-text text-ok">
            ✅ Listo para enviar
          </div>
        </div>
        <div class="coverage-actions">
          <button
            class="btn-action btn-delivery"
            :disabled="!canDispatchParams"
            @click="onDispatchParamsDelivery"
          >
            <Icon name="mdi:moped" size="1.2em" />
            Domicilio
          </button>
        </div>
      </section>

      <main class="stores-list">
        <article
          v-for="store in filteredStores"
          :key="store.id"
          class="store-item"
          :class="{ 'store-item--active': store.id === selectedStoreId }"
          @click="openModal(store)"
        >
          <div class="store-img-wrapper">
            <img
              :src="currentImage(store)"
              @load="loadHighResImage(store)"
              @error="onImgError(store)"
              class="store-img"
              alt="Foto sede"
            />
          </div>
          <div class="store-info">
            <h3 class="store-name">{{ store.name }}</h3>
            <p class="store-services">
              <span v-for="(ot, index) in getAvailableOrderTypes(store.id)" :key="ot.id">
                {{ ot.name.toUpperCase() }}
                <span v-if="index < getAvailableOrderTypes(store.id).length - 1"> | </span>
              </span>
            </p>
            <p class="store-address">
              {{ store.address }} – {{ store.city }}
            </p>
            <button class="store-action" :data-status="store.status || 'unknown'">
              <span v-if="store.status === 'open'" class="status-flex">
                <Icon name="mdi:check-circle-outline" size="1.1em" /> Abierto
              </span>
              <span v-else class="status-flex">Cerrado</span>
            </button>
          </div>
          <button class="store-arrow">
            <Icon name="mdi:chevron-right" size="1.6em" />
          </button>
        </article>
      </main>
    </div>

    <div v-if="isModalOpen && modalStore" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <button class="modal-close-btn" @click="closeModal">
          <Icon name="mdi:close" size="1.5em" />
        </button>

        <div v-if="modalStep === 1">
          <h3 class="modal-title">¿Cómo quieres tu pedido?</h3>
          <p class="modal-subtitle">Sede: <strong>{{ modalStore.name }}</strong></p>

          <div class="modal-actions">
            <button
              v-for="ot in getAvailableOrderTypes(modalStore.id)"
              :key="ot.id"
              class="modal-btn"
              :class="getButtonClass(ot.id)"
              @click="handleModalOption(ot)"
            >
              <div class="btn-icon-circle">
                <Icon :name="getIconForOrderType(ot.id)" size="1.8em" />
              </div>
              <span>{{ ot.name }}</span>
              <small v-if="ot.id === 3">
                {{ isGoogleCity ? 'Ingresa dirección' : 'Selecciona barrio' }}
              </small>
              <small v-if="ot.id === 2">Pasas por él</small>
            </button>
          </div>
        </div>

        <div v-else-if="modalStep === 2">
          <div class="modal-header-nav">
            <button class="modal-back-btn" @click="setModalStep(1)">
              <Icon name="mdi:arrow-left" size="1.2em" /> Volver
            </button>
          </div>

          <div v-if="isGoogleCity">
            <h3 class="modal-title">¿Dónde estás?</h3>
            <div class="search-wrapper modal-search">
              <input
                v-model="modalAddressQuery"
                type="text"
                class="search-input"
                placeholder="Calle 123 # 45 - 67..."
                @input="onModalAddressInput"
                autocomplete="off"
                ref="modalInputRef"
              />
              <ul v-if="modalShowSuggestions" class="autocomplete-list">
                <li v-for="s in modalSuggestions" :key="s.place_id" class="autocomplete-item" @click="onSelectModalSuggestion(s)">
                  <Icon name="mdi:map-marker-outline" class="item-icon" />{{ s.description }}
                </li>
                <li v-if="!modalSuggestions.length && modalAddressQuery.trim() && !modalLoadingAutocomplete" class="autocomplete-empty">
                  Sin resultados.
                </li>
                <li v-if="modalLoadingAutocomplete" class="autocomplete-loading">Buscando...</li>
              </ul>
            </div>
            <div v-if="modalAddressError" class="modal-error">{{ modalAddressError }}</div>
          </div>

          <div v-else class="params-flow-modal">
            <h3 class="modal-title">Datos de Entrega</h3>

            <div class="form-group relative">
              <label class="city-label">Busca tu Barrio</label>
              <input
                type="text"
                class="search-input"
                v-model="modalNeighborhoodSearch"
                placeholder="Escribe para buscar..."
                @focus="modalShowNbList = true"
                @blur="setTimeout(() => modalShowNbList = false, 200)"
              />
              <ul v-if="modalShowNbList && modalFilteredNeighborhoods.length" class="autocomplete-list">
                <li
                  v-for="nb in modalFilteredNeighborhoods"
                  :key="nb.id || nb.neighborhood_id"
                  class="autocomplete-item"
                  @click="onSelectModalNeighborhood(nb)"
                >
                  {{ nb.name }}
                </li>
              </ul>
              <div v-if="modalShowNbList && !modalFilteredNeighborhoods.length" class="autocomplete-list">
                <li class="autocomplete-empty">No encontramos ese barrio</li>
              </div>
            </div>

            <div v-if="modalSelectedNeighborhood" class="selected-nb-info">
              <div class="info-row">
                <span>Barrio:</span>
                <strong>{{ modalSelectedNeighborhood.name }}</strong>
              </div>
              <div class="info-row">
                <span>Domicilio:</span>
                <strong class="text-green">{{ formatCOP(modalSelectedNeighborhood.delivery_price) }}</strong>
              </div>
            </div>

            <div class="form-group" style="margin-top: 1rem;">
              <label class="city-label">Dirección Exacta</label>
              <input
                v-model="modalParamAddress"
                type="text"
                class="search-input"
                placeholder="Ej: Calle 123 # 45 - 67 Apt 201"
              />
            </div>

            <button
              class="btn-action btn-delivery full-width"
              style="margin-top: 1.5rem;"
              :disabled="!modalSelectedNeighborhood || !modalParamAddress.trim()"
              @click="onDispatchModalParams"
            >
              Confirmar Domicilio
            </button>
          </div>
        </div>

        <div v-else-if="modalStep === 3" class="modal-loading-view">
          <Icon name="mdi:loading" size="3em" class="spin-icon" />
          <p>Validando cobertura...</p>
        </div>

        <div v-else-if="modalStep === 4 && modalCoverageResult">
           <div class="modal-header-nav">
            <button class="modal-back-btn" @click="setModalStep(2)">
              <Icon name="mdi:arrow-left" size="1.2em" /> Volver
            </button>
          </div>
          
          <h3 class="modal-title">Resumen de Cobertura</h3>
          
          <div class="coverage-card" style="margin: 1rem 0; width: auto; border: none; box-shadow: none; background: transparent;">
             <div class="coverage-body" style="padding: 0; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem;">
                
                <div class="coverage-row">
                  <span class="coverage-label">Dirección:</span>
                  <span class="coverage-value address-text">{{ modalCoverageResult.formatted_address }}</span>
                </div>

                <div class="coverage-row">
                  <span class="coverage-label">Sede asignada:</span>
                  <span class="coverage-value">
                      {{ modalCoverageResult.nearest?.site?.site_name || 'N/A' }}
                      <small v-if="modalCoverageResult.nearest">
                        ({{ modalCoverageResult.nearest.distance_km.toFixed(1) }} km)
                      </small>
                   </span>
                </div>

                <div class="coverage-row highlight">
                  <span class="coverage-label">Costo envío:</span>
                  <span class="coverage-value price">{{ formatCOP(modalCoverageResult.delivery_cost_cop) }}</span>
                </div>

                <div class="coverage-status-text" :class="modalCoverageResult.nearest?.in_coverage ? 'text-ok' : 'text-fail'">
                  {{ modalCoverageResult.nearest?.in_coverage ? '✅ Cubrimos tu zona' : '❌ Fuera de zona de entrega' }}
                </div>
             </div>
          </div>

          <button
             class="btn-action btn-delivery full-width"
             style="margin-top: 1rem;"
             :disabled="!modalCoverageResult.nearest?.in_coverage"
             @click="confirmGoogleDispatch"
          >
             <Icon name="mdi:check-circle-outline" size="1.2em" />
             Confirmar e Ir
          </button>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import 'leaflet/dist/leaflet.css'

/* =======================
   CONFIG & STATE
   ======================= */
const route = useRoute()
const BACKEND_BASE = 'https://backend.salchimonster.com'
const LOCATIONS_BASE = 'https://api.locations.salchimonster.com'
const URI = 'https://backend.salchimonster.com'
const MAIN_DOMAIN = 'salchimonster.com'

const map = ref<any>(null)
const leafletModule = ref<any>(null)
const markers = ref<Record<number, any>>({})
const mapBounds = ref<any>(null)
const initialBounds = ref<any>(null)

const stores = ref<any[]>([])
const cities = ref<any[]>([])
const sitePaymentsConfig = ref<any[]>([])
const cityMapStatus = ref<any[]>([])

const selectedCityId = ref<number>(0)
const selectedStoreId = ref<number | null>(null)
const sessionToken = ref(typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2))
const isRedirecting = ref(false)
const targetSiteName = ref('')

/* =======================
   SIDEBAR - DROPDOWNS CON FILTRO
   ======================= */
const cityFilterText = ref('')
const cityDdOpen = ref(false)
let closeCityDdTimer: any = null

const neighborhoodFilterText = ref('')
const nbDdOpen = ref(false)
let closeNbDdTimer: any = null

function closeCityDdSoon() {
  if (closeCityDdTimer) clearTimeout(closeCityDdTimer)
  closeCityDdTimer = setTimeout(() => (cityDdOpen.value = false), 200)
}
function closeNbDdSoon() {
  if (closeNbDdTimer) clearTimeout(closeNbDdTimer)
  closeNbDdTimer = setTimeout(() => (nbDdOpen.value = false), 200)
}

function clearCity() {
  selectedCityId.value = 0
  cityFilterText.value = ''
  cityDdOpen.value = false
  onCityChange()
}

function clearNeighborhood() {
  selectedNeighborhoodId.value = ''
  neighborhoodFilterText.value = ''
  nbDdOpen.value = false
}

const orderedCities = computed(() => {
  return [...cities.value.filter((s: any) => ![18, 15, 19].includes(s.city_id))]
    .sort((a: any, b: any) => (a.index ?? 0) - (b.index ?? 0))
})

const filteredCities = computed(() => {
  const q = cityFilterText.value.trim().toLowerCase()
  if (!q) return orderedCities.value
  return orderedCities.value.filter((c: any) => (c.city_name || '').toLowerCase().includes(q))
})

function selectCity(city: any) {
  cityDdOpen.value = false
  if (Number(city.city_id) === 0) {
    selectedCityId.value = 0
    cityFilterText.value = ''
  } else {
    selectedCityId.value = Number(city.city_id)
    cityFilterText.value = city.city_name
  }
  onCityChange()
}

/* =======================
   Google Sidebar
   ======================= */
const addressQuery = ref('')
const suggestions = ref<any[]>([])
const loadingAutocomplete = ref(false)
const showSuggestions = ref(false)
const coverageResult = ref<any | null>(null)
const dropoffMarker = ref<any | null>(null)
let dropoffIcon: any = null

/* =======================
   Barrios Sidebar
   ======================= */
const neighborhoods = ref<any[]>([])
const loadingNeighborhoods = ref(false)
const selectedNeighborhoodId = ref<string>('')
const paramExactAddress = ref('')

const selectedNeighborhoodObj = computed(() => {
  if (!selectedNeighborhoodId.value) return null
  const id = String(selectedNeighborhoodId.value)
  return neighborhoods.value.find((n: any) => String(n.neighborhood_id || n.id) === id) || null
})
const paramDeliveryPrice = computed(() => Number(selectedNeighborhoodObj.value?.delivery_price ?? 0))

const filteredNeighborhoods = computed(() => {
  const base = neighborhoods.value || []
  const q = neighborhoodFilterText.value.trim().toLowerCase()
  if (!q) return base
  return base.filter((n: any) => (n.name || '').toLowerCase().includes(q))
})

function selectNeighborhood(nb: any) {
  const id = String(nb.neighborhood_id || nb.id)
  selectedNeighborhoodId.value = id
  neighborhoodFilterText.value = nb.name
  nbDdOpen.value = false
}

const paramAssignedStore = computed(() => {
  const nb = selectedNeighborhoodObj.value
  if (!nb?.site_id) return null
  return getStoreById(Number(nb.site_id)) || null
})

const canDispatchParams = computed(() => {
  if (!isParamsCity.value) return false
  if (!selectedNeighborhoodObj.value) return false
  if (!paramExactAddress.value.trim()) return false
  const store = paramAssignedStore.value
  if (!store) return false
  return !!getExactOrderType(store.id, 3)
})

/* =======================
   MODAL STATE
   ======================= */
const isModalOpen = ref(false)
const modalStore = ref<any | null>(null)
const modalStep = ref(1)

// Google Modal State
const modalAddressQuery = ref('')
const modalSuggestions = ref<any[]>([])
const modalLoadingAutocomplete = ref(false)
const modalShowSuggestions = ref(false)
const modalAddressError = ref('')
const modalInputRef = ref<HTMLInputElement | null>(null)
// NUEVO: Para guardar el resultado intermedio en el modal
const modalCoverageResult = ref<any>(null)

// Barrios Modal State
const modalNeighborhoodSearch = ref('')
const modalShowNbList = ref(false)
const modalSelectedNeighborhood = ref<any>(null)
const modalParamAddress = ref('')

/* =======================
   HELPERS & COMPUTED
   ======================= */
const selectedCityObj = computed(() => cities.value.find((c: any) => Number(c.city_id) === Number(selectedCityId.value)) || null)

function isGoogleMapsEnabled(cityId: number) {
  const config = cityMapStatus.value.find((c: any) => Number(c.city_id) === Number(cityId))
  return config ? !!config.user_google_map_status : false
}

const isGoogleCity = computed(() => {
  const cityId = modalStore.value ? (modalStore.value.cityId || modalStore.value.city_id) : selectedCityId.value
  return !!cityId && isGoogleMapsEnabled(Number(cityId))
})
const isParamsCity = computed(() => !isGoogleCity.value)

const modalFilteredNeighborhoods = computed(() => {
  if (!modalNeighborhoodSearch.value) return neighborhoods.value
  const q = modalNeighborhoodSearch.value.toLowerCase()
  return neighborhoods.value.filter((n: any) => (n.name || '').toLowerCase().includes(q))
})

/* =======================
   MODAL LOGIC
   ======================= */
async function openModal(store: any) {
  modalStore.value = store
  modalStep.value = 1
  isModalOpen.value = true

  modalAddressQuery.value = ''
  modalSuggestions.value = []
  modalCoverageResult.value = null // Resetear resultado previo

  modalNeighborhoodSearch.value = ''
  modalSelectedNeighborhood.value = null
  modalParamAddress.value = ''
  modalShowNbList.value = false

  const cityId = store.cityId || store.city_id
  if (cityId && !isGoogleMapsEnabled(cityId)) {
    if (neighborhoods.value.length === 0 || selectedCityId.value !== cityId) {
      await loadNeighborhoodsByCity(cityId)
    }
  }
}

async function handleModalOption(orderType: any) {
  if (Number(orderType.id) === 3) {
    const cityId = modalStore.value.cityId || modalStore.value.city_id

    if (isGoogleMapsEnabled(Number(cityId))) {
      setModalStep(2)
      return
    }

    if (neighborhoods.value.length === 0) {
      await loadNeighborhoodsByCity(cityId)
    }
    setModalStep(2)
    return
  }

  dispatchToSite(modalStore.value, orderType, { mode: 'simple', city: selectedCityObj.value })
}

function onSelectModalNeighborhood(nb: any) {
  modalSelectedNeighborhood.value = nb
  modalNeighborhoodSearch.value = nb.name
  modalShowNbList.value = false
}

function onDispatchModalParams() {
  if (!modalSelectedNeighborhood.value || !modalParamAddress.value.trim()) return

  const assignedSiteId = modalSelectedNeighborhood.value.site_id
  let targetStore = getStoreById(Number(assignedSiteId))
  if (!targetStore) targetStore = modalStore.value

  const ot = getExactOrderType(targetStore.id, 3)
  if (!ot) {
    alert('La sede asignada a este barrio no tiene servicio de domicilio activo.')
    return
  }

  dispatchToSite(targetStore, ot, {
    mode: 'params',
    city: cities.value.find((c: any) => c.city_id == targetStore.cityId),
    neighborhood: modalSelectedNeighborhood.value,
    exactAddress: modalParamAddress.value
  })
}

function closeModal() { isModalOpen.value = false; modalStore.value = null }
function setModalStep(step: number) {
  modalStep.value = step
  if (step === 2 && isGoogleCity.value) nextTick(() => modalInputRef.value?.focus())
}

/* =======================
   API LOADERS
   ======================= */
async function loadPaymentConfig() {
  try {
    const res = await fetch(`${URI}/site-payments-complete`)
    sitePaymentsConfig.value = await res.json()
  } catch (e) { console.error('Error loading payment config', e) }
}

async function loadCityMapStatus() {
  try {
    const res = await fetch(`${LOCATIONS_BASE}/data/cities_google_map_status`)
    const data = await res.json()
    cityMapStatus.value = data.data.cities || []
  } catch (e) { console.error('Error loading city map status', e) }
}

async function loadCities() {
  try {
    const res = await fetch(`${BACKEND_BASE}/cities`)
    cities.value = (await res.json()).filter((c: any) => c.visible !== false)
  } catch {}
}

async function loadStores() {
  try {
    const res = await fetch(`${BACKEND_BASE}/sites`)
    const data = await res.json()
    stores.value = data
      .filter((s: any) => s.show_on_web && s.time_zone === 'America/Bogota' && s.site_id != 32)
      .map((s: any) => ({
        id: s.site_id,
        name: `SALCHIMONSTER ${s.site_name}`,
        city: s.city_name,
        cityId: s.city_id,
        address: s.site_address || 'Dirección pendiente',
        lat: s.location?.[0] || 4.0,
        lng: s.location?.[1] || -74.0,
        subdomain: s.subdomain,
        img_id: s.img_id
      }))
  } catch {}
}

async function loadStatuses() {
  const promises = stores.value.map(async (s) => {
    try {
      const res = await fetch(`${BACKEND_BASE}/site/${s.id}/status`)
      const d = await res.json()
      s.status = d.status
    } catch {
      if (!s.status) s.status = 'unknown'
    }
  })
  await Promise.all(promises)
}

/* =======================
   ORDER TYPES
   ======================= */
function getAvailableOrderTypes(siteId: number) {
  const config = sitePaymentsConfig.value.find((s: any) => String(s.site_id) === String(siteId))
  if (!config || !config.order_types) return []
  return config.order_types.filter((ot: any) => ot.methods && ot.methods.length > 0)
}
function getExactOrderType(siteId: number, typeId: number) {
  const available = getAvailableOrderTypes(siteId)
  return available.find((ot: any) => Number(ot.id) === Number(typeId)) || null
}
function getIconForOrderType(id: number) {
  if (id === 3) return 'mdi:moped'
  if (id === 2) return 'mdi:shopping-outline'
  if (id === 6) return 'mdi:silverware-fork-knife'
  return 'mdi:star'
}
function getButtonClass(id: number) {
  if (id === 3) return 'modal-btn--delivery'
  return 'modal-btn--pickup'
}

/* =======================
   DISPATCH
   ======================= */
type DispatchExtra =
  | { mode: 'gmaps', coverageData: any, city?: any }
  | { mode: 'params', city?: any, neighborhood: any, exactAddress: string }
  | { mode: 'simple', city?: any }
  | any

async function dispatchToSite(manualStore: any, orderTypeObj: any, extra: DispatchExtra = { mode: 'simple' }) {
  isRedirecting.value = true
  let targetStore = manualStore
  targetSiteName.value = targetStore?.name || targetStore?.site_name || 'Nueva Sede'
  const targetCityId = targetStore.cityId || targetStore.city_id
  const useGoogleMaps = isGoogleMapsEnabled(Number(targetCityId))
  const isDelivery = Number(orderTypeObj?.id) === 3

  try {
    const hash = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36).substring(2)
    let userSiteData: any = null
    let finalAddress = ''
    let finalLat = 0
    let finalLng = 0
    let finalPlaceId = ''

    if (isDelivery && useGoogleMaps && extra?.mode === 'gmaps' && extra?.coverageData) {
      const coverageData = extra.coverageData
      userSiteData = {
        ...coverageData,
        delivery_cost_cop: coverageData.delivery_cost_cop || 0,
        formatted_address: coverageData.formatted_address
      }
      finalAddress = coverageData.formatted_address || ''
      finalLat = coverageData.lat || 0
      finalLng = coverageData.lng || 0
      finalPlaceId = coverageData.place_id || ''
    }

    if (isDelivery && !useGoogleMaps && extra?.mode === 'params' && extra?.neighborhood) {
      const nb = extra.neighborhood
      finalAddress = (extra.exactAddress || '').toString()
      userSiteData = {
        formatted_address: finalAddress,
        delivery_cost_cop: Number(nb.delivery_price ?? 0),
        neighborhood: {
          ...nb,
          neighborhood_id: nb.neighborhood_id || nb.id,
          name: nb.name,
          site_id: nb.site_id,
          delivery_price: Number(nb.delivery_price ?? 0),
        },
        nearest: {
          in_coverage: true,
          distance_km: 0,
          site: {
            site_id: targetStore.id || targetStore.site_id,
            site_name: (targetStore.name || targetStore.site_name || '').replace('SALCHIMONSTER ', ''),
            subdomain: targetStore.subdomain,
            city_id: targetCityId,
            city: targetStore.city,
            site_address: targetStore.address
          }
        }
      }
    }

    const payload: any = {
      user: {
        name: '',
        neigborhood: '',
        payment_method_option: '',
        phone_number: '',
        site: userSiteData,
        address: finalAddress,
        lat: finalLat,
        lng: finalLng,
        place_id: finalPlaceId,
        order_type: orderTypeObj,
        phone_code: { code: "CO", name: "Colombia", dialCode: "+57", flag: "https://flagcdn.com/h20/co.png", label: "+57", dialDigits: "57" }
      },
      location_meta: {
        city: extra?.city || null,
        neigborhood: extra?.mode === 'params'
          ? {
              ...extra.neighborhood,
              neighborhood_id: extra.neighborhood.neighborhood_id || extra.neighborhood.id,
              name: extra.neighborhood.name,
              site_id: extra.neighborhood.site_id,
              delivery_price: Number(extra.neighborhood.delivery_price ?? 0),
            }
          : null
      },
      cart: [],
      site_location: {
        site_id: targetStore.id || targetStore.site_id,
        site_name: (targetStore.name || targetStore.site_name || '').replace('SALCHIMONSTER ', ''),
        site_address: targetStore.address,
        subdomain: targetStore.subdomain,
        city: targetStore.city
      },
      timestamp: Date.now()
    }

    const res = await fetch(`${URI}/data/${hash}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error('Error saving session')

    const subdomain = targetStore.subdomain || 'www'
    const isDev = window.location.hostname.includes('localhost')
    const protocol = window.location.protocol
    const baseUrl = isDev ? `${protocol}//${subdomain}.localhost:3000` : `https://${subdomain}.${MAIN_DOMAIN}`
    
    // ============================================
    // LÓGICA AGREGADA PARA PRESERVAR QUERY PARAMS
    // ============================================
    const params = new URLSearchParams()
    
    // Hash obligatorio
    params.append('hash', hash)

    // Agregamos inserted_by y token si existen en la URL actual
    if (route.query.inserted_by) {
      params.append('inserted_by', String(route.query.inserted_by))
    }
    if (route.query.token) {
      params.append('token', String(route.query.token))
    }

        if (route.query.iframe) {
      params.append('iframe', String(route.query.iframe))
    }

    // Redirección final
    window.location.href = `${baseUrl}/?${params.toString()}`

  } catch (error) {
    console.error(error)
    isRedirecting.value = false
    alert('Error al transferir. Intenta de nuevo.')
  }
}

/* =======================
   SIDEBAR DISPATCH PARAMS
   ======================= */
function onDispatchParamsDelivery() {
  if (!canDispatchParams.value) return
  const store = paramAssignedStore.value
  if (!store) return
  const ot = getExactOrderType(store.id, 3)
  if (!ot) { alert('Esta sede no tiene habilitado domicilio.'); return }

  dispatchToSite(store, ot, {
    mode: 'params',
    city: selectedCityObj.value,
    neighborhood: selectedNeighborhoodObj.value,
    exactAddress: paramExactAddress.value
  })
}

/* =======================
   MODAL GMaps Autocomplete
   ======================= */
let modalTimeout: any = null
function onModalAddressInput() {
  modalShowSuggestions.value = true
  modalAddressError.value = ''
  if (modalTimeout) clearTimeout(modalTimeout)
  if (!modalAddressQuery.value.trim()) { modalSuggestions.value = []; return }
  modalTimeout = setTimeout(async () => {
    try {
      modalLoadingAutocomplete.value = true
      const params = new URLSearchParams()
      params.append('input', modalAddressQuery.value)
      params.append('language', 'es')
      params.append('countries', 'co')
      params.append('limit', '4')
      params.append('session_token', sessionToken.value)
      if (modalStore.value?.city) params.append('city', modalStore.value.city)
      const res = await fetch(`${LOCATIONS_BASE}/co/places/autocomplete?${params}`)
      const data = await res.json()
      modalSuggestions.value = data.predictions ? data.predictions.map((p: any) => ({ place_id: p.place_id, description: p.description })) : []
    } catch {
      modalSuggestions.value = []
    } finally {
      modalLoadingAutocomplete.value = false
    }
  }, 300)
}

// MODIFICADO: YA NO REDIRIGE, SINO QUE GUARDA Y MUESTRA EL RESUMEN
async function onSelectModalSuggestion(s: any) {
  modalAddressQuery.value = s.description
  modalShowSuggestions.value = false
  modalStep.value = 3 // Loading View

  try {
    const params = new URLSearchParams({ place_id: s.place_id, session_token: sessionToken.value, language: 'es' })
    const res = await fetch(`${LOCATIONS_BASE}/co/places/coverage-details?${params}`)
    const data = await res.json()
    
    // Guardamos el resultado en la variable reactiva
    modalCoverageResult.value = data

    const ot = getExactOrderType(modalStore.value.id, 3)
    if (ot) {
      // En vez de dispatchToSite, pasamos al Paso 4 (Resumen)
      modalStep.value = 4
    } else {
      modalAddressError.value = 'El servicio de domicilio no está disponible en esta sede.'
      modalStep.value = 2
    }
  } catch (e) {
    modalAddressError.value = 'Error validando dirección.'
    modalStep.value = 2
  }
}

// NUEVO: Ejecuta la acción final tras confirmar en el paso 4
function confirmGoogleDispatch() {
  if (!modalCoverageResult.value) return
  
  // Obtenemos la sede sugerida por la API o la sede del modal
  const siteId = modalCoverageResult.value.nearest?.site?.site_id || modalStore.value.id
  let targetStore = getStoreById(siteId)
  
  // Si no se encuentra en el array de stores local, usamos el objeto modalStore
  if (!targetStore) targetStore = modalStore.value

  const ot = getExactOrderType(targetStore.id, 3)

  if (ot) {
      dispatchToSite(targetStore, ot, { 
        mode: 'gmaps', 
        coverageData: modalCoverageResult.value, 
        city: selectedCityObj.value 
      })
  } else {
      alert('Error: No se pudo determinar el tipo de orden para domicilio.')
  }
}

/* =======================
   IMAGES
   ======================= */
const imgCache = ref<Record<number, string>>({})
const currentImage = (store: any) => imgCache.value[store.id] || `${BACKEND_BASE}/read-product-image/96/site-${store.id}`
const loadHighResImage = (store: any) => {
  const i = new Image()
  i.src = `${BACKEND_BASE}/read-product-image/600/site-${store.id}`
  i.onload = () => imgCache.value[store.id] = i.src
}
const onImgError = (store: any) => imgCache.value[store.id] = `${BACKEND_BASE}/read-product-image/96/site-${store.id}`

/* =======================
   UTILS + DATA
   ======================= */
function getStoreById(id: number) { return stores.value.find(s => s.id === id) }
function formatCOP(v: number | null) {
  return v != null
    ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
    : ''
}

/* =======================
   Barrios API
   ======================= */
async function loadNeighborhoodsByCity(cityId: number) {
  loadingNeighborhoods.value = true
  neighborhoods.value = []
  selectedNeighborhoodId.value = ''
  neighborhoodFilterText.value = ''
  try {
    const res = await fetch(`${URI}/neighborhoods/by-city/${cityId}`)
    const data = await res.json()
    neighborhoods.value = Array.isArray(data) ? data : []
  } catch {
    neighborhoods.value = []
  } finally {
    loadingNeighborhoods.value = false
  }
}

/* =======================
   Sidebar Address Search (GMaps)
   ======================= */
let acTimeout: any = null
function onAddressInput() {
  coverageResult.value = null
  showSuggestions.value = true
  if (acTimeout) clearTimeout(acTimeout)

  if (!addressQuery.value.trim()) { suggestions.value = []; return }

  acTimeout = setTimeout(async () => {
    try {
      loadingAutocomplete.value = true
      const params = new URLSearchParams({
        input: addressQuery.value,
        language: 'es',
        countries: 'co',
        limit: '5',
        session_token: sessionToken.value
      })
      if (selectedCityId.value) {
        const c = cities.value.find((x: any) => x.city_id === selectedCityId.value)
        if (c) params.append('city', c.city_name)
      }
      const res = await fetch(`${LOCATIONS_BASE}/co/places/autocomplete?${params}`)
      suggestions.value = (await res.json()).predictions || []
    } catch {
      suggestions.value = []
    } finally {
      loadingAutocomplete.value = false
    }
  }, 300)
}

function onSelectSuggestion(s: any) {
  addressQuery.value = s.description
  showSuggestions.value = false
  suggestions.value = []
  fetchCoverageDetails(s.place_id)
}

async function fetchCoverageDetails(placeId: string) {
  try {
    const res = await fetch(`${LOCATIONS_BASE}/co/places/coverage-details?place_id=${placeId}&session_token=${sessionToken.value}&language=es`)
    const data = await res.json()
    coverageResult.value = data

    if (map.value && leafletModule.value && data.lat) {
      const L = leafletModule.value
      if (dropoffMarker.value) map.value.removeLayer(dropoffMarker.value)
      dropoffMarker.value = L.marker([data.lat, data.lng], { icon: dropoffIcon }).addTo(map.value)
      map.value.setView([data.lat, data.lng], 14)
    }
  } catch {}
}

/* =======================
   MAPA + FILTROS
   ======================= */
const filteredStores = computed(() => {
  let base = stores.value
  if (selectedCityId.value) base = base.filter((s: any) => s.cityId === selectedCityId.value)
  if (mapBounds.value) {
    base = base.filter((s: any) =>
      s.lat <= mapBounds.value.north &&
      s.lat >= mapBounds.value.south &&
      s.lng <= mapBounds.value.east &&
      s.lng >= mapBounds.value.west
    )
  }
  return base
})

function updateBounds() {
  if (map.value) {
    const b = map.value.getBounds()
    mapBounds.value = { north: b.getNorth(), south: b.getSouth(), east: b.getEast(), west: b.getWest() }
  }
}

async function onCityChange() {
  coverageResult.value = null
  addressQuery.value = ''
  suggestions.value = []
  showSuggestions.value = false

  neighborhoods.value = []
  selectedNeighborhoodId.value = ''
  neighborhoodFilterText.value = ''
  if (!selectedCityId.value) paramExactAddress.value = ''

  if (selectedCityId.value && !isGoogleMapsEnabled(selectedCityId.value)) {
    await loadNeighborhoodsByCity(selectedCityId.value)
  }

  if (!map.value || !leafletModule.value) return
  const L = leafletModule.value
  const cityIdAtClick = selectedCityId.value

  if (!initialBounds.value) initialBounds.value = map.value.getBounds()

  if (!cityIdAtClick) {
    map.value.flyToBounds(initialBounds.value, { padding: [40, 40], animate: true, duration: 0.9 })
    return
  }

  const cityStores = stores.value.filter((s: any) => s.cityId === cityIdAtClick)
  const latlngs: [number, number][] = cityStores.map((s: any) => [s.lat, s.lng])
  if (!latlngs.length) return

  const targetBounds = L.latLngBounds(latlngs)
  map.value.flyToBounds(initialBounds.value, { padding: [40, 40], animate: true, duration: 0.7 })

  setTimeout(() => {
    if (!map.value || selectedCityId.value !== cityIdAtClick) return
    map.value.flyToBounds(targetBounds, { padding: [40, 40], animate: true, duration: 0.9 })
  }, 750)
}

/* Mantener el texto de ciudad cuando cambia selectedCityId (por ejemplo al limpiar) */
watch(selectedCityId, (id) => {
  if (!id) return
  const c = cities.value.find((x: any) => Number(x.city_id) === Number(id))
  if (c) cityFilterText.value = c.city_name
})

onMounted(async () => {
  await Promise.all([loadPaymentConfig(), loadCityMapStatus()])
  await Promise.all([loadCities(), loadStores()])
  await loadStatuses()

  const mod = await import('leaflet')
  const L = (mod as any).default ?? mod
  leafletModule.value = L

  const colombiaBounds = L.latLngBounds(L.latLng(-4.5, -79.5), L.latLng(13.5, -66.5))
  map.value = L.map('vicio-map', {
    zoom: 6,
    minZoom: 5,
    maxZoom: 16,
    maxBounds: colombiaBounds,
    maxBoundsViscosity: 1.0,
    zoomControl: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    touchZoom: false,
    boxZoom: false,
    keyboard: false,
    dragging: false,
    tap: false
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
  }).addTo(map.value)

  const fireIcon = L.divIcon({
    className: 'leaflet-div-icon fire-icon',
    html: `<img src="https://cdn.deliclever.com/viciocdn/ecommerce/icon-fire-color.gif" class="fire-img" style="width:100%;height:100%"/>`,
    iconSize: [42, 42]
  })

  dropoffIcon = L.icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41]
  })

  const group = L.featureGroup()
  stores.value.forEach((s: any) => {
    const m = L.marker([s.lat, s.lng], { icon: fireIcon })
      .addTo(map.value)
      .bindPopup(`<b>${s.name}</b><br>${s.address}`)
    group.addLayer(m)
    markers.value[s.id] = m
  })

  if (stores.value.length) {
    map.value.fitBounds(group.getBounds(), { padding: [40, 40] })
    map.value.setMinZoom(map.value.getBoundsZoom(group.getBounds()))
    initialBounds.value = group.getBounds()
  } else {
    initialBounds.value = colombiaBounds
    map.value.fitBounds(colombiaBounds, { padding: [40, 40] })
  }

  map.value.on('moveend', updateBounds)
  updateBounds()
})


</script>

<style scoped>
/* Tus estilos originales se mantienen */
.vicio-page { display: flex; min-height: 100vh; width: 100%; overflow-x: hidden; background: var(--bg-page); color: var(--text-primary); font-family: 'Roboto', sans-serif; }
.vicio-map { flex: 1 1 55%; height: 100vh; background: #e2e8f0; }
.vicio-sidebar {  display: flex; flex-direction: column; background: #ffffff; border-left: 1px solid var(--border-subtle); box-shadow: -5px 0 25px rgba(0, 0, 0, 0.05); max-height: 100vh; }
.sidebar-header { padding: 1.4rem 1.8rem 1rem; border-bottom: 1px solid var(--border-subtle); background: #ffffff; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); position: relative; z-index: 5; }
.sidebar-title { font-size: 0.82rem; letter-spacing: 0.18em; font-weight: 800; margin: 0 0 0.9rem; text-transform: uppercase; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem; }
.sidebar-title::before { content: "🔥"; font-size: 1rem; }
.city-select-wrapper { margin-bottom: 0.9rem; }
.city-label { display: block; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-soft); margin-bottom: 0.35rem; }

/* Reusamos tu look de select, pero como input filtrable */
.city-select-input {
  width: 100%;
  padding: 0.55rem 2.4rem 0.55rem 0.9rem;
  border-radius: 0.55rem;
  border: 1px solid var(--border-subtle);
  font-size: 0.86rem;
  outline: none;
  background: #ffffff;
  color: var(--text-primary);
  box-sizing: border-box;
}
.city-select-input:hover { border-color: var(--accent); background-color: #f8fafc; }
.city-select-input:focus { border-color: var(--accent); background-color: #ffffff; }

/* Wrapper dropdown */
.filter-dd { position: relative; }
.filter-dd-control { position: relative; display: flex; align-items: center; }
.city-select-arrow { position: absolute; right: 0.9rem; pointer-events: none; display: flex; color: var(--text-primary); }

.filter-dd-clear {
  position: absolute;
  right: 2.2rem;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  color: #94a3b8;
}
.filter-dd-clear:hover { color: #ef4444; }

/* list */
.dd-list { z-index: 40; }

.search-wrapper { position: relative; display: flex; flex-direction: column; gap: 0.25rem; }
.search-input { padding: 0.55rem 1rem; border-radius: 0.55rem; border: 1px solid var(--border-subtle); font-size: 0.9rem; background: #f1f5f9; outline: none; width: 100%; box-sizing: border-box;}
.search-input:focus { background: #ffffff; border-color: var(--accent); }

.autocomplete-list { position: absolute; top: 100%; left: 0; right: 0; margin-top: 0.35rem; background: #ffffff; border-radius: 0.55rem; border: 1px solid var(--border-subtle); max-height: 220px; overflow-y: auto; list-style: none; padding: 0.25rem 0; z-index: 20; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1); }
.autocomplete-item { padding: 0.6rem 1rem; font-size: 0.86rem; cursor: pointer; display: flex; align-items: center; gap: 0.55rem; }
.autocomplete-item:hover { background: #fff7ed; color: var(--accent); }
.item-icon { color: var(--text-soft); font-size: 1.1em; }
.autocomplete-empty, .autocomplete-loading { padding: 0.8rem; text-align: center; font-size: 0.8rem; color: #888; }

.coverage-card { margin: 1rem 1.8rem; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 0.75rem; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
.coverage-header { background: #f8fafc; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid #e2e8f0; }
.coverage-icon { color: #ff6600; }
.coverage-title { margin: 0; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; color: #334155; }
.coverage-body { padding: 1rem; font-size: 0.9rem; }
.coverage-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.coverage-label { color: #64748b; font-weight: 500; font-size: 0.85rem; }
.coverage-value { color: #1e293b; font-weight: 600; text-align: right; max-width: 60%; }
.coverage-value.address-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.coverage-value.price { color: #16a34a; font-weight: 800; font-size: 1rem; }
.coverage-status-text { margin-top: 0.8rem; padding-top: 0.5rem; border-top: 1px dashed #e2e8f0; text-align: center; font-size: 0.85rem; font-weight: 700; }
.text-ok { color: #15803d; }
.text-fail { color: #b91c1c; }
.coverage-actions { display: flex; gap: 0.8rem; padding: 0 1rem 1rem; flex-wrap: wrap; }
.btn-action { flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.4rem; padding: 0.7rem; border-radius: 0.5rem; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; cursor: pointer; border: none; transition: transform 0.1s; }
.btn-action:disabled { opacity: .55; cursor: not-allowed; }
.btn-action:active { transform: scale(0.97); }
.btn-delivery { background-color: #ff6600; color: #ffffff; box-shadow: 0 4px 10px rgba(255, 102, 0, 0.25); }
.btn-delivery:hover { background-color: #e65c00; }
.btn-pickup { background-color: #ffffff; color: #334155; border: 2px solid #e2e8f0; }
.btn-pickup:hover { border-color: #334155; background-color: #f8fafc; }
.stores-list { flex: 1; overflow-y: auto; padding: 0.45rem 0; background: #ffffff; }
.store-item { display: flex; align-items: center; justify-content: flex-start; padding: 0.95rem 1.8rem; border-bottom: 1px solid #f1f5f9; cursor: pointer; gap: 1rem; transition: all 0.15s ease; }
.store-item:hover { background: #f8fafc; transform: translateY(-1px); }
.store-item--active { background: #fff7ed; border-left: 3px solid #ff6600; }
.store-img-wrapper { width: 90px; height: 90px; flex-shrink: 0; border-radius: 0.5rem; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); background-color: #f1f5f9; }
.store-img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease; }
.store-item:hover .store-img { transform: scale(1.05); }
.store-info { flex: 1; display: flex; flex-direction: column; gap: 0.2rem; }
.store-name { margin: 0; font-size: 1rem; font-weight: 800; color: var(--text-primary); }
.store-services { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: #ff6600; letter-spacing: 0.12em; }
.store-address { font-size: 0.84rem; color: var(--text-soft); margin-bottom: 0.4rem; }
.store-action { align-self: flex-start; border: none; font-size: 0.72rem; font-weight: 800; padding: 0.38rem 0.85rem; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.12em; display: inline-flex; align-items: center; }
.status-flex { display: flex; align-items: center; gap: 0.35rem; }
.store-action[data-status='open'] { background: #dcfce7; color: #166534; }
.store-action[data-status='closed'], .store-action[data-status='close'] { background: #fee2e2; color: #991b1b; }
.store-action[data-status='unknown'] { background: #f1f5f9; color: #94a3b8; }
.store-arrow { background: #000000; color: #ffffff; width: 40px; height: 40px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: transform 0.2s ease, background 0.2s ease; box-shadow: 0 4px 10px rgba(0,0,0,0.2); flex-shrink: 0; }
.store-arrow:hover { background: #333333; transform: scale(1.1); }
.no-results { padding: 2rem; text-align: center; color: #64748b; font-size: 0.9rem; }
:global(.leaflet-div-icon.fire-icon) { width: 42px !important; height: 42px !important; border: none; background: transparent; display: flex; align-items: center; justify-content: center; }
:global(.leaflet-div-icon.fire-icon .fire-img) { width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2)); }
:deep(.leaflet-tile) { filter: grayscale(100%) !important; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 9999; padding: 1rem; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px); animation: fadeIn 0.2s; }
.modal-content { background: white; width: 90%; max-width: 450px; border-radius: 12px; min-height: 80vh; max-height: 20rem; padding: 2rem; position: relative; animation: slideUp 0.3s; }
.modal-close-btn { position: absolute; top: 10px; right: 10px; background: transparent; border: none; cursor: pointer; color: #94a3b8; padding: 5px; }
.modal-close-btn:hover { color: #ef4444; }
.modal-title { margin: 0 0 5px; font-size: 1.2rem; font-weight: 800; color: #1e293b; text-align: center; text-transform: uppercase; margin-top: 2rem; }
.modal-subtitle { text-align: center; color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem; }
.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
.modal-btn { display: flex; flex-direction: column; align-items: center; padding: 1.5rem 1rem; border-radius: 12px; border: 2px solid transparent; cursor: pointer; background: #f8fafc; transition: all 0.2s; }
.btn-icon-circle { width: 50px; height: 50px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.modal-btn span { font-weight: 800; font-size: 1rem; margin-bottom: 2px; text-transform: uppercase; }
.modal-btn small { font-size: 0.75rem; color: #94a3b8; }
.modal-btn--delivery:hover { background: #fff7ed; border-color: #ff6600; color: #c2410c; }
.modal-btn--delivery:hover .btn-icon-circle { background: #ff6600; color: white; }
.modal-btn--pickup:hover { background: #f0fdf4; border-color: #16a34a; color: #15803d; }
.modal-btn--pickup:hover .btn-icon-circle { background: #16a34a; color: white; }
.modal-header-nav { position: absolute; top: 2rem; left: 1.5rem; margin-bottom: 1rem; }
.modal-back-btn { background: transparent; border: none; cursor: pointer; display: flex; align-items: center; gap: 5px; font-size: 0.8rem; color: #64748b; font-weight: 700; }
.modal-back-btn:hover { color: #334155; }
.modal-search { margin-top: 1rem; }
.modal-search .search-input { border: 2px solid #e2e8f0; font-size: 1rem; padding: 0.8rem; }
.modal-search .search-input:focus { border-color: #ff6600; outline: none; }
.modal-error { margin-top: 10px; color: #ef4444; font-size: 0.85rem; text-align: center; }
.modal-loading-view { text-align: center; padding: 2rem 0; color: #64748b; }
.spin-icon { animation: spin 1s linear infinite; color: #ff6600; margin-bottom: 1rem; }
.redirect-overlay { position: fixed; inset: 0; background: rgba(255,255,255,0.9); z-index: 10000; display: flex; align-items: center; justify-content: center; }
.redirect-content { text-align: center; animation: popIn 0.5s ease-out; }
.redirect-spinner { position: relative; display: inline-flex; margin-bottom: 2rem; color: #ff6600; }
.rocket-icon { z-index: 2; animation: rocketFloat 1.5s ease-in-out infinite alternate; color: #ff6600; }
.pulse-ring { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; border-radius: 50%; border: 2px solid #ff6600; opacity: 0; animation: pulse 2s infinite; }
.redirect-store { font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0.5rem 0; }
.redirect-subtitle { font-size: 1rem; color: #94a3b8; }

/* NUEVOS ESTILOS PARA FLUJO BARRIOS EN MODAL */
.params-flow-modal { margin-top: 1rem; }
.selected-nb-info { background: #f8fafc; border: 1px dashed #cbd5e1; padding: 0.8rem; margin-top: 1rem; border-radius: 8px; font-size: 0.9rem; }
.info-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.text-green { color: #16a34a; }
.full-width { width: 100%; margin-top: 1rem; }
.relative { position: relative; }

@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes rocketFloat { from { transform: translateY(0); } to { transform: translateY(-10px); } }
@keyframes pulse { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; } }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 900px) {
  .vicio-page { flex-direction: column; height: 100vh; overflow: hidden; }
  .vicio-map { flex: 0 0 40%; height: 40% !important; width: 100%; z-index: 10; }
  .vicio-sidebar { flex: 1 1 60%; height: 60% !important; width: 100%; overflow: hidden; border-radius: 1.5rem 1.5rem 0 0; margin-top: -1.5rem; z-index: 20; box-shadow: 0 -4px 20px rgba(0,0,0,0.15); }
  .stores-list { flex: 1; overflow-y: auto; padding-bottom: 2rem; }
  .sidebar-header { flex-shrink: 0; position: sticky; top: 0; }
  .store-img-wrapper { width: 70px; height: 70px; }
  .store-item { padding: 0.8rem 1rem; }
  .coverage-card { margin: 1rem; }
}
</style>