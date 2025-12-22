<template>
  <div class="vicio-root">
    <Transition name="fade">
      <div v-if="isRedirecting" class="redirect-overlay">
        <div class="redirect-content">
          <div class="redirect-spinner">
            <Icon name="mdi:rocket-launch-outline" size="3em" class="rocket-icon" />
            <div class="pulse-ring"></div>
          </div>
          <h2 class="redirect-title">{{ t('redirect_title') }}</h2>
          <h3 class="redirect-store">{{ targetSiteName }}</h3>
          <p class="redirect-subtitle">{{ t('redirect_subtitle') }}</p>
        </div>
      </div>
    </Transition>

    <!-- ✅ App-like shell: sin scroll global, todo ocurre dentro -->
    <div class="vicio-page" :class="{ 'is-map-collapsed': shouldCollapseMap }">
      <ClientOnly>
        <div class="vicio-map-shell">
          <div id="vicio-map" class="vicio-map"></div>
        </div>
      </ClientOnly>

      <div class="vicio-sidebar">
        <header class="sidebar-header">
          <div class="sidebar-top-row">
            <h2 class="sidebar-title">{{ t('choose_nearest') }}</h2>

            <!-- ✅ Selector idioma (local + localStorage) -->
            <div class="lang-wrap" ref="langWrapRef">
              <button class="lang-btn" type="button" @click="toggleLangMenu" :aria-label="t('language')">
                <img :src="currentLang.flag" class="lang-flag" :alt="currentLang.label" />
                <span class="lang-label">{{ currentLang.label }}</span>
                <Icon name="mdi:chevron-down" size="1.2em" class="lang-chevron" />
              </button>

              <div v-if="langMenuOpen" class="lang-menu" role="menu">
                <button
                  v-for="opt in languageOptions"
                  :key="opt.value"
                  class="lang-option"
                  type="button"
                  role="menuitem"
                  @click="selectLang(opt.value)"
                >
                  <img :src="opt.flag" class="lang-flag" :alt="opt.label" />
                  <span>{{ opt.label }}</span>
                  <Icon v-if="opt.value === lang" name="mdi:check" size="1.1em" class="lang-check" />
                </button>
              </div>
            </div>
          </div>

          <!-- ✅ (CIUDAD FIJA) Se elimina selector y cualquier control para cambiar ciudad -->

          <!-- GOOGLE CITY: AUTOCOMPLETE DIRECCION -->
          <div class="search-wrapper" v-if="isGoogleCity">
            <AutoComplete
              v-model="addressQuery"
              :suggestions="suggestions"
              optionLabel="description"
              :placeholder="t('type_address')"
              class="w-full"
              :minLength="3"
              :delay="250"
              @complete="onAddressComplete"
              @item-select="onSelectSuggestionEvent"
              dropdown
            >
              <template #item="{ item }">
                <div class="ac-item">
                  <Icon name="mdi:map-marker-outline" class="item-icon" />
                  <span>{{ item.description }}</span>
                </div>
              </template>
            </AutoComplete>
          </div>

          <!-- PARAMS CITY: BARRIOS + DIRECCION EXACTA -->
          <div v-if="isParamsCity" class="params-box">
            <div class="form-group">
              <label class="city-label">{{ t('neighborhood_sector') }}</label>

              <AutoComplete
                v-model="selectedNeighborhood"
                :suggestions="nbSuggestions"
                optionLabel="name"
                class="w-full"
                :minLength="1"
                :delay="150"
                :disabled="loadingNeighborhoods || neighborhoods.length === 0"
                :placeholder="loadingNeighborhoods ? t('loading_neighborhoods') : (neighborhoods.length ? t('type_to_search') : t('no_neighborhoods'))"
                @complete="onNeighborhoodComplete"
                dropdown
                style="width: 100%;"
                forceSelection
              >
                <template #item="{ item }">
                  <div class="ac-item">
                    <Icon name="mdi:map-marker-radius-outline" class="item-icon" />
                    <span>{{ item.name }}</span>
                  </div>
                </template>
              </AutoComplete>
            </div>

            <div class="form-group" style="margin-top:.7rem;">
              <label class="city-label">{{ t('exact_address') }}</label>
              <InputText
                style="width: 100%;"
                v-model="paramExactAddress"
                class="w-full"
                :placeholder="t('exact_address_ph')"
              />
            </div>
          </div>
        </header>

        <!-- RESULTADO GOOGLE -->
        <section v-if="coverageResult && isGoogleCity" class="coverage-card">
          <div class="coverage-header">
            <Icon name="mdi:map-marker-check" size="1.4em" class="coverage-icon" />
            <h3 class="coverage-title">{{ t('search_result') }}</h3>
          </div>

          <div class="coverage-body">
            <div class="coverage-row">
              <span class="coverage-label">{{ t('address') }}</span>
              <span class="coverage-value address-text">{{ coverageResult.formatted_address }}</span>
            </div>

            <div class="coverage-row">
              <span class="coverage-label">{{ t('nearest_store') }}</span>
              <span class="coverage-value">
                {{ coverageResult.nearest?.site?.site_name || t('na') }}
                <small v-if="coverageResult.nearest">
                  ({{ Number(coverageResult.nearest.distance_km || 0).toFixed(1) }} km)
                </small>
              </span>
            </div>

            <div class="coverage-row highlight">
              <span class="coverage-label">{{ t('delivery_cost') }}</span>
              <span class="coverage-value price">{{ formatCOP(coverageResult.delivery_cost_cop) }}</span>
            </div>

            <div class="coverage-status-text" :class="coverageResult.nearest?.in_coverage ? 'text-ok' : 'text-fail'">
              {{ coverageResult.nearest?.in_coverage ? t('in_coverage') : t('out_of_coverage') }}
            </div>
          </div>

          <div class="coverage-actions" v-if="coverageResult.nearest">
            <Button
              v-if="coverageResult.nearest?.in_coverage && getExactOrderType(coverageResult.nearest.site.site_id, 3)"
              class="btn-action btn-delivery"
              @click="dispatchToSite(
                getStoreById(coverageResult.nearest.site.site_id) || coverageResult.nearest.site,
                getExactOrderType(coverageResult.nearest.site.site_id, 3),
                { mode: 'gmaps', coverageData: coverageResult, city: selectedCityObj }
              )"
            >
              <template #icon>
                <Icon name="mdi:moped" size="1.2em" />
              </template>
              <span>{{ t('delivery') }}</span>
            </Button>
          </div>
        </section>

        <!-- RESULTADO PARAMS -->
        <section v-if="isParamsCity && selectedNeighborhood" class="coverage-card">
          <div class="coverage-header">
            <Icon name="mdi:home-map-marker" size="1.4em" class="coverage-icon" />
            <h3 class="coverage-title">{{ t('your_zone_by_neighborhood') }}</h3>
          </div>

          <div class="coverage-body">
            <div class="coverage-row">
              <span class="coverage-label">{{ t('neighborhood') }}</span>
              <span class="coverage-value">{{ selectedNeighborhood?.name || '—' }}</span>
            </div>

            <div class="coverage-row highlight">
              <span class="coverage-label">{{ t('delivery_cost') }}</span>
              <span class="coverage-value price">{{ formatCOP(paramDeliveryPrice) }}</span>
            </div>

            <div class="coverage-status-text text-ok">{{ t('ready_to_send') }}</div>
          </div>

          <div class="coverage-actions">
            <Button
              class="btn-action btn-delivery"
              :disabled="!canDispatchParams"
              @click="onDispatchParamsDelivery"
            >
              <template #icon>
                <Icon name="mdi:moped" size="1.2em" />
              </template>
              <span>{{ t('delivery') }}</span>
            </Button>
          </div>
        </section>

        <!-- LISTA SEDES (scroll interno) -->
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
                :alt="t('store_photo_alt')"
              />
            </div>

            <div class="store-info">
              <h3 class="store-name">{{ store.name }}</h3>

              <p class="store-services">
                <span v-for="(ot, index) in getAvailableOrderTypes(store.id)" :key="ot.id">
                  {{ String(ot.name || '').toUpperCase() }}
                  <span v-if="index < getAvailableOrderTypes(store.id).length - 1"> | </span>
                </span>
              </p>

              <p class="store-address">
                {{ store.address }} – {{ store.city }}
              </p>

              <button class="store-action" :data-status="store.status || 'unknown'">
                <span v-if="store.status === 'open'" class="status-flex">
                  <Icon name="mdi:check-circle-outline" size="1.1em" /> {{ t('open') }}
                </span>
                <span v-else class="status-flex">{{ t('closed') }}</span>
              </button>
            </div>

            <button class="store-arrow" type="button">
              <Icon name="mdi:chevron-right" size="1.6em" />
            </button>
          </article>
        </main>
      </div>

      <!-- MODAL (PrimeVue Dialog) -->
      <Dialog
        v-model:visible="isModalOpen"
        modal
        dismissableMask
        :style="{ width: 'min(92vw, 520px)' }"
        :contentStyle="{ minHeight: '70vh' }"
        :showHeader="false"
      >
        <div v-if="modalStore" class="pv-modal">
          <button class="modal-close-btn" type="button" @click="closeModal">
            <Icon name="mdi:close" size="1.5em" />
          </button>

          <!-- STEP 1 -->
          <div v-if="modalStep === 1">
            <h3 class="modal-title">{{ t('how_want_order') }}</h3>
            <p class="modal-subtitle">{{ t('store_label') }} <strong>{{ modalStore.name }}</strong></p>

            <div class="modal-actions">
              <Button
                v-for="ot in getAvailableOrderTypes(modalStore.id)"
                :key="ot.id"
                class="modal-btn"
                :class="getButtonClass(ot.id)"
                @click="handleModalOption(ot)"
                severity="secondary"
              >
                <Icon :name="getIconForOrderType(ot.id)" size="1.8em" />
                <span>{{ lang === 'en' ? tOrderTypeName(ot) : ot.name }}</span>
              </Button>
            </div>
          </div>

          <!-- STEP 2 -->
          <div v-else-if="modalStep === 2">
            <div class="modal-header-nav">
              <Button text class="modal-back-btn" @click="setModalStep(1)">
                <Icon name="mdi:arrow-left" size="1.2em" />
                <span>{{ t('back') }}</span>
              </Button>
            </div>

            <!-- GOOGLE MODAL -->
            <div v-if="isGoogleCity">
              <h3 class="modal-title">{{ t('where_are_you') }}</h3>

              <AutoComplete
                v-model="modalAddressQuery"
                :suggestions="modalSuggestions"
                optionLabel="description"
                :placeholder="t('modal_address_ph')"
                class="w-full"
                :minLength="3"
                style="width: 100%;"
                :delay="250"
                @complete="onModalAddressComplete"
                @item-select="onSelectModalSuggestionEvent"
                dropdown
              >
                <template #item="{ item }">
                  <div class="ac-item">
                    <Icon name="mdi:map-marker-outline" class="item-icon" />
                    <span>{{ item.description }}</span>
                  </div>
                </template>
              </AutoComplete>

              <div v-if="modalAddressError" class="modal-error">{{ modalAddressError }}</div>
            </div>

            <!-- PARAMS MODAL -->
            <div v-else class="params-flow-modal">
              <h3 class="modal-title">{{ t('delivery_details') }}</h3>

              <div class="form-group">
                <label class="city-label">{{ t('search_your_neighborhood') }}</label>

                <AutoComplete
                  v-model="modalSelectedNeighborhood"
                  :suggestions="modalNbSuggestions"
                  optionLabel="name"
                  class="w-full"
                  :placeholder="t('type_to_search')"
                  :minLength="1"
                  style="width:100%;"
                  :delay="150"
                  @complete="onModalNeighborhoodComplete"
                  dropdown
                  forceSelection
                />
              </div>

              <div v-if="modalSelectedNeighborhood" style="margin: 1rem 0;" class="selected-nb-info">
                <div class="info-row">
                  <span>{{ t('neighborhood') }} </span>
                  <strong>{{ modalSelectedNeighborhood.name }}</strong>
                </div>
                <div class="info-row">
                  <span>{{ t('delivery_cost') }} </span>
                  <strong class="text-green">{{ formatCOP(Number(modalSelectedNeighborhood.delivery_price || 0)) }}</strong>
                </div>
              </div>

              <div class="form-group" style="margin-top: 1rem;">
                <label class="city-label">{{ t('exact_address_modal') }}</label>
                <InputText
                  style="width: 100%;"
                  v-model="modalParamAddress"
                  class="w-full"
                  :placeholder="t('exact_address_modal_ph')"
                />
              </div>

              <Button
                class="btn-action btn-delivery full-width"
                style="margin-top: 1.5rem;"
                :disabled="!modalSelectedNeighborhood || !modalParamAddress.trim()"
                @click="onDispatchModalParams"
              >
                <template #icon>
                  <Icon name="mdi:moped" size="1.2em" />
                </template>
                <span>{{ t('confirm_delivery') }}</span>
              </Button>
            </div>
          </div>

          <!-- STEP 3 -->
          <div v-else-if="modalStep === 3" class="modal-loading-view">
            <ProgressSpinner style="width:48px;height:48px" />
            <p>{{ t('validating_coverage') }}</p>
          </div>

          <!-- STEP 4 -->
          <div v-else-if="modalStep === 4 && modalCoverageResult">
            <div class="modal-header-nav">
              <Button text class="modal-back-btn" @click="setModalStep(2)">
                <template #icon>
                  <Icon name="mdi:arrow-left" size="1.2em" />
                </template>
                <span>{{ t('back') }}</span>
              </Button>
            </div>

            <h3 class="modal-title">{{ t('coverage_summary') }}</h3>

            <div class="coverage-card" style="margin: 1rem 0; width: auto; border: none; box-shadow: none; background: transparent;">
              <div class="coverage-body" style="padding: 0; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem;">
                <div class="coverage-row">
                  <span class="coverage-label">{{ t('address') }}</span>
                  <span class="coverage-value address-text">{{ modalCoverageResult.formatted_address }}</span>
                </div>

                <div class="coverage-row">
                  <span class="coverage-label">{{ t('assigned_store') }}</span>
                  <span class="coverage-value">
                    {{ modalCoverageResult.nearest?.site?.site_name || t('na') }}
                    <small v-if="modalCoverageResult.nearest">
                      ({{ Number(modalCoverageResult.nearest.distance_km || 0).toFixed(1) }} km)
                    </small>
                  </span>
                </div>

                <div class="coverage-row highlight">
                  <span class="coverage-label">{{ t('delivery_cost') }}</span>
                  <span class="coverage-value price">{{ formatCOP(modalCoverageResult.delivery_cost_cop) }}</span>
                </div>

                <div class="coverage-status-text" :class="modalCoverageResult.nearest?.in_coverage ? 'text-ok' : 'text-fail'">
                  {{ modalCoverageResult.nearest?.in_coverage ? t('in_coverage') : t('out_of_coverage') }}
                </div>
              </div>
            </div>

            <Button
              class="btn-action btn-delivery full-width"
              style="margin-top: 1rem;"
              :disabled="!modalCoverageResult.nearest?.in_coverage"
              @click="confirmGoogleDispatch"
            >
              <template #icon>
                <Icon name="mdi:check-circle-outline" size="1.2em" />
              </template>
              <span>{{ t('confirm_and_go') }}</span>
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import 'leaflet/dist/leaflet.css'

/* PrimeVue */
import Dialog from 'primevue/dialog'
import AutoComplete from 'primevue/autocomplete'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'

/* =======================
   ✅ I18N LOCAL (sin Pinia)
   ======================= */
const LANG_KEY = 'vicio_lang'
const lang = ref('es')
const langMenuOpen = ref(false)
const langWrapRef = ref(null)

const languageOptions = [
  { value: 'es', label: 'Español', flag: 'https://flagcdn.com/h20/es.png' },
  { value: 'en', label: 'English', flag: 'https://flagcdn.com/h20/us.png' }
]

const currentLang = computed(() => languageOptions.find(o => o.value === lang.value) || languageOptions[0])

const texts = {
  es: {
    language: 'Idioma',
    redirect_title: 'Te estamos llevando a',
    redirect_subtitle: 'Iniciando tu experiencia...',
    choose_nearest: 'ELIGE TU SALCHIMONSTER MÁS CERCANO',
    type_address: 'Escribe tu dirección...',
    neighborhood_sector: 'Barrio / Sector',
    loading_neighborhoods: 'Cargando barrios...',
    type_to_search: 'Escribe para buscar...',
    no_neighborhoods: 'No hay barrios',
    exact_address: 'Dirección exacta',
    exact_address_ph: 'Ej: Calle 123 # 45 - 67...',
    search_result: 'Resultado de búsqueda',
    address: 'Dirección:',
    nearest_store: 'Sede más cercana:',
    assigned_store: 'Sede asignada:',
    delivery_cost: 'Costo envío:',
    in_coverage: '✅ Cubrimos tu zona',
    out_of_coverage: '❌ Fuera de zona de entrega',
    delivery: 'Domicilio',
    your_zone_by_neighborhood: 'Tu zona (Por Barrios)',
    ready_to_send: '✅ Listo para enviar',
    store_photo_alt: 'Foto sede',
    open: 'Abierto',
    closed: 'Cerrado',
    how_want_order: '¿Cómo quieres tu pedido?',
    store_label: 'Sede:',
    back: 'Volver',
    where_are_you: '¿Dónde estás?',
    modal_address_ph: 'Calle 123 # 45 - 67...',
    delivery_details: 'Datos de Entrega',
    search_your_neighborhood: 'Busca tu Barrio',
    neighborhood: 'Barrio:',
    exact_address_modal: 'Dirección Exacta',
    exact_address_modal_ph: 'Ej: Calle 123 # 45 - 67 Apt 201',
    confirm_delivery: 'Confirmar Domicilio',
    validating_coverage: 'Validando cobertura...',
    coverage_summary: 'Resumen de Cobertura',
    confirm_and_go: 'Confirmar e Ir',
    na: 'N/A',

    // Mensajes/errores
    delivery_not_available_store: 'El servicio de domicilio no está disponible en esta sede.',
    error_validating_address: 'Error validando dirección.',
    nb_assigned_no_delivery: 'La sede asignada a este barrio no tiene servicio de domicilio activo.',
    could_not_determine_order_type: 'Error: No se pudo determinar el tipo de orden para domicilio.',
    transfer_error: 'Error al transferir. Intenta de nuevo.',
    this_store_no_delivery: 'Esta sede no tiene habilitado domicilio.'
  },
  en: {
    language: 'Language',
    redirect_title: 'Taking you to',
    redirect_subtitle: 'Starting your experience...',
    choose_nearest: 'CHOOSE YOUR NEAREST SALCHIMONSTER',
    type_address: 'Type your address...',
    neighborhood_sector: 'Neighborhood / Area',
    loading_neighborhoods: 'Loading neighborhoods...',
    type_to_search: 'Type to search...',
    no_neighborhoods: 'No neighborhoods available',
    exact_address: 'Exact address',
    exact_address_ph: 'E.g. 123 Main St...',
    search_result: 'Search result',
    address: 'Address:',
    nearest_store: 'Nearest store:',
    assigned_store: 'Assigned store:',
    delivery_cost: 'Delivery fee:',
    in_coverage: '✅ We deliver to your area',
    out_of_coverage: '❌ Out of delivery area',
    delivery: 'Delivery',
    your_zone_by_neighborhood: 'Your area (By neighborhood)',
    ready_to_send: '✅ Ready to deliver',
    store_photo_alt: 'Store photo',
    open: 'Open',
    closed: 'Closed',
    how_want_order: 'How would you like your order?',
    store_label: 'Store:',
    back: 'Back',
    where_are_you: 'Where are you?',
    modal_address_ph: '123 Main St...',
    delivery_details: 'Delivery details',
    search_your_neighborhood: 'Find your neighborhood',
    neighborhood: 'Neighborhood:',
    exact_address_modal: 'Exact address',
    exact_address_modal_ph: 'E.g. 123 Main St Apt 201',
    confirm_delivery: 'Confirm delivery',
    validating_coverage: 'Validating coverage...',
    coverage_summary: 'Coverage summary',
    confirm_and_go: 'Confirm and go',
    na: 'N/A',

    // Messages/errors
    delivery_not_available_store: 'Delivery is not available at this store.',
    error_validating_address: 'Error validating address.',
    nb_assigned_no_delivery: 'The store assigned to this neighborhood does not have delivery enabled.',
    could_not_determine_order_type: 'Error: Could not determine delivery order type.',
    transfer_error: 'Transfer failed. Please try again.',
    this_store_no_delivery: 'This store does not have delivery enabled.'
  }
}

function t(key) {
  return (texts[lang.value] && texts[lang.value][key]) ? texts[lang.value][key] : key
}

function toggleLangMenu() {
  langMenuOpen.value = !langMenuOpen.value
}
function selectLang(v) {
  lang.value = v
  langMenuOpen.value = false
}

function onOutsideClick(e) {
  const el = langWrapRef.value
  if (!el) return
  if (!el.contains(e.target)) langMenuOpen.value = false
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    const saved = window.localStorage.getItem(LANG_KEY)
    if (saved === 'es' || saved === 'en') lang.value = saved
    window.addEventListener('click', onOutsideClick, true)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('click', onOutsideClick, true)
  }
})

watch(lang, (v) => {
  if (typeof window !== 'undefined') window.localStorage.setItem(LANG_KEY, v)
})

/* Si en tu backend los order_types vienen en ES, este helper traduce los “clásicos” en modal */
function tOrderTypeName(ot) {
  const id = Number(ot?.id)
  if (id === 3) return t('delivery')
  if (id === 2) return 'Pickup'
  if (id === 6) return 'Dine-in'
  return ot?.name || ''
}

/* =======================
   CONFIG & STATE
   ======================= */
const route = useRoute()
const BACKEND_BASE = 'https://backend.salchimonster.com'
const LOCATIONS_BASE = 'https://api.locations.salchimonster.com'
const URI = 'https://backend.salchimonster.com'
const MAIN_DOMAIN = 'salchimonster.com'

const FIXED_CITY_ID = 15 // ✅ CIUDAD FIJA

const map = ref(null)
const leafletModule = ref(null)
const markers = ref({})
const mapBounds = ref(null)
const initialBounds = ref(null)

const stores = ref([])
const cities = ref([])
const sitePaymentsConfig = ref([])
const cityMapStatus = ref([])

/* ✅ ciudad fija: 15 */
const selectedCityId = ref(FIXED_CITY_ID)
const selectedStoreId = ref(null)

const sessionToken = ref((typeof crypto !== 'undefined' && crypto.randomUUID)
  ? crypto.randomUUID()
  : Math.random().toString(36).substring(2)
)

const isRedirecting = ref(false)
const targetSiteName = ref('')

/* =======================
   ✅ App-like: bloquear scroll global + zoom del navegador
   ======================= */
const preventGesture = (e) => { try { e.preventDefault() } catch {} }
const preventCtrlWheelZoom = (e) => { if (e.ctrlKey) { try { e.preventDefault() } catch {} } }

function lockPage() {
  if (typeof window === 'undefined') return
  document.documentElement.classList.add('no-global-scroll')
  document.body.classList.add('no-global-scroll')
  window.addEventListener('gesturestart', preventGesture, { passive: false })
  window.addEventListener('gesturechange', preventGesture, { passive: false })
  window.addEventListener('gestureend', preventGesture, { passive: false })
  window.addEventListener('wheel', preventCtrlWheelZoom, { passive: false })
}

function unlockPage() {
  if (typeof window === 'undefined') return
  document.documentElement.classList.remove('no-global-scroll')
  document.body.classList.remove('no-global-scroll')
  window.removeEventListener('gesturestart', preventGesture)
  window.removeEventListener('gesturechange', preventGesture)
  window.removeEventListener('gestureend', preventGesture)
  window.removeEventListener('wheel', preventCtrlWheelZoom)
}

/* =======================
   ✅ MOBILE DETECTOR + COLLAPSE MAP
   ======================= */
const isMobile = ref(false)
let mq

function updateIsMobile() {
  if (typeof window === 'undefined') return
  isMobile.value = mq ? mq.matches : window.matchMedia('(max-width: 900px)').matches
}

onMounted(() => {
  lockPage()
  if (typeof window === 'undefined') return
  mq = window.matchMedia('(max-width: 900px)')
  updateIsMobile()
  if (mq.addEventListener) mq.addEventListener('change', updateIsMobile)
  else mq.addListener(updateIsMobile)
})

onBeforeUnmount(() => {
  unlockPage()
  if (!mq) return
  if (mq.removeEventListener) mq.removeEventListener('change', updateIsMobile)
  else mq.removeListener(updateIsMobile)
})

/* =======================
   CITY (fija)
   ======================= */
const selectedCityObj = computed(() => {
  return cities.value.find((c) => Number(c.city_id) === Number(FIXED_CITY_ID)) || null
})

/* =======================
   Google Sidebar
   ======================= */
const addressQuery = ref('')
const suggestions = ref([])
const coverageResult = ref(null)
const dropoffMarker = ref(null)
let dropoffIcon = null

function normalizePredictions(predictions) {
  return (predictions || []).map((p) => ({
    place_id: p.place_id,
    description: p.description,
  }))
}

async function onAddressComplete(e) {
  coverageResult.value = null
  const q = (e.query || '').trim()
  if (q.length < 3) {
    suggestions.value = []
    return
  }

  try {
    const params = new URLSearchParams({
      input: q,
      language: lang.value === 'en' ? 'en' : 'es',
      countries: 'co',
      limit: '5',
      session_token: sessionToken.value
    })

    // ✅ ciudad fija: agrega el nombre si existe
    const c = cities.value.find((x) => Number(x.city_id) === Number(FIXED_CITY_ID))
    if (c) params.append('city', c.city_name)

    const res = await fetch(`${LOCATIONS_BASE}/places/autocomplete?${params}`)
    const data = await res.json()
    suggestions.value = normalizePredictions(data.predictions)
  } catch {
    suggestions.value = []
  }
}

function onSelectSuggestionEvent(ev) {
  const item = ev.value
  if (!item?.place_id) return
  addressQuery.value = item.description
  suggestions.value = []
  fetchCoverageDetails(item.place_id)
}

async function fetchCoverageDetails(placeId) {
  try {
    const res = await fetch(
      `${LOCATIONS_BASE}/places/coverage-details?place_id=${placeId}&session_token=${sessionToken.value}&language=${lang.value === 'en' ? 'en' : 'es'}`
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
   Barrios Sidebar
   ======================= */
const neighborhoods = ref([])
const loadingNeighborhoods = ref(false)
const selectedNeighborhood = ref(null)
const nbSuggestions = ref([])
const paramExactAddress = ref('')

const paramDeliveryPrice = computed(() => Number(selectedNeighborhood.value?.delivery_price ?? 0))

const paramAssignedStore = computed(() => {
  const nb = selectedNeighborhood.value
  if (!nb?.site_id) return null
  return getStoreById(Number(nb.site_id)) || null
})

const canDispatchParams = computed(() => {
  if (!isParamsCity.value) return false
  if (!selectedNeighborhood.value) return false
  if (!paramExactAddress.value.trim()) return false
  const store = paramAssignedStore.value
  if (!store) return false
  return !!getExactOrderType(store.id, 3)
})

async function onNeighborhoodComplete(e) {
  const q = (e.query || '').trim().toLowerCase()
  const base = neighborhoods.value || []
  nbSuggestions.value = !q
    ? base.slice(0, 50)
    : base.filter((n) => (n.name || '').toLowerCase().includes(q)).slice(0, 50)
}

async function loadNeighborhoodsByCity(cityId) {
  loadingNeighborhoods.value = true
  neighborhoods.value = []
  selectedNeighborhood.value = null
  nbSuggestions.value = []
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
   MODAL STATE
   ======================= */
const isModalOpen = ref(false)
const modalStore = ref(null)
const modalStep = ref(1)

const modalAddressQuery = ref('')
const modalSuggestions = ref([])
const modalCoverageResult = ref(null)
const modalAddressError = ref('')

const modalSelectedNeighborhood = ref(null)
const modalNbSuggestions = ref([])
const modalParamAddress = ref('')

/* =======================
   CITY MAP STATUS
   ======================= */
function isGoogleMapsEnabled(cityId) {
  // const config = cityMapStatus.value.find((c) => Number(c.city_id) === Number(cityId))
  return true
  // return config ? !!config.user_google_map_status : false
}

const isGoogleCity = computed(() => {
  const cityId = modalStore.value
    ? (modalStore.value.cityId || modalStore.value.city_id)
    : FIXED_CITY_ID
  return !!Number(cityId) && isGoogleMapsEnabled(Number(cityId))
})
const isParamsCity = computed(() => !isGoogleCity.value)

/* ✅ colapsa el mapa cuando ya hay selección (o modal abierto) en móvil */
const shouldCollapseMap = computed(() => {
  if (!isMobile.value) return false
  const sidebarHasResult =
    (!!coverageResult.value && isGoogleCity.value) ||
    (!!selectedNeighborhood.value && isParamsCity.value)
  const modalIsOpen = !!isModalOpen.value
  return sidebarHasResult || modalIsOpen
})

watch(shouldCollapseMap, async (collapsed) => {
  if (!collapsed) {
    await nextTick()
    setTimeout(() => {
      try {
        map.value?.invalidateSize?.()
        if (initialBounds.value) map.value?.fitBounds?.(initialBounds.value, { padding: [20, 20] })
      } catch {}
    }, 380)
  }
})

/* =======================
   MODAL LOGIC
   ======================= */
async function openModal(store) {
  selectedStoreId.value = store.id
  modalStore.value = store
  modalStep.value = 1
  isModalOpen.value = true

  modalAddressQuery.value = ''
  modalSuggestions.value = []
  modalCoverageResult.value = null
  modalAddressError.value = ''

  modalSelectedNeighborhood.value = null
  modalNbSuggestions.value = []
  modalParamAddress.value = ''

  const cityId = store.cityId || store.city_id
  if (cityId && !isGoogleMapsEnabled(cityId)) {
    if (neighborhoods.value.length === 0) {
      await loadNeighborhoodsByCity(cityId)
    }
  }
}

function closeModal() {
  isModalOpen.value = false
  modalStore.value = null
}

function setModalStep(step) {
  modalStep.value = step
}

async function handleModalOption(orderType) {
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

async function onModalAddressComplete(e) {
  const q = (e.query || '').trim()
  if (q.length < 3) {
    modalSuggestions.value = []
    return
  }

  try {
    const params = new URLSearchParams()
    params.append('input', q)
    params.append('language', lang.value === 'en' ? 'en' : 'es')
    params.append('countries', 'co')
    params.append('limit', '4')
    params.append('session_token', sessionToken.value)
    if (modalStore.value?.city) params.append('city', modalStore.value.city)

    const res = await fetch(`${LOCATIONS_BASE}/places/autocomplete?${params}`)
    const data = await res.json()
    modalSuggestions.value = normalizePredictions(data.predictions)
  } catch {
    modalSuggestions.value = []
  }
}

function onSelectModalSuggestionEvent(ev) {
  const item = ev.value
  if (!item?.place_id) return
  onSelectModalSuggestion(item)
}

async function onSelectModalSuggestion(s) {
  modalAddressQuery.value = s.description
  modalStep.value = 3

  try {
    const params = new URLSearchParams({
      place_id: s.place_id,
      session_token: sessionToken.value,
      language: lang.value === 'en' ? 'en' : 'es'
    })
    const res = await fetch(`${LOCATIONS_BASE}/places/coverage-details?${params}`)
    const data = await res.json()

    modalCoverageResult.value = data

    const ot = getExactOrderType(modalStore.value.id, 3)
    if (ot) {
      modalStep.value = 4
    } else {
      modalAddressError.value = t('delivery_not_available_store')
      modalStep.value = 2
    }
  } catch {
    modalAddressError.value = t('error_validating_address')
    modalStep.value = 2
  }
}

async function onModalNeighborhoodComplete(e) {
  const q = (e.query || '').trim().toLowerCase()
  const base = neighborhoods.value || []
  modalNbSuggestions.value = !q
    ? base.slice(0, 50)
    : base.filter((n) => (n.name || '').toLowerCase().includes(q)).slice(0, 50)
}

function onDispatchModalParams() {
  if (!modalSelectedNeighborhood.value || !modalParamAddress.value.trim()) return

  const assignedSiteId = modalSelectedNeighborhood.value.site_id
  let targetStore = getStoreById(Number(assignedSiteId))
  if (!targetStore) targetStore = modalStore.value

  const ot = getExactOrderType(targetStore.id, 3)
  if (!ot) {
    alert(t('nb_assigned_no_delivery'))
    return
  }

  dispatchToSite(targetStore, ot, {
    mode: 'params',
    city: selectedCityObj.value,
    neighborhood: modalSelectedNeighborhood.value,
    exactAddress: modalParamAddress.value
  })
}

function confirmGoogleDispatch() {
  if (!modalCoverageResult.value) return

  const siteId = modalCoverageResult.value.nearest?.site?.site_id || modalStore.value.id
  let targetStore = getStoreById(Number(siteId))
  if (!targetStore) targetStore = modalStore.value

  const ot = getExactOrderType(targetStore.id, 3)
  if (ot) {
    dispatchToSite(targetStore, ot, {
      mode: 'gmaps',
      coverageData: modalCoverageResult.value,
      city: selectedCityObj.value
    })
  } else {
    alert(t('could_not_determine_order_type'))
  }
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
    cities.value = (await res.json()).filter((c) => c.visible !== false)
  } catch {}
}

async function loadStores() {
  try {
    const res = await fetch(`${BACKEND_BASE}/sites`)
    const data = await res.json()
    stores.value = data
      .filter((s) =>
        s.show_on_web &&
        s.time_zone === 'America/New_York' &&
        s.site_id != 32 &&
        Number(s.city_id) === Number(FIXED_CITY_ID) // ✅ SOLO CIUDAD 15
      )
      .map((s) => ({
        id: s.site_id,
        name: `SALCHIMONSTER ${s.site_name}`,
        city: s.city_name,
        cityId: s.city_id,
        address: s.site_address || (lang.value === 'en' ? 'Address pending' : 'Dirección pendiente'),
        lat: s.location?.[0] || 40.7128,
        lng: s.location?.[1] || -74.0060,
        subdomain: s.subdomain,
        img_id: s.img_id,
        status: 'unknown'
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
function getAvailableOrderTypes(siteId) {
  const config = sitePaymentsConfig.value.find((s) => String(s.site_id) === String(siteId))
  if (!config || !config.order_types) return []
  return config.order_types.filter((ot) => ot.methods && ot.methods.length > 0)
}
function getExactOrderType(siteId, typeId) {
  const available = getAvailableOrderTypes(siteId)
  return available.find((ot) => Number(ot.id) === Number(typeId)) || null
}
function getIconForOrderType(id) {
  if (Number(id) === 3) return 'mdi:moped'
  if (Number(id) === 2) return 'mdi:shopping-outline'
  if (Number(id) === 6) return 'mdi:silverware-fork-knife'
  return 'mdi:star'
}
function getButtonClass(id) {
  if (Number(id) === 3) return 'modal-btn--delivery'
  return 'modal-btn--pickup'
}

/* =======================
   DISPATCH
   ======================= */
async function dispatchToSite(manualStore, orderTypeObj, extra = { mode: 'simple' }) {
  isRedirecting.value = true
  let targetStore = manualStore
  targetSiteName.value = targetStore?.name || targetStore?.site_name || 'Nueva Sede'
  const targetCityId = targetStore.cityId || targetStore.city_id
  const useGoogleMaps = isGoogleMapsEnabled(Number(targetCityId))
  const isDelivery = Number(orderTypeObj?.id) === 3

  try {
    const hash = (typeof crypto !== 'undefined' && crypto.randomUUID)
      ? crypto.randomUUID()
      : Date.now().toString(36).substring(2)

    let userSiteData = null
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

    const payload = {
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

    const params = new URLSearchParams()
    params.append('hash', hash)
    if (route.query.inserted_by) params.append('inserted_by', String(route.query.inserted_by))
    if (route.query.token) params.append('token', String(route.query.token))
    if (route.query.iframe) params.append('iframe', String(route.query.iframe))

    window.location.href = `${baseUrl}/?${params.toString()}`
  } catch (error) {
    console.error(error)
    isRedirecting.value = false
    alert(t('transfer_error'))
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
  if (!ot) { alert(t('this_store_no_delivery')); return }

  dispatchToSite(store, ot, {
    mode: 'params',
    city: selectedCityObj.value,
    neighborhood: selectedNeighborhood.value,
    exactAddress: paramExactAddress.value
  })
}

/* =======================
   IMAGES
   ======================= */
const imgCache = ref({})
const currentImage = (store) => imgCache.value[store.id] || `${BACKEND_BASE}/read-product-image/96/site-${store.id}`
const loadHighResImage = (store) => {
  const i = new Image()
  i.src = `${BACKEND_BASE}/read-product-image/600/site-${store.id}`
  i.onload = () => { imgCache.value[store.id] = i.src }
}
const onImgError = (store) => { imgCache.value[store.id] = `${BACKEND_BASE}/read-product-image/96/site-${store.id}` }

/* =======================
   UTILS
   ======================= */
function getStoreById(id) { return stores.value.find(s => Number(s.id) === Number(id)) }
function formatCOP(v) {
  return v != null
    ? new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
    : ''
}

/* =======================
   MAPA + FILTROS
   ======================= */
const filteredStores = computed(() => {
  let base = stores.value

  if (mapBounds.value) {
    base = base.filter((s) =>
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

onMounted(async () => {
  await Promise.all([loadPaymentConfig(), loadCityMapStatus()])
  await Promise.all([loadCities(), loadStores()])
  await loadStatuses()

  // ✅ si esta ciudad NO usa Google Maps, precargar barrios una sola vez
  if (!isGoogleMapsEnabled(FIXED_CITY_ID)) {
    await loadNeighborhoodsByCity(FIXED_CITY_ID)
  }

  const mod = await import('leaflet')
  const L = mod.default ?? mod
  leafletModule.value = L

  const nycBounds = L.latLngBounds(
    L.latLng(39.85, -75.30),
    L.latLng(40.95, -73.70)
  )

  map.value = L.map('vicio-map', {
    center: [40.7128, -74.0060],
    zoom: 12,
    minZoom: 2,
    maxZoom: 16,
    maxBounds: nycBounds,
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

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap' }).addTo(map.value)

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
  stores.value.forEach((s) => {
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
    initialBounds.value = nycBounds
    map.value.fitBounds(nycBounds, { padding: [40, 40] })
  }

  map.value.on('moveend', updateBounds)
  updateBounds()
})
</script>

<style scoped>
/* (Tu CSS original tal cual, sin cambios) */
/* =========================
   ✅ GLOBAL: sin scroll global (app-like)
   ========================= */
:global(html.no-global-scroll),
:global(body.no-global-scroll) {
  height: 100%;
  overflow: hidden !important;
  overscroll-behavior: none;
}

:global(body.no-global-scroll) { margin: 0; }
:global(html.no-global-scroll) { -webkit-text-size-adjust: 100%; }

.vicio-root { width: 100%; height: 100%; }
.vicio-page {
  display: flex;
  width: 100%;
  height: 100dvh;
  max-height: 100dvh;
  overflow: hidden;
  background: var(--bg-page);
  color: var(--text-primary);
  font-family: 'Roboto', sans-serif;
  touch-action: none;
}

.vicio-map-shell {
  flex: 1 1 55%;
  height: 100%;
  background: #e2e8f0;
  overflow: hidden;
  position: relative;
}
.vicio-map {
  width: 100%;
  height: 100%;
  background: #e2e8f0;
  touch-action: none;
}

.vicio-sidebar {
  flex: 1 1 45%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-left: 1px solid var(--border-subtle);
  box-shadow: -5px 0 25px rgba(0, 0, 0, 0.05);
  height: 100%;
  overflow: hidden;
}

.sidebar-header {
  padding: 1.4rem 1.8rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  position: relative;
  z-index: 5;
}

/* ✅ NUEVO: fila superior con selector de idioma */
.sidebar-top-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: .75rem;
  margin-bottom: .9rem;
}

.sidebar-title {
  font-size: 0.82rem;
  letter-spacing: 0.18em;
  font-weight: 800;
  margin: 0;
  text-transform: uppercase;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex: 1;
}
.sidebar-title::before { content: "🔥"; font-size: 1rem; }

.city-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-soft);
  margin-bottom: 0.35rem;
}

.search-wrapper { position: relative; display: flex; flex-direction: column; gap: 0.25rem; }
.params-box { margin-top: .6rem; }

.ac-item { display: flex; align-items: center; gap: .55rem; }
.item-icon { color: var(--text-soft); font-size: 1.1em; }

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
.coverage-actions { display: flex; gap: 0.8rem; padding: 0 1rem 1rem; flex-wrap: wrap; }

.btn-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.7rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  cursor: pointer;
  border: none;
  transition: transform 0.1s;
}
.btn-action:disabled { opacity: .55; cursor: not-allowed; }
.btn-action:active { transform: scale(0.97); }
.btn-delivery { background-color: #ff6600; color: #ffffff; box-shadow: 0 4px 10px rgba(255, 102, 0, 0.25); }
.btn-delivery:hover { background-color: #e65c00; }
.full-width { width: 100%; }

.stores-list {
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
  padding: 0.45rem 0 1.2rem;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
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
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, background 0.2s ease;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
  flex-shrink: 0;
}
.store-arrow:hover { background: #333333; transform: scale(1.1); }

:global(.leaflet-div-icon.fire-icon) { width: 42px !important; height: 42px !important; border: none; background: transparent; display: flex; align-items: center; justify-content: center; }
:global(.leaflet-div-icon.fire-icon .fire-img) { width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2)); }
:deep(.leaflet-tile) { filter: grayscale(100%) !important; }

.modal-close-btn { position: absolute; top: 10px; right: 10px; background: transparent; border: none; cursor: pointer; color: #94a3b8; padding: 5px; }
.modal-close-btn:hover { color: #ef4444; }

.modal-title {
  margin: 0 0 5px;
  font-size: 1.2rem;
  font-weight: 800;
  color: #1e293b;
  text-align: center;
  text-transform: uppercase;
  margin-top: 2rem;
}
.modal-subtitle { text-align: center; color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem; }

.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
.modal-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.1rem 1rem;
  border-radius: 12px;
  width: 100%;
  aspect-ratio: 1 / 1;
  border: 2px solid transparent;
  background: #f8fafc;
}
.modal-btn--delivery:hover { background: #fff7ed; border-color: #ff6600; color: #c2410c; }
.modal-btn--pickup:hover { background: #f0fdf4; border-color: #16a34a; color: #15803d; }

.modal-header-nav { margin-bottom: 0.8rem; }
.modal-back-btn { display: inline-flex; align-items: center; gap: 6px; margin: 1rem; }

.modal-error { margin-top: 10px; color: #ef4444; font-size: 0.85rem; text-align: center; }
.modal-loading-view { text-align: center; padding: 2rem 0; color: #64748b; }

.redirect-overlay { position: fixed; inset: 0; background: rgba(255,255,255,0.9); z-index: 10000; display: flex; align-items: center; justify-content: center; }
.redirect-content { text-align: center; animation: popIn 0.5s ease-out; }
.redirect-spinner { position: relative; display: inline-flex; margin-bottom: 2rem; color: #ff6600; }
.rocket-icon { z-index: 2; animation: rocketFloat 1.5s ease-in-out infinite alternate; color: #ff6600; }
.pulse-ring { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; border-radius: 50%; border: 2px solid #ff6600; opacity: 0; animation: pulse 2s infinite; }
.redirect-store { font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0.5rem 0; }
.redirect-subtitle { font-size: 1rem; color: #94a3b8; }

@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes rocketFloat { from { transform: translateY(0); } to { transform: translateY(-10px); } }
@keyframes pulse { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ✅ NUEVO: estilos selector de idioma */
.lang-wrap { position: relative; flex-shrink: 0; }
.lang-btn{
  display:flex;
  align-items:center;
  gap:.45rem;
  padding:.35rem .55rem;
  border-radius: .6rem;
  border: 1px solid #e2e8f0;
  background:#ffffff;
  cursor:pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.lang-btn:hover{ background:#f8fafc; }
.lang-flag{ width:18px; height:18px; border-radius: 999px; object-fit: cover; }
.lang-label{ font-size:.78rem; font-weight:800; color:#0f172a; }
.lang-chevron{ color:#64748b; }
.lang-menu{
  position:absolute;
  right:0;
  top: calc(100% + 8px);
  background:#ffffff;
  border:1px solid #e2e8f0;
  border-radius:.75rem;
  box-shadow: 0 12px 28px rgba(0,0,0,0.12);
  overflow:hidden;
  min-width: 160px;
  z-index: 50;
}
.lang-option{
  width:100%;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:.6rem;
  padding:.6rem .75rem;
  border:none;
  background:transparent;
  cursor:pointer;
  font-weight:800;
  color:#0f172a;
}
.lang-option:hover{ background:#f8fafc; }
.lang-check{ color:#16a34a; }

@media (max-width: 900px) {
  .vicio-page { flex-direction: column; }

  .vicio-map-shell {
    flex: 0 0 auto;
    height: 40%;
    width: 100%;
    z-index: 10;
    transition: height 0.38s ease, opacity 0.38s ease, transform 0.38s ease;
  }

  .vicio-sidebar {
    flex: 1 1 auto;
    height: 60%;
    width: 100%;
    overflow: hidden;
    border-radius: 1.5rem 1.5rem 0 0;
    margin-top: -1.5rem;
    z-index: 20;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
    transition: height 0.38s ease, border-radius 0.38s ease, margin-top 0.38s ease;
  }

  .vicio-page.is-map-collapsed .vicio-map-shell {
    height: 0% !important;
    opacity: 0;
    transform: translateY(-10px);
    pointer-events: none;
  }

  .vicio-page.is-map-collapsed .vicio-sidebar {
    height: 100% !important;
    margin-top: 0 !important;
    border-radius: 0 !important;
  }

  .store-img-wrapper { width: 70px; height: 70px; }
  .store-item { padding: 0.8rem 1rem; }
  .coverage-card { margin: 1rem; }
}
</style>
