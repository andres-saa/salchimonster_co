<template>
  <div class="checkout-page">
    <!-- ================== OVERLAY REDIRECCIÓN ================== -->
    <Transition name="fade">
      <div v-if="isRedirecting" class="redirect-overlay">
        <div class="redirect-content">
          <div class="redirect-spinner">
            <Icon name="mdi:rocket-launch-outline" size="3em" class="rocket-icon" />
            <div class="pulse-ring"></div>
          </div>
          <h2 class="redirect-title">Te estamos llevando a</h2>
          <h3 class="redirect-store">{{ targetSiteName }}</h3>
          <p class="redirect-subtitle">Transfiriendo tu pedido...</p>
        </div>
      </div>
    </Transition>

    <!-- ================== DIALOG GOOGLE (PrimeVue) ================== -->
    <Dialog
      v-model:visible="see_sites"
      modal
      :closable="false"
      :dismissableMask="true"
      :style="{ width: '32rem', maxWidth: '95vw' }"
      @hide="closeModal"
      class="pv-google-dialog"
    >
      <template #header>
        <div class="modal-header">
          <h3 class="modal-title">{{ t('site_selector') }}</h3>
          <Button class="btn-icon-close" text rounded @click="closeModal">
            <Icon name="mdi:close" size="20" />
          </Button>
        </div>
      </template>

      <div class="modal-body">
        <div class="search-box" :class="{ 'is-focused': !!addressQuery }">
          <Icon name="mdi:magnify" class="search-icon" />

          <InputText
            ref="addressInputRef"
            v-model="addressQuery"
            :placeholder="t('address_placeholder')"
            autocomplete="off"
            class="search-input"
            @input="onSearchInput"
          />

          <Button v-if="addressQuery" class="btn-clear" text rounded @click="clearSearch">
            <Icon name="mdi:close-circle" />
          </Button>
        </div>

        <ul
          v-if="showAddressSuggestions && dir_options.length > 0 && !tempSiteData?.site_id"
          class="suggestions-list"
        >
          <li v-for="item in dir_options" :key="item.place_id" @click="onAddressSelect(item)">
            <div class="suggestion-icon"><Icon name="mdi:map-marker-outline" /></div>
            <div class="suggestion-content">
              <span class="main">{{ item.structured_formatting?.main_text || item.description }}</span>
              <span class="sub">{{ item.structured_formatting?.secondary_text }}</span>
            </div>
          </li>
        </ul>

        <div v-if="isValidating" class="loading-state">
          <ProgressSpinner style="width: 32px; height: 32px" />
          <span>Verificando cobertura...</span>
        </div>

        <div
          v-if="tempSiteData?.status === 'checked' && !isValidating"
          class="result-card"
          :class="tempSiteData.in_coverage ? 'is-success' : 'is-error'"
        >
          <div class="result-header">
            <div class="status-icon">
              <Icon :name="tempSiteData.in_coverage ? 'mdi:check-bold' : 'mdi:map-marker-off'" />
            </div>
            <div class="status-text">
              <h4>{{ tempSiteData.in_coverage ? t('in_coverage') : t('not_in_coverage') }}</h4>
              <p>{{ tempSiteData.formatted_address }}</p>
            </div>
          </div>

          <div v-if="tempSiteData.in_coverage" class="result-details">
            <div class="detail-row">
              <span>{{ t('delivery_price') }}</span>
              <strong>{{ formatCOP(tempSiteData.delivery_cost_cop) }}</strong>
            </div>
            <div class="detail-row">
              <span>{{ t('distance') }}</span>
              <strong>{{ tempSiteData.distance_miles }} {{ t('km') }}</strong>
            </div>
            <div class="detail-row full">
              <span>{{ t('ships_from_site') }}</span>
              <strong>{{ tempSiteData.nearest?.site?.site_name }}</strong>
            </div>
          </div>

          <div v-else class="error-message">
            <p>{{ lang === 'en' ? tempSiteData.error?.message_en : tempSiteData.error?.message_es }}</p>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer">
          <Button class="btn btn-secondary" outlined @click="closeModal">
            {{ t('cancel') }}
          </Button>

          <Button
            class="btn btn-primary"
            @click="confirmSelection"
            :disabled="!tempSiteData?.in_coverage || isRedirecting"
          >
            {{ t('save') }}
          </Button>
        </div>
      </template>
    </Dialog>

    <!-- ================== PAGE ================== -->
    <div class="checkout-layout">
      <header class="page-header">
        <h1>{{ t('finalize_purchase') }}</h1>
      </header>

      <div class="checkout-grid">
        <div class="form-column">
          <!-- ================== TABS TIPO ORDEN ================== -->
          <div class="card card-tabs" v-if="computedOrderTypesVisible.length > 0">
            <div class="tabs-container">
              <label
                v-for="opt in computedOrderTypesVisible"
                :key="opt.id"
                class="tab-item"
                :class="{ 'is-active': orderTypeIdStr === String(opt.id) }"
              >
                <input
                  type="radio"
                  name="order_type"
                  :value="String(opt.id)"
                  v-model="orderTypeIdStr"
                  class="hidden-radio"
                />
                <span class="tab-label">
                  {{ opt.name }}
                </span>
              </label>
            </div>
          </div>
          <div v-else class="card" style="text-align:center; color: #666;">
            <p>{{ lang === 'en' ? 'Loading delivery options...' : 'Cargando opciones de entrega...' }}</p>
          </div>

          <!-- ================== DATOS PERSONALES ================== -->
          <section class="card form-section">
            <h2 class="section-title">Datos Personales</h2>

            <div class="form-row">
              <div class="form-group full">
                <label>{{ t('name') }}</label>
                <InputText class="input-modern" v-model="user.user.name" :placeholder="t('name')" />
              </div>
            </div>

            <div class="form-row split">
              <div class="form-group">
                <label>{{ t('phone') }}</label>

                <div class="phone-control">
                  <!-- ✅ PrimeVue Select con bandera + dialCode -->
                  <div class="country-select">
                    <Select
                      v-model="user.user.phone_code"
                      :options="countries"
                      optionLabel="name"
                      :placeholder="lang === 'en' ? '+1' : '+57'"
                      filter
                      :filterPlaceholder="t('search_country_or_code')"
                      class="pv-select pv-select-country"
                    >
                      <template #value="{ value, placeholder }">
                        <div class="pv-country-value" style="display:flex; gap:.35rem; align-items:center;">
                          <img v-if="value?.flag" :src="value.flag" alt="flag" class="flag-mini" />
                          <span class="pv-country-dial">{{ value?.dialCode || placeholder }}</span>
                        </div>
                      </template>

                      <template #option="{ option }">
                        <div class="pv-country-option" style="display:flex; gap:.35rem; align-items:center;">
                          <img :src="option.flag" class="flag-mini" alt="flag" />
                          <span class="pv-country-name">{{ option.name }}</span>
                          <small class="pv-country-code"> ({{ option.dialCode }})</small>
                        </div>
                      </template>
                    </Select>
                  </div>

                  <InputText
                    type="tel"
                    class="input-modern input-phone"
                    v-model="user.user.phone_number"
                    @blur="formatPhoneOnBlur"
                    :placeholder="'300 000 0000'"
                  />
                </div>

                <span v-if="phoneError" class="field-error">{{ phoneError }}</span>
              </div>

              <div class="form-group">
                <label>{{ t('email') }}</label>
                <InputText type="email" class="input-modern" v-model="user.user.email" :placeholder="t('email')" />
              </div>
            </div>
          </section>

          <!-- ================== DIRECCIÓN / PICKUP ================== -->
          <section class="card form-section">
            <h2 class="section-title">
              {{ [2, 6].includes(user.user.order_type?.id) ? (user.user.order_type?.id === 6 ? 'En el Local' : t('site_recoger')) : t('address') }}
            </h2>

            <!-- DELIVERY -->
            <div v-if="!user.user.order_type || ![2, 6].includes(user.user.order_type.id)" class="address-selector">
              <div
                class="address-card"
                :class="{ 'has-address': user.user.address, 'no-address': !user.user.address }"
                @click="openAddressModal"
              >
                <div class="icon-box-addr">
                  <Icon name="mdi:map-marker" />
                </div>

                <div class="addr-info">
                  <span v-if="user.user.address" class="addr-title">{{ user.user.address }}</span>
                  <span v-else class="addr-placeholder">{{ t('address_placeholder') }}</span>

                  <div v-if="user.user.address" class="addr-meta">
                    <span class="badge badge-delivery">
                      {{
                        siteStore?.location?.neigborhood?.delivery_price != null
                          ? formatCOP(siteStore.location.neigborhood.delivery_price)
                          : (lang === 'en' ? 'Free Shipping' : 'Envío Gratis')
                      }}
                    </span>
                    <span v-if="siteStore?.location?.site?.site_name" class="site-name">
                      • {{ lang === 'en' ? 'From' : 'Desde' }} {{ siteStore.location.site.site_name }}
                    </span>
                  </div>
                </div>

                <div class="action-arrow">
                  <Icon :name="user.user.address ? 'mdi:pencil' : 'mdi:plus'" />
                </div>
              </div>
            </div>

            <!-- PICKUP -->
            <div v-else class="address-selector">
              <div class="address-card has-address" @click="siteStore.setVisible('currentSiteSites', true)">
                <div class="icon-box-addr pickup"><Icon name="mdi:store-marker" /></div>
                <div class="addr-info">
                  <span class="addr-title">{{ siteStore?.location?.site?.site_name || t('site_selector') }}</span>
                  <span class="addr-text">{{ siteStore?.location?.site?.site_address }}</span>
                </div>
                <div class="action-arrow"><Icon name="mdi:chevron-right" /></div>
              </div>

              <div
                v-if="[33, 35, 36].includes(siteStore.location?.site?.site_id) && user.user.order_type?.id === 2"
                class="form-group mt-3"
              >
                <label>{{ t('vehicle_plate') }}</label>
                <InputText class="input-modern" v-model="user.user.placa" placeholder="ABC-123" />
              </div>
            </div>
          </section>

          <!-- ================== PAGO & DETALLES ================== -->
          <section class="card form-section">
            <h2 class="section-title">Pago & Detalles</h2>

            <!-- CUPONES -->
            <div class="coupon-wrapper">
              <div class="coupon-toggle" @click="have_discount = !have_discount">
                <div class="coupon-left">
                  <Icon name="mdi:ticket-percent-outline" size="20" />
                  <span>{{ t('code') }}</span>
                </div>
                <div class="switch" :class="{ 'on': have_discount }">
                  <div class="knob"></div>
                </div>
              </div>

              <div v-if="have_discount" class="coupon-content">
                <div class="coupon-input-row">
                  <InputText
                    v-model="temp_discount"
                    :placeholder="t('code_placeholder')"
                    :disabled="temp_code?.status === 'active'"
                    class="coupon-input"
                  />

                  <Button
                    v-if="temp_code?.status === 'active'"
                    class="btn-coupon remove"
                    @click="clearCoupon"
                    severity="danger"
                    outlined
                  >
                    <Icon name="mdi:trash-can-outline" />
                  </Button>

                  <Button
                    v-else
                    class="btn-coupon apply"
                    @click="validateDiscount(temp_discount, { silent: false })"
                    :disabled="!temp_discount"
                  >
                    {{ lang === 'en' ? 'Apply' : 'Aplicar' }}
                  </Button>
                </div>

                <div
                  v-if="temp_code?.status"
                  class="coupon-feedback"
                  :class="temp_code.status === 'active' ? 'positive' : 'negative'"
                >
                  <Icon :name="temp_code.status === 'active' ? 'mdi:check-circle' : 'mdi:alert-circle'" size="18" />

                  <div v-if="temp_code.status === 'active'" class="feedback-info">
                    <span class="discount-title">{{ temp_code.discount_name }}</span>
                    <span class="discount-amount" v-if="temp_code.amount">
                      Ahorras: <strong>{{ formatCOP(temp_code.amount) }}</strong>
                    </span>
                    <span class="discount-amount" v-else-if="temp_code.percent">
                      Ahorras: <strong>{{ temp_code.percent }}%</strong>
                    </span>
                  </div>

                  <div v-else class="feedback-info">
                    <span>
                      {{ temp_code.status === 'invalid_site' ? 'No válido en esta sede' : (lang === 'en' ? 'Invalid code' : 'Código no válido') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- ✅ PrimeVue Select método de pago -->
            <div class="form-group" v-if="computedPaymentOptions.length > 0">
              <label>{{ t('payment_method') }}</label>

              <div class="select-wrapper">
                <Icon name="mdi:credit-card-outline" class="select-icon" />

                <Select
                  v-model="user.user.payment_method_option"
                  :options="computedPaymentOptions"
                  optionLabel="name"
                  :placeholder="lang === 'en' ? 'Select an option' : 'Selecciona una opción'"
                  class="pv-select pv-select-payment input-modern with-icon"
                />
              </div>
            </div>

            <div class="form-group">
              <label>{{ t('notes') }}</label>
              <Textarea
                class="input-modern"
                rows="3"
                v-model="store.order_notes"
                :placeholder="t('additional_notes')"
              />
            </div>
          </section>
        </div>

        <div class="summary-column">
          <resumen />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import resumen from '../resumen.vue'
import { usecartStore, useSitesStore, useUserStore } from '#imports'
import { URI } from '~/service/conection'
import { buildCountryOptions } from '~/service/utils/countries'
import { parsePhoneNumberFromString } from 'libphonenumber-js/min'

// PrimeVue 4
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import ProgressSpinner from 'primevue/progressspinner'

/* ================= STORES ================= */
const user = useUserStore()
const siteStore = useSitesStore()
const store = usecartStore()

/* ================= Helpers ================= */
const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const apiFetch = async (url) => (await fetch(url)).json()

/* ================= Config ================= */
const uri_api_google = 'https://api.locations.salchimonster.com'
const sitePaymentsComplete = ref([])
const MAIN_DOMAIN = 'salchimonster.com'

/* ================= Redirect overlay ================= */
const isRedirecting = ref(false)
const targetSiteName = ref('')

/* ================= i18n ================= */
const lang = computed(() =>
  (user?.lang?.name || 'es').toString().toLowerCase() === 'en' ? 'en' : 'es'
)

const DICT = {
  es: {
    finalize_purchase: 'Finalizar Compra',
    name: 'Nombre Completo',
    phone: 'Celular',
    site_recoger: 'Sede para Recoger',
    payment_method: 'Método de Pago',
    notes: 'Notas del pedido',
    code: '¿Tienes un cupón?',
    site_selector: 'Seleccionar ubicación',
    address_placeholder: 'Buscar dirección (Ej: Calle 123...)',
    in_coverage: '¡Estás en zona de cobertura!',
    not_in_coverage: 'Fuera de cobertura',
    distance: 'Distancia',
    km: 'km',
    ships_from_site: 'Te enviamos desde ',
    delivery_price: 'Costo Domicilio',
    cancel: 'Cancelar',
    save: 'Confirmar ubicación',
    email: 'Correo Electrónico',
    vehicle_plate: 'Placa del vehículo',
    additional_notes: 'Ej: Timbre dañado, dejar en portería...',
    search_country_or_code: 'Buscar país...',
    address: 'Dirección de Entrega',
    code_placeholder: 'Ingresa el código'
  },
  en: {
    finalize_purchase: 'Checkout',
    name: 'Full Name',
    phone: 'Mobile Phone',
    site_recoger: 'Pickup Location',
    payment_method: 'Payment Method',
    notes: 'Order Notes',
    code: 'Have a coupon?',
    site_selector: 'Select Location',
    address_placeholder: 'Search address...',
    in_coverage: 'Great! In coverage area',
    not_in_coverage: 'Out of coverage',
    distance: 'Distance',
    km: 'km',
    ships_from_site: 'Shipping from',
    delivery_price: 'Delivery Fee',
    cancel: 'Cancel',
    save: 'Confirm Location',
    email: 'Email',
    vehicle_plate: 'Vehicle Plate',
    additional_notes: 'Ex: Doorbell broken...',
    search_country_or_code: 'Search country...',
    address: 'Delivery Address',
    code_placeholder: 'Enter code'
  }
}
const t = (key) => DICT[lang.value]?.[key] || DICT.es[key] || key

const formatCOP = (v) =>
  v === 0
    ? 'Gratis'
    : new Intl.NumberFormat(lang.value === 'en' ? 'en-CO' : 'es-CO', {
        style: 'currency',
        currency: 'COP',
        maximumFractionDigits: 0
      }).format(v)

/* ================= Modal Google (Prime Dialog) ================= */
const see_sites = ref(false)
const addressQuery = ref('')
const dir_options = ref([])
const isValidating = ref(false)
const showAddressSuggestions = ref(false)
const sessionToken = ref(null)
const tempSiteData = ref(null)
const addressInputRef = ref(null)

const openAddressModal = () => {
  addressQuery.value = ''
  tempSiteData.value = null
  dir_options.value = []
  see_sites.value = true
  if (!sessionToken.value) sessionToken.value = generateUUID()
}

const closeModal = () => {
  see_sites.value = false
  sessionToken.value = null
}

const onSearchInput = async () => {
  tempSiteData.value = null
  showAddressSuggestions.value = true

  if (!addressQuery.value.trim()) {
    dir_options.value = []
    return
  }

  const city = siteStore.location?.site?.city_name || ''
  const params = new URLSearchParams({
    input: addressQuery.value,
    session_token: sessionToken.value,
    language: lang.value,
    city,
    limit: '5'
  })

  try {
    const res = await (await fetch(`${uri_api_google}/co/places/autocomplete?${params}`)).json()
    dir_options.value = (res.predictions || res).filter((p) => p?.place_id)
  } catch (e) {
    dir_options.value = []
  }
}

const clearSearch = () => {
  addressQuery.value = ''
  onSearchInput()
}

const onAddressSelect = async (item) => {
  if (!item?.place_id) return

  isValidating.value = true
  showAddressSuggestions.value = false
  addressQuery.value = item.description

  try {
    const params = new URLSearchParams({
      place_id: item.place_id,
      session_token: sessionToken.value,
      language: lang.value
    })
    const details = await (await fetch(`${uri_api_google}/co/places/coverage-details?${params}`)).json()

    tempSiteData.value = {
      ...details,
      formatted_address: details.formatted_address || item.description,
      status: 'checked',
      in_coverage: !details.error && details.nearest?.in_coverage
    }
  } catch (e) {
    tempSiteData.value = {
      status: 'checked',
      in_coverage: false,
      error: { message_es: 'Error de conexión', message_en: 'Connection error' },
      formatted_address: item.description
    }
  } finally {
    isValidating.value = false
  }
}

/* ================= Confirm / Redirect ================= */
const confirmSelection = async () => {
  if (!tempSiteData.value?.in_coverage) return

  const currentSiteId = siteStore.location?.site?.site_id
  const newSiteId = tempSiteData.value.nearest?.site?.site_id

  if (currentSiteId && newSiteId && String(currentSiteId) !== String(newSiteId)) {
    await handleSiteChange(tempSiteData.value)
    return
  }

  applySiteSelection(tempSiteData.value)
  closeModal()
}

const applySiteSelection = (data) => {
  // data = coverage-details
  user.user.site = data
  user.user.address = data.formatted_address
  user.user.lat = data.lat
  user.user.lng = data.lng
  user.user.place_id = data.place_id

  // sitio real al que queda asociado
  siteStore.location.site = data.nearest?.site || siteStore.location.site
  store.address_details = data

  if (data.delivery_cost_cop != null) {
    siteStore.location.neigborhood.delivery_price = data.delivery_cost_cop
  }

  ensureValidOrderTypeForCurrentSite()
}

const handleSiteChange = async (newData) => {
  isRedirecting.value = true
  const site = newData.nearest?.site
  targetSiteName.value = site?.site_name || 'Nueva Sede'

  try {
    const hash = generateUUID()

    const payload = {
      user: {
        ...user.user,
        site: newData,
        address: newData.formatted_address,
        lat: newData.lat,
        lng: newData.lng,
        place_id: newData.place_id
      },
      cart: store.cart,
      site_location: site,
      discount: store.applied_coupon || null,
      coupon_ui: store.coupon_ui || null,
      coupon_code: store.applied_coupon?.code || store.coupon_ui?.draft_code || null
    }

    await fetch(`${URI}/data/${hash}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const subdomain = site?.subdomain
    if (!subdomain) {
      alert('Lo sentimos, no pudimos localizar la dirección web de esta sede.')
      isRedirecting.value = false
      return
    }

    const isDev = window.location.hostname.includes('localhost')
    const protocol = window.location.protocol
    const targetUrl = isDev
      ? `${protocol}//${subdomain}.localhost:3000/pay?hash=${hash}`
      : `https://${subdomain}.${MAIN_DOMAIN}/pay?hash=${hash}`

    window.location.href = targetUrl
  } catch (error) {
    console.error('Error switching site:', error)
    alert('Ocurrió un error al cambiar de sede. Intenta nuevamente.')
    isRedirecting.value = false
  }
}

/* ================= Teléfono (Prime Select) ================= */
const phoneError = ref('')
const countries = ref([])

const initCountries = () => {
  countries.value = buildCountryOptions(lang.value).map((c) => ({
    ...c,
    dialDigits: (c.dialCode || '').replace(/\D+/g, ''),
    flag: `https://flagcdn.com/h20/${c.code.toLowerCase()}.png`
  }))
}

const formatPhoneOnBlur = () => {
  const countryIso = user.user.phone_code?.code
  const phone = parsePhoneNumberFromString(user.user.phone_number || '', countryIso)
  if (phone && phone.isValid()) user.user.phone_number = phone.formatNational()
}

watch(
  [() => user.user.phone_number, () => user.user.phone_code],
  ([num, country]) => {
    phoneError.value = ''
    if (!num) return
    const phone = parsePhoneNumberFromString((num || '').toString(), country?.code)
    if (phone && phone.isValid()) {
      user.user.phone_e164 = phone.number
    } else {
      user.user.phone_e164 = null
      phoneError.value = lang.value === 'en' ? 'Invalid phone number' : 'Número inválido'
    }
  },
  { immediate: true }
)

/* ================= Tipos de orden / pagos ================= */
const computedOrderTypesVisible = computed(() => {
  const siteId = siteStore.location?.site?.site_id
  if (!siteId || !sitePaymentsComplete.value.length) return []
  const siteConfig = sitePaymentsComplete.value.find((s) => String(s.site_id) === String(siteId))
  if (!siteConfig || !siteConfig.order_types) return []
  return siteConfig.order_types.filter((ot) => ot.methods && ot.methods.length > 0)
})

const orderTypeIdStr = computed({
  get: () => (user.user.order_type?.id ? String(user.user.order_type.id) : null),
  set: (idStr) => {
    const id = Number(idStr)
    const opt = computedOrderTypesVisible.value.find((o) => o.id === id)
    user.user.order_type = opt
  }
})

const computedPaymentOptions = computed(() => {
  const typeId = user.user.order_type?.id
  if (!typeId) return []
  const selectedOrderType = computedOrderTypesVisible.value.find((ot) => Number(ot.id) === Number(typeId))
  return selectedOrderType?.methods || []
})

const ensureValidOrderTypeForCurrentSite = () => {
  const list = computedOrderTypesVisible.value
  if (list.length === 0) {
    user.user.order_type = null
    return
  }
  const currentId = user.user.order_type?.id
  if (!currentId || !list.some((o) => Number(o.id) === Number(currentId))) {
    user.user.order_type = list[0]
  }
}

watch(
  () => user.user.order_type,
  (newType) => {
    if (newType?.id === 2 || newType?.id === 6) {
      siteStore.location.neigborhood.delivery_price = 0
    } else {
      const cost = user.user.site?.delivery_cost_cop ?? siteStore?.delivery_price
      if (cost != null) siteStore.location.neigborhood.delivery_price = cost
    }

    const currentMethodId = user.user.payment_method_option?.id
    const availableMethods = computedPaymentOptions.value
    if (!availableMethods.some((m) => m.id === currentMethodId)) {
      user.user.payment_method_option = null
    }
  }
)

/* ================= Cupones (persist + auto-apply) ================= */
const have_discount = computed({
  get: () => !!store.coupon_ui?.enabled || !!store.applied_coupon,
  set: (v) => store.setCouponUi({ enabled: !!v })
})

const temp_discount = computed({
  get: () => store.applied_coupon?.code || store.coupon_ui?.draft_code || '',
  set: (v) => store.setCouponUi({ draft_code: (v || '').toString() })
})

const temp_code = ref({})
const lastAutoApplyKey = ref('')

const validateDiscount = async (code, opts = { silent: false }) => {
  const silent = !!opts?.silent

  const site = siteStore.location?.site
  if (!site) {
    if (!silent) alert('Selecciona una sede primero')
    return
  }

  const finalCode = (code || '').toString().trim()
  if (!finalCode) return

  try {
    const res = await (await fetch(`${URI}/discount/get-discount-by-code/${encodeURIComponent(finalCode)}`)).json()

    if (res) {
      if (Array.isArray(res.sites) && !res.sites.some((s) => String(s.site_id) === String(site.site_id))) {
        temp_code.value = { status: 'invalid_site' }
        if (store.applied_coupon?.code) store.removeCoupon()
        if (!silent) alert(lang.value === 'en' ? 'Coupon not valid for this site' : 'Este cupón no es válido para esta sede.')
        return
      }

      store.applyCoupon(res)
      temp_code.value = {
        ...res,
        status: 'active',
        discount_name: res.discount_name || res.name || 'Descuento'
      }
    } else {
      temp_code.value = { status: 'invalid' }
      if (store.applied_coupon?.code) store.removeCoupon()
    }
  } catch (e) {
    console.error(e)
    temp_code.value = { status: 'error' }
    if (!silent) alert(lang.value === 'en' ? 'Error validating coupon.' : 'Error validando el cupón.')
  }
}

const autoApplyCouponIfNeeded = async () => {
  const siteId = siteStore.location?.site?.site_id
  if (!siteId) return

  const appliedCode = store.applied_coupon?.code ? String(store.applied_coupon.code) : ''
  const draftCode = store.coupon_ui?.draft_code ? String(store.coupon_ui.draft_code) : ''
  const enabled = !!store.coupon_ui?.enabled

  const candidate = appliedCode || (enabled ? draftCode : '')
  if (!candidate) return

  const key = `${siteId}|${candidate}`
  if (lastAutoApplyKey.value === key) return
  lastAutoApplyKey.value = key

  have_discount.value = true
  temp_discount.value = candidate

  await validateDiscount(candidate, { silent: true })
}

watch(
  () => store.applied_coupon,
  (newCoupon) => {
    if (newCoupon && newCoupon.code) {
      have_discount.value = true
      temp_discount.value = newCoupon.code
      temp_code.value = {
        ...newCoupon,
        status: 'active',
        discount_name: newCoupon.discount_name || newCoupon.name || 'Descuento'
      }
    } else {
      temp_code.value = {}
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => siteStore.location?.site?.site_id,
  async () => {
    await autoApplyCouponIfNeeded()
  },
  { immediate: true }
)

watch(
  () => store.coupon_ui?.draft_code,
  async () => {
    await autoApplyCouponIfNeeded()
  }
)

const clearCoupon = () => {
  temp_code.value = {}
  store.removeCoupon()
  have_discount.value = true
  temp_discount.value = ''
}

/* ================= Mount ================= */
onMounted(async () => {
  initCountries()
  if (!user.user.phone_code) {
    const defaultCode = lang.value === 'en' ? 'US' : 'CO'
    user.user.phone_code = countries.value.find((c) => c.code === defaultCode)
  }

  try {
    const spData = await apiFetch(`${URI}/site-payments-complete`)
    sitePaymentsComplete.value = spData || []
    ensureValidOrderTypeForCurrentSite()
  } catch (e) {
    console.error('Error loading payment config', e)
  }

  await autoApplyCouponIfNeeded()
})

watch(lang, initCountries)
</script>

<style scoped>
/* =========================================
   VARIABLES & TEMA
   ========================================= */
.checkout-page {
  --primary: #000000;
  --bg-page: #f8f9fa;
  --bg-card: #ffffff;
  --text-main: #1f2937;
  --text-light: #6b7280;
  --border: #e5e7eb;
  --border-focus: #000000;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.03);
  --shadow-hover: 0 10px 25px rgba(0, 0, 0, 0.06);
  --success: #10b981;
  --error: #ef4444;

  font-family: 'Inter', -apple-system, sans-serif;
  color: var(--text-main);
  background-color: var(--bg-page);
  min-height: 100vh;
}

/* =========================================
   ANIMACIÓN DE REDIRECCIÓN (COHETE)
   ========================================= */
.redirect-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100dvh;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  z-index: 99999;
  display: flex; align-items: center; justify-content: center;
}
.redirect-content { text-align: center; animation: popIn 0.5s ease-out; }
.redirect-spinner { position: relative; display: inline-flex; margin-bottom: 2rem; color: #ff6600; }
.rocket-icon { z-index: 2; animation: rocketFloat 1.5s ease-in-out infinite alternate; color: #ff6600; }
.pulse-ring {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 80px; height: 80px; border-radius: 50%; border: 2px solid #ff6600;
  opacity: 0; animation: pulse 2s infinite;
}
.redirect-title { font-size: 1.2rem; color: #64748b; margin: 0; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; }
.redirect-store { font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0.5rem 0; line-height: 1.1; max-width: 90vw; }
.redirect-subtitle { font-size: 1rem; color: #94a3b8; margin-top: 1rem; }

@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes rocketFloat { from { transform: translateY(0); } to { transform: translateY(-10px); } }
@keyframes pulse { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* LAYOUT */
.checkout-layout { max-width: 1100px; margin: 0 auto; padding: 2rem .5rem; }
.page-header { text-align: center; margin-bottom: 2.5rem; }
.page-header h1 { font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; margin: 0; }
.checkout-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; }
@media (min-width: 992px) { .checkout-grid { grid-template-columns: 1.4fr 1fr; align-items: start; } }

/* CARDS */
.card {
  background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border);
  padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow-card);
  transition: transform 0.2s, box-shadow 0.2s;
}
.section-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 1.25rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border); color: #111; }

/* TABS */
.card-tabs { padding: 0; background: #f1f5f9; border: none; }
.tabs-container { display: flex; background: #ffffff; border-radius: var(--radius-sm); }
.tab-item {
  flex: 1; text-align: center; padding: 0.75rem; border-radius: 6px; cursor: pointer;
  font-weight: 600; font-size: 0.95rem; color: rgb(0, 0, 0); transition: all 0.2s ease; position: relative; margin: 0;
}
.tab-item.is-active { background: #000000; color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.hidden-radio { position: absolute; opacity: 0; width: 0; height: 0; }

/* FORM */
.form-row { margin-bottom: 1rem; }
.form-row.split { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media(min-width: 600px) { .form-row.split { grid-template-columns: 1fr 1fr; } }
label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: #374151; }

.input-modern { width: 100%; }

/* PrimeVue inputs full width */
:deep(.p-inputtext),
:deep(.p-textarea),
:deep(.p-select) {
  width: 100%;
}

/* TELÉFONO */
.phone-control { display: flex; gap: 0.5rem; }
.country-select { min-width: 120px; }
.flag-mini { width: 18px; border-radius: 2px; }
.field-error { font-size: 0.8rem; color: var(--error); margin-top: 4px; display: block; }

/* ADDRESS CARD */
.address-card {
  display: flex; align-items: center; gap: 1rem; padding: 1rem; border: 1px solid var(--border);
  border-radius: var(--radius-sm); cursor: pointer; transition: all 0.2s; background: #fff;
}
.address-card:hover { border-color: #000; box-shadow: var(--shadow-card); }
.address-card.no-address { border-style: dashed; background: #f9fafb; }
.icon-box-addr {
  width: 40px; height: 40px; background: #f3f4f6; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #666;
}
.has-address .icon-box-addr, .pickup .icon-box-addr { background: #000; color: #fff; }
.addr-info { flex: 1; display: flex; flex-direction: column; }
.addr-title { font-weight: 600; font-size: 0.95rem; }
.addr-placeholder { color: var(--text-light); }
.addr-text { font-size: 0.85rem; color: var(--text-light); }
.addr-meta { font-size: 0.8rem; margin-top: 4px; display: flex; align-items: center; gap: 5px; }
.badge-delivery { background: #ecfdf5; color: #047857; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
.action-arrow { color: #9ca3af; }
.mt-3 { margin-top: 1rem; }

/* CUPONES */
.coupon-wrapper { border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; margin-bottom: 1.5rem; }
.coupon-toggle { display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 1rem; background: #f9fafb; cursor: pointer; }
.coupon-left { display: flex; gap: 0.5rem; align-items: center; font-weight: 600; font-size: 0.9rem; }
.switch { width: 36px; height: 20px; background: #d1d5db; border-radius: 20px; position: relative; transition: 0.3s; }
.switch.on { background: #000; }
.knob { width: 16px; height: 16px; background: #fff; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: 0.3s; }
.switch.on .knob { transform: translateX(16px); }
.coupon-content { padding: 1rem; border-top: 1px solid var(--border); }
.coupon-input-row { display: flex; gap: 0.5rem; align-items: center; }
.coupon-input { flex: 1; }
.btn-coupon { font-weight: 700; border-radius: 8px; }
.coupon-feedback { margin-top: 0.8rem; font-size: 0.85rem; display: flex; gap: 0.6rem; align-items: flex-start; font-weight: 500; padding: 0.6rem; border-radius: 6px; }
.coupon-feedback.positive { color: var(--success); background: #ecfdf5; }
.coupon-feedback.negative { color: var(--error); background: #fef2f2; }
.feedback-info { display: flex; flex-direction: column; }
.discount-title { font-weight: 700; color: #065f46; font-size: 0.9rem; text-transform: uppercase; }
.discount-amount { font-size: 0.85rem; color: #047857; margin-top: 2px; }

/* Payment select icon overlay */
.select-wrapper { position: relative; }
.with-icon { padding-left: 2.6rem; }
.select-icon { position: absolute; left: 0.8rem; top: 50%; transform: translateY(-50%); color: #6b7280; pointer-events: none; z-index: 2; }

/* ================== Dialog styles ================== */
.modal-header { display:flex; align-items:center; justify-content:space-between; width:100%; gap: 1rem; }
.modal-title { margin: 0; font-size: 1.1rem; font-weight: 800; }
.btn-icon-close { color: #666; }

.modal-body { padding-top: .5rem; }

.search-box {
  display: flex; align-items: center; gap: 0.5rem;
  background: #f3f4f6; border-radius: 10px; padding: 0 0.75rem;
  margin-bottom: 1rem; border: 1px solid transparent; transition: 0.2s;
}
.search-box.is-focused { background: #fff; border-color: #000; box-shadow: 0 0 0 3px rgba(0,0,0,0.05); }
.search-icon { color: #666; }
.search-input { flex: 1; border: none !important; box-shadow: none !important; background: transparent !important; padding: 0.9rem 0.2rem !important; }
.btn-clear { color: #777; }

.suggestions-list { list-style: none; padding: 0; margin: 0; border: 1px solid #eee; border-radius: 8px; overflow: hidden; }
.suggestions-list li { padding: 0.8rem 1rem; border-bottom: 1px solid #f9f9f9; display: flex; gap: 0.8rem; cursor: pointer; align-items: flex-start; }
.suggestions-list li:hover { background: #f9fafb; }
.suggestion-icon { margin-top: 2px; color: #666; }
.suggestion-content { display: flex; flex-direction: column; }
.suggestion-content .main { font-weight: 700; font-size: 0.9rem; }
.suggestion-content .sub { font-size: 0.8rem; color: #888; }

.loading-state { text-align: center; padding: 1.25rem 0.25rem; color: #666; display: flex; flex-direction: column; align-items: center; gap: 0.6rem; }

.result-card { border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.result-card.is-success { border-color: #d1fae5; }
.result-card.is-error { border-color: #fee2e2; }
.result-header { padding: 1rem; display: flex; gap: 1rem; align-items: center; background: #f9fafb; }
.is-success .result-header { background: #ecfdf5; }
.is-error .result-header { background: #fef2f2; }
.status-icon { width: 32px; height: 32px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; }
.is-success .status-icon { color: #10b981; }
.is-error .status-icon { color: #ef4444; }
.status-text h4 { margin: 0; font-size: 1rem; }
.status-text p { margin: 0; font-size: 0.85rem; opacity: 0.85; }
.result-details { padding: 1rem; background: #fff; }
.detail-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.95rem; }
.detail-row.full { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed #eee; display: block; }
.error-message { padding: 1rem; color: #b91c1c; font-size: 0.9rem; background: #fff; }

.modal-footer { display:flex; justify-content:flex-end; gap: .75rem; width: 100%; }
.btn-primary { background: #000 !important; border-color: #000 !important; }
.btn-secondary { border-color: #d1d5db !important; color: #374151 !important; }

/* PrimeVue dialog padding tweak */
:deep(.p-dialog-content) { padding-top: 0.5rem; }
:deep(.p-dialog-header) { padding: 1rem 1.25rem; }
:deep(.p-dialog-content) { padding: 1rem 1.25rem; }
:deep(.p-dialog-footer) { padding: 1rem 1.25rem; }
</style>
