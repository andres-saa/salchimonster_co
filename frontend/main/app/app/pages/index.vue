<template>
  <div class="vicio-page">
    <!-- Overlay de redirección -->
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

    <!-- MAPA -->
    <ClientOnly>
      <div id="vicio-map" class="vicio-map"></div>
    </ClientOnly>

    <!-- SIDEBAR -->
    <div class="vicio-sidebar">
      <header class="sidebar-header">
        <h2 class="sidebar-title">ELIGE TU SALCHIMONSTER MÁS CERCANO</h2>

        <!-- CIUDAD (PrimeVue Dropdown) -->
        <div class="field">
          <label class="field-label">Ciudad</label>

          <!-- IMPORTANTE:
            - No tocamos estilos internos de PrimeVue (p-inputtext / padding / etc.)
            - Solo usamos style width:100% para layout.
          -->
          <Dropdown
            v-model="selectedCityId"
            :options="cityOptions"
            optionLabel="city_name"
            optionValue="city_id"
            filter
            showClear
            placeholder="Todas las ciudades"
            style="width: 100%;"
            @change="onCityChange"
            @clear="onCityClear"
          />
        </div>

        <!-- GOOGLE: DIRECCIÓN (PrimeVue AutoComplete) -->
        <div v-if="selectedCityIdNumber && isGoogleCity" class="field">
          <label class="field-label">Dirección</label>

          <AutoComplete
            v-model="addressQuery"
            :suggestions="suggestions"
            field="description"
            :loading="loadingAutocomplete"
            placeholder="Escribe tu dirección..."
            style="width: 100%;"
            inputStyle="width: 100%;"
            @complete="onAddressComplete"
            @item-select="onSelectSuggestion"
            @clear="onClearAddress"
          />
        </div>

        <!-- PARAMS: BARRIOS (PrimeVue Dropdown + InputText) -->
        <div v-if="selectedCityIdNumber && isParamsCity" class="params-box">
          <div class="field">
            <label class="field-label">Barrio / Sector</label>

            <Dropdown
              v-model="selectedNeighborhoodId"
              :options="neighborhoodOptions"
              optionLabel="name"
              optionValue="_id"
              filter
              showClear
              :disabled="loadingNeighborhoods || neighborhoodOptions.length === 0"
              :placeholder="loadingNeighborhoods ? 'Cargando barrios...' : (neighborhoodOptions.length ? 'Busca tu barrio' : 'No hay barrios')"
              style="width: 100%;"
              @change="onNeighborhoodChange"
              @clear="onNeighborhoodClear"
            />
          </div>

          <div class="field">
            <label class="field-label">Dirección exacta</label>
            <InputText
              v-model="paramExactAddress"
              placeholder="Ej: Calle 123 # 45 - 67..."
              style="width: 100%;"
            />
          </div>
        </div>
      </header>

      <!-- RESULTADO GOOGLE -->
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
          <Button
            v-if="coverageResult.nearest?.in_coverage && getExactOrderType(coverageResult.nearest.site.site_id, 3)"
            @click="dispatchToSite(
              getStoreById(coverageResult.nearest.site.site_id) || coverageResult.nearest.site,
              getExactOrderType(coverageResult.nearest.site.site_id, 3),
              { mode: 'gmaps', coverageData: coverageResult, city: selectedCityObj }
            )"
          >
            <Icon name="mdi:moped" size="1.2em" style="margin-right:.45rem;" />
            Domicilio
          </Button>
        </div>
      </section>

      <!-- RESULTADO PARAMS -->
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

          <div class="coverage-status-text text-ok">✅ Listo para enviar</div>
        </div>

        <div class="coverage-actions">
          <Button :disabled="!canDispatchParams" @click="onDispatchParamsDelivery">
            <Icon name="mdi:moped" size="1.2em" style="margin-right:.45rem;" />
            Domicilio
          </Button>
        </div>
      </section>

      <!-- LISTA TIENDAS -->
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

            <p class="store-address">{{ store.address }} – {{ store.city }}</p>

            <span class="store-action" :data-status="store.status || 'unknown'">
              <span v-if="store.status === 'open'" class="status-flex">
                <Icon name="mdi:check-circle-outline" size="1.1em" /> Abierto
              </span>
              <span v-else class="status-flex">Cerrado</span>
            </span>
          </div>

          <span class="store-arrow">
            <Icon name="mdi:chevron-right" size="1.6em" />
          </span>
        </article>
      </main>
    </div>

    <!-- MODAL (PrimeVue Dialog) -->
    <Dialog
      v-model:visible="isModalOpen"
      modal
      :closable="false"
      :draggable="false"
      style="width: 92vw; max-width: 460px;"
    >
      <template #header>
        <div class="modal-header">
          <div class="modal-header-left">
            <Button v-if="modalStep !== 1" text @click="setModalStep(1)">
              <Icon name="mdi:arrow-left" size="1.2em" style="margin-right:.4rem;" />
              Volver
            </Button>
          </div>

          <div class="modal-header-right">
            <Button text @click="closeModal">
              <Icon name="mdi:close" size="1.3em" />
            </Button>
          </div>
        </div>
      </template>

      <!-- STEP 1 -->
      <div v-if="modalStore && modalStep === 1" class="modal-body">
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

      <!-- STEP 2 -->
      <div v-else-if="modalStore && modalStep === 2" class="modal-body">
        <div v-if="isGoogleCity">
          <h3 class="modal-title">¿Dónde estás?</h3>

          <div class="field">
            <label class="field-label">Dirección</label>
            <AutoComplete
              v-model="modalAddressQuery"
              :suggestions="modalSuggestions"
              field="description"
              :loading="modalLoadingAutocomplete"
              placeholder="Calle 123 # 45 - 67..."
              style="width: 100%;"
              inputStyle="width: 100%;"
              @complete="onModalAddressComplete"
              @item-select="onSelectModalSuggestion"
            />
          </div>

          <div v-if="modalAddressError" class="modal-error">{{ modalAddressError }}</div>
        </div>

        <div v-else class="params-flow-modal">
          <h3 class="modal-title">Datos de Entrega</h3>

          <div class="field">
            <label class="field-label">Barrio</label>

            <Dropdown
              v-model="modalSelectedNeighborhoodId"
              :options="neighborhoodOptions"
              optionLabel="name"
              optionValue="_id"
              filter
              showClear
              :disabled="loadingNeighborhoods || neighborhoodOptions.length === 0"
              placeholder="Busca tu barrio"
              style="width: 100%;"
              @change="syncModalSelectedNeighborhood"
              @clear="clearModalNeighborhood"
            />
          </div>

          <div v-if="modalSelectedNeighborhood" class="selected-nb-info">
            <div class="info-row">
              <span>Barrio:</span>
              <strong>{{ modalSelectedNeighborhood.name }}</strong>
            </div>
            <div class="info-row">
              <span>Domicilio:</span>
              <strong class="text-green">{{ formatCOP(Number(modalSelectedNeighborhood.delivery_price || 0)) }}</strong>
            </div>
          </div>

          <div class="field">
            <label class="field-label">Dirección Exacta</label>
            <InputText
              v-model="modalParamAddress"
              placeholder="Ej: Calle 123 # 45 - 67 Apt 201"
              style="width: 100%;"
            />
          </div>

          <Button
            style="width: 100%;"
            :disabled="!modalSelectedNeighborhood || !modalParamAddress.trim()"
            @click="onDispatchModalParams"
          >
            Confirmar Domicilio
          </Button>
        </div>
      </div>

      <!-- STEP 3 -->
      <div v-else-if="modalStore && modalStep === 3" class="modal-loading-view">
        <ProgressSpinner />
        <p>Validando cobertura...</p>
      </div>

      <!-- STEP 4 -->
      <div v-else-if="modalStore && modalStep === 4 && modalCoverageResult" class="modal-body">
        <h3 class="modal-title">Resumen de Cobertura</h3>

        <div class="coverage-card modal-coverage">
          <div class="coverage-body">
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

        <Button
          style="width: 100%;"
          :disabled="!modalCoverageResult.nearest?.in_coverage"
          @click="confirmGoogleDispatch"
        >
          <Icon name="mdi:check-circle-outline" size="1.2em" style="margin-right:.45rem;" />
          Confirmar e Ir
        </Button>
      </div>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import 'leaflet/dist/leaflet.css'

// PrimeVue (solo componentes; estilos vienen de tu theme global)
import Dropdown from 'primevue/dropdown'
import AutoComplete from 'primevue/autocomplete'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import ProgressSpinner from 'primevue/progressspinner'

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

/**
 * Prime Dropdown con showClear tiende a setear null
 * -> manejamos null como "todas"
 */
const selectedCityId = ref<number | null>(null)
const selectedStoreId = ref<number | null>(null)

const sessionToken = ref(
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : Math.random().toString(36).substring(2)
)

const isRedirecting = ref(false)
const targetSiteName = ref('')

/* =======================
   CITY OPTIONS (Dropdown)
   ======================= */
const orderedCities = computed(() => {
  return [...cities.value.filter((s: any) => ![18, 15, 19].includes(s.city_id))]
    .sort((a: any, b: any) => (a.index ?? 0) - (b.index ?? 0))
})

const cityOptions = computed(() => {
  // Incluye "Todas las ciudades" como opción real
  return [{ city_id: 0, city_name: 'Todas las ciudades' }, ...orderedCities.value]
})

const selectedCityIdNumber = computed(() => Number(selectedCityId.value ?? 0))
const selectedCityObj = computed(() => {
  const id = selectedCityIdNumber.value
  if (!id) return null
  return cities.value.find((c: any) => Number(c.city_id) === id) || null
})

function onCityClear() {
  selectedCityId.value = 0
  onCityChange()
}

/* =======================
   Google Sidebar
   ======================= */
const addressQuery = ref('')
const suggestions = ref<any[]>([])
const loadingAutocomplete = ref(false)
const coverageResult = ref<any | null>(null)
const dropoffMarker = ref<any | null>(null)
let dropoffIcon: any = null

/* =======================
   Barrios Sidebar
   ======================= */
const neighborhoods = ref<any[]>([])
const loadingNeighborhoods = ref(false)

const selectedNeighborhoodId = ref<string | null>(null)
const paramExactAddress = ref('')

const neighborhoodOptions = computed(() => {
  return (neighborhoods.value || []).map((n: any) => ({
    ...n,
    _id: String(n.neighborhood_id || n.id)
  }))
})

const selectedNeighborhoodObj = computed(() => {
  if (!selectedNeighborhoodId.value) return null
  const id = String(selectedNeighborhoodId.value)
  return neighborhoodOptions.value.find((n: any) => String(n._id) === id) || null
})

const paramDeliveryPrice = computed(() => Number(selectedNeighborhoodObj.value?.delivery_price ?? 0))

function onNeighborhoodChange() {
  // nada extra; el computed selectedNeighborhoodObj ya se actualiza
}
function onNeighborhoodClear() {
  selectedNeighborhoodId.value = null
}

/* =======================
   Helpers / Computed
   ======================= */
function isGoogleMapsEnabled(cityId: number) {
  const config = cityMapStatus.value.find((c: any) => Number(c.city_id) === Number(cityId))
  return config ? !!config.user_google_map_status : false
}

const isGoogleCity = computed(() => {
  const cityId = modalStore.value ? (modalStore.value.cityId || modalStore.value.city_id) : selectedCityIdNumber.value
  return !!cityId && isGoogleMapsEnabled(Number(cityId))
})

const isParamsCity = computed(() => !isGoogleCity.value)

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

// Google Modal
const modalAddressQuery = ref('')
const modalSuggestions = ref<any[]>([])
const modalLoadingAutocomplete = ref(false)
const modalAddressError = ref('')
const modalCoverageResult = ref<any>(null)

// Params Modal
const modalParamAddress = ref('')
const modalSelectedNeighborhoodId = ref<string | null>(null)
const modalSelectedNeighborhood = ref<any>(null)

/* =======================
   MODAL LOGIC
   ======================= */
async function openModal(store: any) {
  modalStore.value = store
  modalStep.value = 1
  isModalOpen.value = true

  modalAddressQuery.value = ''
  modalSuggestions.value = []
  modalCoverageResult.value = null
  modalAddressError.value = ''

  modalParamAddress.value = ''
  modalSelectedNeighborhoodId.value = null
  modalSelectedNeighborhood.value = null

  const cityId = store.cityId || store.city_id
  if (cityId && !isGoogleMapsEnabled(cityId)) {
    // Cargamos barrios si esta ciudad usa params
    if (neighborhoods.value.length === 0 || selectedCityIdNumber.value !== Number(cityId)) {
      await loadNeighborhoodsByCity(cityId)
    }
  }
}

function closeModal() {
  isModalOpen.value = false
  modalStore.value = null
}

function setModalStep(step: number) {
  modalStep.value = step
  if (step === 2 && isGoogleCity.value) nextTick(() => {}) // si luego quieres focus, aquí
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

function syncModalSelectedNeighborhood() {
  if (!modalSelectedNeighborhoodId.value) {
    modalSelectedNeighborhood.value = null
    return
  }
  const id = String(modalSelectedNeighborhoodId.value)
  modalSelectedNeighborhood.value = neighborhoodOptions.value.find((n: any) => String(n._id) === id) || null
}
function clearModalNeighborhood() {
  modalSelectedNeighborhoodId.value = null
  modalSelectedNeighborhood.value = null
}

/* =======================
   API LOADERS
   ======================= */
async function loadPaymentConfig() {
  try {
    const res = await fetch(`${URI}/site-payments-complete`)
    sitePaymentsConfig.value = await res.json()
  } catch (e) {
    console.error('Error loading payment config', e)
  }
}

async function loadCityMapStatus() {
  try {
    const res = await fetch(`${LOCATIONS_BASE}/data/cities_google_map_status`)
    const data = await res.json()
    cityMapStatus.value = data.data.cities || []
  } catch (e) {
    console.error('Error loading city map status', e)
  }
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
  | { mode: 'gmaps'; coverageData: any; city?: any }
  | { mode: 'params'; city?: any; neighborhood: any; exactAddress: string }
  | { mode: 'simple'; city?: any }
  | any

async function dispatchToSite(manualStore: any, orderTypeObj: any, extra: DispatchExtra = { mode: 'simple' }) {
  isRedirecting.value = true

  let targetStore = manualStore
  targetSiteName.value = targetStore?.name || targetStore?.site_name || 'Nueva Sede'

  const targetCityId = targetStore.cityId || targetStore.city_id
  const useGoogleMaps = isGoogleMapsEnabled(Number(targetCityId))
  const isDelivery = Number(orderTypeObj?.id) === 3

  try {
    const hash =
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : Date.now().toString(36).substring(2)

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
          delivery_price: Number(nb.delivery_price ?? 0)
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
        phone_code: {
          code: 'CO',
          name: 'Colombia',
          dialCode: '+57',
          flag: 'https://flagcdn.com/h20/co.png',
          label: '+57',
          dialDigits: '57'
        }
      },
      location_meta: {
        city: extra?.city || null,
        neigborhood:
          extra?.mode === 'params'
            ? {
                ...extra.neighborhood,
                neighborhood_id: extra.neighborhood.neighborhood_id || extra.neighborhood.id,
                name: extra.neighborhood.name,
                site_id: extra.neighborhood.site_id,
                delivery_price: Number(extra.neighborhood.delivery_price ?? 0)
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

    // Preservar query params
    const params = new URLSearchParams()
    params.append('hash', hash)

    if (route.query.inserted_by) params.append('inserted_by', String(route.query.inserted_by))
    if (route.query.token) params.append('token', String(route.query.token))
    if (route.query.iframe) params.append('iframe', String(route.query.iframe))

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
  if (!ot) {
    alert('Esta sede no tiene habilitado domicilio.')
    return
  }

  dispatchToSite(store, ot, {
    mode: 'params',
    city: selectedCityObj.value,
    neighborhood: selectedNeighborhoodObj.value,
    exactAddress: paramExactAddress.value
  })
}

/* =======================
   MODAL PARAMS DISPATCH
   ======================= */
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

/* =======================
   Google Autocomplete (Sidebar)
   ======================= */
let acTimeout: any = null
function onAddressComplete(e: any) {
  coverageResult.value = null
  if (acTimeout) clearTimeout(acTimeout)

  const q = String(e.query || '')
  if (!q.trim()) {
    suggestions.value = []
    return
  }

  acTimeout = setTimeout(async () => {
    try {
      loadingAutocomplete.value = true
      const params = new URLSearchParams({
        input: q,
        language: 'es',
        countries: 'co',
        limit: '5',
        session_token: sessionToken.value
      })

      if (selectedCityIdNumber.value) {
        const c = cities.value.find((x: any) => Number(x.city_id) === selectedCityIdNumber.value)
        if (c) params.append('city', c.city_name)
      }

      const res = await fetch(`${LOCATIONS_BASE}/co/places/autocomplete?${params}`)
      const data = await res.json()
      // Normalizamos a lo que Prime espera: objetos con field="description"
      suggestions.value = (data.predictions || []).map((p: any) => ({
        place_id: p.place_id,
        description: p.description
      }))
    } catch {
      suggestions.value = []
    } finally {
      loadingAutocomplete.value = false
    }
  }, 260)
}

function onSelectSuggestion(ev: any) {
  const s = ev?.value
  if (!s?.place_id) return
  addressQuery.value = s.description
  suggestions.value = []
  fetchCoverageDetails(s.place_id)
}

function onClearAddress() {
  addressQuery.value = ''
  suggestions.value = []
  coverageResult.value = null
}

/* =======================
   Google Autocomplete (Modal)
   ======================= */
let modalTimeout: any = null
function onModalAddressComplete(e: any) {
  if (modalTimeout) clearTimeout(modalTimeout)

  const q = String(e.query || '')
  modalAddressError.value = ''

  if (!q.trim()) {
    modalSuggestions.value = []
    return
  }

  modalTimeout = setTimeout(async () => {
    try {
      modalLoadingAutocomplete.value = true
      const params = new URLSearchParams()
      params.append('input', q)
      params.append('language', 'es')
      params.append('countries', 'co')
      params.append('limit', '4')
      params.append('session_token', sessionToken.value)
      if (modalStore.value?.city) params.append('city', modalStore.value.city)

      const res = await fetch(`${LOCATIONS_BASE}/co/places/autocomplete?${params}`)
      const data = await res.json()
      modalSuggestions.value = (data.predictions || []).map((p: any) => ({
        place_id: p.place_id,
        description: p.description
      }))
    } catch {
      modalSuggestions.value = []
    } finally {
      modalLoadingAutocomplete.value = false
    }
  }, 260)
}

async function onSelectModalSuggestion(ev: any) {
  const s = ev?.value
  if (!s?.place_id) return

  modalAddressQuery.value = s.description
  modalStep.value = 3

  try {
    const params = new URLSearchParams({ place_id: s.place_id, session_token: sessionToken.value, language: 'es' })
    const res = await fetch(`${LOCATIONS_BASE}/co/places/coverage-details?${params}`)
    const data = await res.json()

    modalCoverageResult.value = data

    const siteId = data.nearest?.site?.site_id || modalStore.value.id
    const storeCandidate = getStoreById(Number(siteId)) || modalStore.value
    const ot = getExactOrderType(storeCandidate.id, 3)

    if (ot) {
      modalStep.value = 4
    } else {
      modalAddressError.value = 'El servicio de domicilio no está disponible en esta sede.'
      modalStep.value = 2
    }
  } catch {
    modalAddressError.value = 'Error validando dirección.'
    modalStep.value = 2
  }
}

function confirmGoogleDispatch() {
  if (!modalCoverageResult.value) return

  const siteId = modalCoverageResult.value.nearest?.site?.site_id || modalStore.value.id
  let targetStore = getStoreById(Number(siteId))
  if (!targetStore) targetStore = modalStore.value

  const ot = getExactOrderType(targetStore.id, 3)
  if (!ot) {
    alert('Error: No se pudo determinar el tipo de orden para domicilio.')
    return
  }

  dispatchToSite(targetStore, ot, {
    mode: 'gmaps',
    coverageData: modalCoverageResult.value,
    city: selectedCityObj.value
  })
}

/* =======================
   Coverage details (Sidebar)
   ======================= */
async function fetchCoverageDetails(placeId: string) {
  try {
    const res = await fetch(
      `${LOCATIONS_BASE}/co/places/coverage-details?place_id=${placeId}&session_token=${sessionToken.value}&language=es`
    )
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
   Barrios API
   ======================= */
async function loadNeighborhoodsByCity(cityId: number) {
  loadingNeighborhoods.value = true
  neighborhoods.value = []
  selectedNeighborhoodId.value = null

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
   MAPA + FILTROS
   ======================= */
const filteredStores = computed(() => {
  let base = stores.value

  const cityId = selectedCityIdNumber.value
  if (cityId) base = base.filter((s: any) => Number(s.cityId) === cityId)

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
  if (!map.value) return
  const b = map.value.getBounds()
  mapBounds.value = { north: b.getNorth(), south: b.getSouth(), east: b.getEast(), west: b.getWest() }
}

/**
 * City change:
 * - Limpia flows
 * - Si ciudad es params => carga barrios
 * - Ajusta bounds
 */
async function onCityChange() {
  coverageResult.value = null
  addressQuery.value = ''
  suggestions.value = []

  neighborhoods.value = []
  selectedNeighborhoodId.value = null
  paramExactAddress.value = ''

  const cityId = selectedCityIdNumber.value
  if (cityId && !isGoogleMapsEnabled(cityId)) {
    await loadNeighborhoodsByCity(cityId)
  }

  if (!map.value || !leafletModule.value) return
  const L = leafletModule.value

  if (!initialBounds.value) initialBounds.value = map.value.getBounds()

  if (!cityId) {
    map.value.flyToBounds(initialBounds.value, { padding: [40, 40], animate: true, duration: 0.9 })
    return
  }

  const cityStores = stores.value.filter((s: any) => Number(s.cityId) === cityId)
  const latlngs: [number, number][] = cityStores.map((s: any) => [s.lat, s.lng])
  if (!latlngs.length) return

  const targetBounds = L.latLngBounds(latlngs)
  map.value.flyToBounds(initialBounds.value, { padding: [40, 40], animate: true, duration: 0.7 })

  setTimeout(() => {
    if (!map.value || selectedCityIdNumber.value !== cityId) return
    map.value.flyToBounds(targetBounds, { padding: [40, 40], animate: true, duration: 0.9 })
  }, 750)
}

watch(selectedCityId, async (v) => {
  // si el usuario limpia (null), lo tratamos como "todas"
  if (v == null) selectedCityId.value = 0
})

/* =======================
   IMAGES
   ======================= */
const imgCache = ref<Record<number, string>>({})
const currentImage = (store: any) => imgCache.value[store.id] || `${BACKEND_BASE}/read-product-image/96/site-${store.id}`
const loadHighResImage = (store: any) => {
  const i = new Image()
  i.src = `${BACKEND_BASE}/read-product-image/600/site-${store.id}`
  i.onload = () => (imgCache.value[store.id] = i.src)
}
const onImgError = (store: any) => (imgCache.value[store.id] = `${BACKEND_BASE}/read-product-image/96/site-${store.id}`)

/* =======================
   UTILS
   ======================= */
function getStoreById(id: number) {
  return stores.value.find((s) => Number(s.id) === Number(id))
}

function formatCOP(v: number | null) {
  return v != null
    ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
    : ''
}

/* =======================
   MOUNT
   ======================= */
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
/* =========================
   Layout propio (NO tocamos estilos internos de PrimeVue)
   ========================= */

.vicio-page {
  display: flex;
  min-height: 100vh;
  width: 100%;
  overflow-x: hidden;
  background: var(--bg-page);
  color: var(--text-primary);
  font-family: 'Roboto', sans-serif;
}

.vicio-map {
  flex: 1 1 55%;
  height: 100vh;
  background: #e2e8f0;
}

.vicio-sidebar {
  flex: 1 1 45%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-left: 1px solid var(--border-subtle);
  box-shadow: -5px 0 25px rgba(0, 0, 0, 0.05);
  max-height: 100vh;
}

.sidebar-header {
  padding: 1.4rem 1.8rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  position: relative;
  z-index: 5;
}

.sidebar-title {
  font-size: 0.82rem;
  letter-spacing: 0.18em;
  font-weight: 800;
  margin: 0 0 0.9rem;
  text-transform: uppercase;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.sidebar-title::before {
  content: '🔥';
  font-size: 1rem;
}

.field {
  margin-bottom: 0.9rem;
}

.field-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-soft);
  margin-bottom: 0.35rem;
}

/* Caja params */
.params-box {
  margin-top: 0.5rem;
}

/* Coverage card */
.coverage-card {
  margin: 1rem 1.8rem;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.coverage-header {
  background: #f8fafc;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}
.coverage-icon { color: #ff6600; }
.coverage-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #334155;
}
.coverage-body { padding: 1rem; font-size: 0.9rem; }
.coverage-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.coverage-label { color: #64748b; font-weight: 500; font-size: 0.85rem; }
.coverage-value { color: #1e293b; font-weight: 600; text-align: right; max-width: 60%; }
.coverage-value.address-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.coverage-value.price { color: #16a34a; font-weight: 800; font-size: 1rem; }
.coverage-status-text {
  margin-top: 0.8rem;
  padding-top: 0.5rem;
  border-top: 1px dashed #e2e8f0;
  text-align: center;
  font-size: 0.85rem;
  font-weight: 700;
}
.text-ok { color: #15803d; }
.text-fail { color: #b91c1c; }

.coverage-actions {
  display: flex;
  gap: 0.8rem;
  padding: 0 1rem 1rem;
  flex-wrap: wrap;
}

/* Lista tiendas */
.stores-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.45rem 0;
  background: #ffffff;
}

.store-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0.95rem 1.8rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  gap: 1rem;
  transition: all 0.15s ease;
}
.store-item:hover { background: #f8fafc; transform: translateY(-1px); }
.store-item--active { background: #fff7ed; border-left: 3px solid #ff6600; }

.store-img-wrapper {
  width: 90px;
  height: 90px;
  flex-shrink: 0;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  background-color: #f1f5f9;
}
.store-img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease; }
.store-item:hover .store-img { transform: scale(1.05); }

.store-info { flex: 1; display: flex; flex-direction: column; gap: 0.2rem; }
.store-name { margin: 0; font-size: 1rem; font-weight: 800; color: var(--text-primary); }
.store-services { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: #ff6600; letter-spacing: 0.12em; }
.store-address { font-size: 0.84rem; color: var(--text-soft); margin-bottom: 0.4rem; }

.store-action {
  align-self: flex-start;
  border: none;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.38rem 0.85rem;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  display: inline-flex;
  align-items: center;
}
.status-flex { display: flex; align-items: center; gap: 0.35rem; }
.store-action[data-status='open'] { background: #dcfce7; color: #166534; }
.store-action[data-status='closed'],
.store-action[data-status='close'] { background: #fee2e2; color: #991b1b; }
.store-action[data-status='unknown'] { background: #f1f5f9; color: #94a3b8; }

.store-arrow {
  background: #000000;
  color: #ffffff;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
  flex-shrink: 0;
}

/* Leaflet custom icon */
:global(.leaflet-div-icon.fire-icon) {
  width: 42px !important;
  height: 42px !important;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}
:global(.leaflet-div-icon.fire-icon .fire-img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}
:deep(.leaflet-tile) { filter: grayscale(100%) !important; }

/* Modal (contenido interno) */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.modal-body {
  padding-top: 0.25rem;
}
.modal-title {
  margin: 0 0 5px;
  font-size: 1.2rem;
  font-weight: 800;
  color: #1e293b;
  text-align: center;
  text-transform: uppercase;
  margin-top: 0.4rem;
}
.modal-subtitle {
  text-align: center;
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 1.0rem;
}
.modal-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.8rem;
}
.modal-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem 1rem;
  border-radius: 12px;
  border: 2px solid transparent;
  cursor: pointer;
  background: #f8fafc;
  transition: all 0.2s;
}
.btn-icon-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.modal-btn span { font-weight: 800; font-size: 1rem; margin-bottom: 2px; text-transform: uppercase; }
.modal-btn small { font-size: 0.75rem; color: #94a3b8; }
.modal-btn--delivery:hover { background: #fff7ed; border-color: #ff6600; color: #c2410c; }
.modal-btn--delivery:hover .btn-icon-circle { background: #ff6600; color: white; }
.modal-btn--pickup:hover { background: #f0fdf4; border-color: #16a34a; color: #15803d; }
.modal-btn--pickup:hover .btn-icon-circle { background: #16a34a; color: white; }

.modal-error { margin-top: 10px; color: #ef4444; font-size: 0.85rem; text-align: center; }
.modal-loading-view { text-align: center; padding: 1.2rem 0; color: #64748b; }
.modal-coverage { margin: 1rem 0; }

.params-flow-modal { margin-top: 0.4rem; }
.selected-nb-info {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  padding: 0.8rem;
  margin: 0.7rem 0 0.9rem;
  border-radius: 8px;
  font-size: 0.9rem;
}
.info-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.text-green { color: #16a34a; }

/* Overlay redirect */
.redirect-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255,255,255,0.9);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.redirect-content { text-align: center; animation: popIn 0.5s ease-out; }
.redirect-spinner { position: relative; display: inline-flex; margin-bottom: 2rem; color: #ff6600; }
.rocket-icon { z-index: 2; animation: rocketFloat 1.5s ease-in-out infinite alternate; color: #ff6600; }
.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px solid #ff6600;
  opacity: 0;
  animation: pulse 2s infinite;
}
.redirect-store { font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0.5rem 0; }
.redirect-subtitle { font-size: 1rem; color: #94a3b8; }

@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes rocketFloat { from { transform: translateY(0); } to { transform: translateY(-10px); } }
@keyframes pulse { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Responsive */
@media (max-width: 900px) {
  .vicio-page { flex-direction: column; height: 100vh; overflow: hidden; }
  .vicio-map { flex: 0 0 40%; height: 40% !important; width: 100%; z-index: 10; }
  .vicio-sidebar {
    flex: 1 1 60%;
    height: 60% !important;
    width: 100%;
    overflow: hidden;
    border-radius: 1.5rem 1.5rem 0 0;
    margin-top: -1.5rem;
    z-index: 20;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
  }
  .stores-list { flex: 1; overflow-y: auto; padding-bottom: 2rem; }
  .sidebar-header { flex-shrink: 0; position: sticky; top: 0; }
  .store-img-wrapper { width: 70px; height: 70px; }
  .store-item { padding: 0.8rem 1rem; }
  .coverage-card { margin: 1rem; }
}
</style>
