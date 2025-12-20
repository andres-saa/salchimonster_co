<template>
  <div class="checkout-page">
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

    <div class="checkout-layout">
      <header class="page-header">
        <h1>{{ t('finalize_purchase') }}</h1>
      </header>

      <div class="checkout-grid">
        <div class="form-column">
          <div class="tabs-wrapper" v-if="computedOrderTypesVisible.length > 0">
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
                >
                <span class="tab-label">{{ opt.name }}</span>
              </label>
            </div>
          </div>
          <div v-else class="card loading-card">
            <Icon name="svg-spinners:3-dots-scale" size="1.5rem" />
            <p>{{ lang === 'en' ? 'Loading delivery options...' : 'Cargando opciones de entrega...' }}</p>
          </div>

          <section class="card form-section">
            <h2 class="section-title">
              <Icon name="mdi:account-outline" class="section-icon" />
              Datos Personales
            </h2>

            <div class="form-grid">
              <div class="form-group full-width">
                <label>{{ t('name') }}</label>
                <input type="text" class="input-modern" v-model="user.user.name" :placeholder="t('name')" />
              </div>

              <div class="form-group full-width">
                <label>{{ t('phone') }}</label>
                <div class="phone-control" style="min-width: 100%;">
                  <USelectMenu
                    v-model="countryValue"
                    :items="countryItems"
                    :avatar="countryValue?.avatar"
                    :search-input="{ placeholder: t('search_country_or_code') }"
                    class="country-menu-wrapper"
                    :ui="{ 
                      base: 'h-full', 
                      trigger: 'h-[48px] bg-white border border-gray-200 rounded-lg shadow-sm focus:ring-2 focus:ring-black' 
                    }"
                    :popper="{ placement: 'bottom-start' }"
                  >
                    <template #option="{ item }">
                      <div class="country-option">
                        <img v-if="item?.avatar?.src" :src="item.avatar.src" :alt="item.avatar.alt" class="flag-mini-ui" />
                        <div class="country-option-text">
                          <span class="country-name">{{ item?.name }}</span>
                          <small class="country-code">({{ item?.dialCode }})</small>
                        </div>
                      </div>
                    </template>
                  </USelectMenu>

                  <input
                    type="tel"
                    class="input-modern input-phone"
                    v-model="user.user.phone_number"
                    @blur="formatPhoneOnBlur"
                    placeholder="300 000 0000"
                  />
                </div>
                <span v-if="phoneError" class="field-error">{{ phoneError }}</span>
              </div>

                 <div class="form-group full-width">
                 <label>{{ t('email') }}</label>
                <input style="" type="email" class="input-modern" v-model="user.user.email" :placeholder="t('email')" />
              </div>

              <div class="form-group">
                
              </div>
            </div>
          </section>

          <section class="card form-section">
            <h2 class="section-title">
              <Icon :name="isPickup ? 'mdi:store-marker-outline' : 'mdi:map-marker-radius-outline'" class="section-icon" />
              {{ isPickup ? (user.user.order_type?.id === 6 ? 'En el Local' : t('site_recoger')) : t('address') }}
            </h2>

            <div class="form-group full-width" v-if="[2,6].includes(user.user.order_type?.id)">
              <label>{{ lang === 'en' ? 'Site' : 'Sede' }}</label>
              <USelectMenu
                v-model="siteValue"
                :items="siteItems"
                class="w-full"
                :search-input="{ placeholder: lang === 'en' ? 'Search site...' : 'Buscar sede...' }"
                :ui="{ trigger: 'h-[48px] bg-white' }"
              >
                <template #label="{ item }">
                  <div class="site-label">
                    <Icon name="mdi:storefront-outline" class="text-gray-500" />
                    <span class="site-label-text truncate">
                      {{ item?.label || (lang === 'en' ? 'Select site' : 'Selecciona sede') }}
                    </span>
                  </div>
                </template>
                <template #option="{ item }">
                  <div class="site-option">
                    <Icon name="mdi:storefront-outline" />
                    <div class="site-option-text">
                      <span class="site-name">{{ item?.label }}</span>
                      <small class="site-sub" v-if="item?.city_name">{{ item.city_name }}</small>
                    </div>
                  </div>
                </template>
              </USelectMenu>
            </div>

            <div v-else class="form-group full-width">
              <label>
                {{ isPickup ? (lang === 'en' ? 'Selected Site' : 'Sede seleccionada') : (lang === 'en' ? 'Location (Neighborhood)' : 'Ubicación (Barrio/Sector)') }}
              </label>

              <div class="address-card has-address" @click="siteStore.setVisible('currentSite', true)">
                <div class="icon-box-addr" :class="{ 'pickup': isPickup }">
                  <Icon :name="isPickup ? 'mdi:store-marker' : 'mdi:map-marker'" />
                </div>
                <div class="addr-info">
                  <span class="addr-title">
                    {{ siteStore.location.neigborhood?.name || siteStore.location.site?.site_name || t('site_selector') }}
                  </span>
                  <span class="addr-text" v-if="siteStore.location.city">
                    {{ siteStore.location.city.city_name }}
                  </span>
                  <div v-if="!isPickup && siteStore.location.neigborhood?.delivery_price" class="addr-meta">
                    <span class="badge badge-delivery">
                      {{ t('delivery_price') }}: {{ formatCOP(siteStore.location.neigborhood.delivery_price) }}
                    </span>
                  </div>
                </div>
                <div class="action-arrow">
                  <Icon name="mdi:pencil" />
                </div>
              </div>
            </div>

            <div class="form-group full-width mt-4" v-if="!isPickup">
              <label>{{ lang === 'en' ? 'Exact Address' : 'Dirección exacta' }}</label>
              <input
                type="text"
                class="input-modern"
                v-model="user.user.address"
                :placeholder="t('address_placeholder')"
              />
            </div>

            <div v-if="isPickup && [33, 35, 36].includes(siteStore.location?.site?.site_id)" class="form-group full-width mt-4">
              <label>{{ t('vehicle_plate') }}</label>
              <input type="text" class="input-modern" v-model="user.user.placa" placeholder="ABC-123" />
            </div>
          </section>

          <section class="card form-section">
            <h2 class="section-title">
              <Icon name="mdi:credit-card-check-outline" class="section-icon" />
              Pago & Detalles
            </h2>

            <div class="coupon-wrapper">
              <div class="coupon-toggle" @click="have_discount = !have_discount">
                <div class="coupon-left">
                  <div class="coupon-icon-box">
                    <Icon name="mdi:ticket-percent-outline" />
                  </div>
                  <span>{{ t('code') }}</span>
                </div>
                <div class="switch" :class="{ 'on': have_discount }">
                  <div class="knob"></div>
                </div>
              </div>

              <div v-if="have_discount" class="coupon-content">
                <div class="coupon-input-row">
                  <input
                    type="text"
                    class="input-modern input-coupon"
                    v-model="temp_discount"
                    :placeholder="t('code_placeholder')"
                    :disabled="temp_code?.status === 'active'"
                  >
                  <button v-if="temp_code?.status === 'active'" class="btn-coupon remove" @click="clearCoupon">
                    <Icon name="mdi:trash-can-outline" />
                  </button>
                  <button
                    v-else
                    class="btn-coupon apply"
                    @click="validateDiscount(temp_discount, { silent: false })"
                    :disabled="!temp_discount"
                  >
                    {{ lang === 'en' ? 'Apply' : 'Aplicar' }}
                  </button>
                </div>

                <div v-if="temp_code?.status" class="coupon-feedback" :class="temp_code.status === 'active' ? 'positive' : 'negative'">
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
                      {{ temp_code.status === 'invalid_site'
                        ? 'No válido en esta sede'
                        : (lang === 'en' ? 'Invalid code' : 'Código no válido') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-group full-width" v-if="computedPaymentOptions.length > 0">
              <label>{{ t('payment_method') }}</label>
              <USelectMenu
                v-model="paymentValue"
                :items="paymentItems"
                class="w-full"
                :search-input="{ placeholder: lang === 'en' ? 'Search payment method...' : 'Buscar método...' }"
                :ui="{ trigger: 'h-[48px] bg-white' }"
              >
                <template #label="{ item }">
                  <div class="pay-label">
                    <Icon name="mdi:credit-card-outline" class="text-gray-500" />
                    <span class="pay-label-text">
                      {{ item?.label || (lang === 'en' ? 'Select an option' : 'Selecciona una opción') }}
                    </span>
                  </div>
                </template>
                <template #option="{ item }">
                  <div class="pay-option">
                    <Icon name="mdi:credit-card-outline" />
                    <span>{{ item?.label }}</span>
                  </div>
                </template>
              </USelectMenu>
            </div>

            <div class="form-group full-width mt-4">
              <label>{{ t('notes') }}</label>
              <textarea
                class="input-modern"
                rows="3"
                v-model="store.order_notes"
                :placeholder="t('additional_notes')"
              ></textarea>
            </div>
          </section>
        </div>

        <div class="summary-column">
          <div class="sticky-summary">
            <resumen />
          </div>
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

/* ================= STORES & INIT ================= */
const user = useUserStore()
const siteStore = useSitesStore()
const store = usecartStore()

const sitePaymentsComplete = ref([])
const MAIN_DOMAIN = 'salchimonster.com'

// Para selector Nuxt UI de sedes
const allSites = ref([]) 

// ESTADO PARA LA REDIRECCIÓN
const isRedirecting = ref(false)
const targetSiteName = ref('')

/* ================= I18n & UTILS ================= */
const lang = computed(() => (user?.lang?.name || 'es').toString().toLowerCase() === 'en' ? 'en' : 'es')

const DICT = {
  es: {
    finalize_purchase: 'Finalizar Compra', name: 'Nombre Completo', phone: 'Celular', site_recoger: 'Sede para Recoger',
    payment_method: 'Método de Pago', notes: 'Notas del pedido', code: '¿Tienes un cupón?',
    site_selector: 'Seleccionar ubicación', address_placeholder: 'Buscar dirección (Ej: Calle 123...)',
    delivery_price: 'Costo Domicilio', cancel: 'Cancelar', save: 'Confirmar ubicación', email: 'Correo Electrónico',
    vehicle_plate: 'Placa del vehículo', additional_notes: 'Ej: Timbre dañado, dejar en portería...',
    search_country_or_code: 'Buscar país...', address: 'Dirección de Entrega', code_placeholder: 'Código'
  },
  en: {
    finalize_purchase: 'Checkout', name: 'Full Name', phone: 'Mobile Phone', site_recoger: 'Pickup Location',
    payment_method: 'Payment Method', notes: 'Order Notes', code: 'Have a coupon?',
    site_selector: 'Select Location', address_placeholder: 'Search address...',
    delivery_price: 'Delivery Fee', cancel: 'Cancel', save: 'Confirm Location', email: 'Email',
    vehicle_plate: 'Vehicle Plate', additional_notes: 'Ex: Doorbell broken...',
    search_country_or_code: 'Search country...', address: 'Delivery Address', code_placeholder: 'Code'
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

/* ================= LÓGICA DE TIPOS DE ORDEN ================= */
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

const isPickup = computed(() => {
  const id = user.user.order_type?.id
  return id === 2 || id === 6
})

const computedPaymentOptions = computed(() => {
  const typeId = user.user.order_type?.id
  if (!typeId) return []
  const selectedOrderType = computedOrderTypesVisible.value.find((ot) => Number(ot.id) === Number(typeId))
  return selectedOrderType?.methods || []
})

const ensureValidOrderTypeForCurrentSite = () => {
  const list = computedOrderTypesVisible.value
  if (list.length === 0) return
  const currentId = user.user.order_type?.id
  if (!currentId || !list.some((o) => Number(o.id) === Number(currentId))) {
    user.user.order_type = list[0]
  }
}

/* ================== MÉTODOS DE PAGO (Nuxt UI) ================== */
const paymentItems = computed(() => {
  return (computedPaymentOptions.value || []).map((m) => ({
    label: m.name,
    id: String(m.id),
    raw: m
  }))
})

const paymentValue = ref(null)

const syncPaymentValueFromUser = () => {
  const current = user.user.payment_method_option?.id
  if (!current) {
    paymentValue.value = null
    return
  }
  paymentValue.value = paymentItems.value.find((i) => i.id === String(current)) || null
}

watch(paymentItems, () => {
  syncPaymentValueFromUser()
})

watch(paymentValue, (v) => {
  if (!v?.raw) {
    user.user.payment_method_option = null
    return
  }
  user.user.payment_method_option = v.raw
})

/* ================== EFECTOS DE TIPO DE ORDEN ================== */
const syncOrderTypeEffects = () => {
  const newType = user.user.order_type

  if (newType?.id == 2 || newType?.id == 6) {
    siteStore.location.tem_cost = siteStore.location.neigborhood?.delivery_price
    if (siteStore.location.neigborhood) siteStore.location.neigborhood.delivery_price = 0
  } else {
    const cost =
      user.user.site?.delivery_cost_cop ??
      siteStore?.delivery_price ??
      siteStore.location.tem_cost

    if (cost != null && siteStore.location.neigborhood) siteStore.location.neigborhood.delivery_price = cost
  }

  // Si método seleccionado ya no existe, limpiarlo
  const currentMethodId = user.user.payment_method_option?.id
  const available = computedPaymentOptions.value || []
  if (!available.some((m) => String(m.id) === String(currentMethodId))) {
    user.user.payment_method_option = null
  }

  syncPaymentValueFromUser()
}

watch(() => user.user.order_type, () => {
  syncOrderTypeEffects()
})

/* ================== TELÉFONO (Nuxt UI) ================== */
const phoneError = ref('')
const countries = ref([])

const initCountries = () => {
  countries.value = buildCountryOptions(lang.value).map((c) => ({
    ...c,
    flag: `https://flagcdn.com/h20/${c.code.toLowerCase()}.png`
  }))

  const fallback = lang.value === 'en' ? 'US' : 'CO'
  const code = user.user.phone_code?.code || fallback
  const found = countries.value.find((c) => c.code === code) || countries.value[0] || null
  user.user.phone_code = found

  countryValue.value = found ? toCountryItem(found) : null
}

const toCountryItem = (c) => ({
  label: ` (${c.dialCode}) ${c.name} `,
  id: c.code,
  name: c.name,
  dialCode: c.dialCode || '+57',
  avatar: { src: c.flag, alt: c.name },
  raw: c
})

const countryItems = computed(() => countries.value.map(toCountryItem))
const countryValue = ref(null)

watch(countryValue, (v) => {
  if (v?.raw) user.user.phone_code = v.raw
})

const formatPhoneOnBlur = () => {
  const countryIso = user.user.phone_code?.code
  const phone = parsePhoneNumberFromString(user.user.phone_number || '', countryIso)
  if (phone && phone.isValid()) user.user.phone_number = phone.formatNational()
}

watch([() => user.user.phone_number, () => user.user.phone_code], ([num, country]) => {
  phoneError.value = ''
  if (!num) return
  const phone = parsePhoneNumberFromString((num || '').toString(), country?.code)
  if (phone && phone.isValid()) {
    user.user.phone_e164 = phone.number
  } else {
    user.user.phone_e164 = null
    phoneError.value = lang.value === 'en' ? 'Invalid phone number' : 'Número inválido'
  }
}, { immediate: true })

/* ================== CUPONES ================== */
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
    if (!silent) alert('Error validando el cupón.')
  }
}

const clearCoupon = () => {
  temp_code.value = {}
  store.removeCoupon()
  have_discount.value = true
  temp_discount.value = ''
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
  if (!temp_discount.value) temp_discount.value = candidate

  await validateDiscount(candidate, { silent: true })
}

watch(() => store.applied_coupon, (newCoupon) => {
  if (newCoupon && newCoupon.code) {
    have_discount.value = true
    if (temp_discount.value !== newCoupon.code) temp_discount.value = newCoupon.code
    temp_code.value = {
      ...newCoupon,
      status: 'active',
      discount_name: newCoupon.discount_name || newCoupon.name || 'Descuento'
    }
  } else {
    if (temp_code.value?.status === 'active') temp_code.value = {}
  }
}, { immediate: true, deep: true })

watch(() => store.coupon_ui?.draft_code, async () => {
  await autoApplyCouponIfNeeded()
})

/* ================== SELECTOR DE SEDES (Nuxt UI) ================== */
const siteItems = computed(() => {
  const arr = Array.isArray(allSites.value) ? allSites.value : []
  return arr.map((s) => ({
    label: s.site_name || s.name || `Sede ${s.site_id}`,
    id: String(s.site_id),
    city_name: s.city_name || s.city?.city_name || '',
    raw: s
  }))
})

const siteValue = ref(null)

const syncSiteValueFromStore = () => {
  const id = siteStore.location?.site?.site_id
  if (!id) { siteValue.value = null; return }
  siteValue.value = siteItems.value.find((i) => i.id === String(id)) || null
}

watch(siteItems, () => syncSiteValueFromStore())

watch(siteValue, (v) => {
  if (!v?.raw) return
  // IMPORTANT: esto dispara tu watch de siteStore.location.site.site_id y puede redirigir
  siteStore.location.site = v.raw
  user.user.site = v.raw
})

/* ================== REDIRECCIÓN ================== */
watch(() => siteStore.location?.site?.site_id, async (newSiteId, oldSiteId) => {
  ensureValidOrderTypeForCurrentSite()
  await autoApplyCouponIfNeeded()
  syncSiteValueFromStore()

  if (newSiteId && oldSiteId && String(newSiteId) !== String(oldSiteId)) {
    const newSiteData = siteStore.location.site
    await handleSiteChangeRedirect(newSiteData)
  }
})

const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const handleSiteChangeRedirect = async (targetSite) => {
  isRedirecting.value = true
  targetSiteName.value = targetSite.site_name || 'Nueva Sede'

  try {
    const hash = generateUUID()
    const currentNb = siteStore.location.neigborhood || {}
    const nbName = currentNb.name || currentNb.neighborhood_name || ''

    const cleanNeighborhood = {
      ...currentNb,
      name: nbName,
      id: currentNb.id || currentNb.neighborhood_id,
      neighborhood_id: currentNb.neighborhood_id || currentNb.id,
      delivery_price: currentNb.delivery_price
    }

    const payload = {
      user: {
        ...user.user,
        site: targetSite,
        address: user.user.address
      },
      cart: store.cart,
      site_location: targetSite,
      location_meta: {
        city: siteStore.location.city,
        neigborhood: cleanNeighborhood
      },
      discount: store.applied_coupon || null,
      coupon_ui: store.coupon_ui || null
    }

    await fetch(`${URI}/data/${hash}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const subdomain = targetSite.subdomain
    if (!subdomain) {
      alert('Esta sede no tiene dirección web configurada.')
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
    console.error('Redirection error:', error)
    isRedirecting.value = false
  }
}

onMounted(async () => {
  initCountries()
  try {
    const spData = await (await fetch(`${URI}/site-payments-complete`)).json()
    sitePaymentsComplete.value = spData || []
    ensureValidOrderTypeForCurrentSite()
    syncOrderTypeEffects()
  } catch (e) { console.error(e) }

  try {
    const sites = await (await fetch(`${URI}/sites`)).json()
    allSites.value = Array.isArray(sites) ? sites : (sites?.sites || [])
    syncSiteValueFromStore()
  } catch (e) { console.error('Error cargando sedes:', e) }

  await autoApplyCouponIfNeeded()
  syncPaymentValueFromUser()
})

watch(lang, () => { initCountries() })
</script>

<style scoped>
/* =========================================
   VARIABLES & TEMA
   ========================================= */
.checkout-page {
  --primary: #000000;
  --bg-page: #F9FAFB; /* Gris muy suave */
  --bg-card: #ffffff;
  --text-main: #111827;
  --text-light: #6B7280;
  --border-color: #E5E7EB;
  --border-focus: #000000;
  
  --radius-lg: 16px; /* Bordes más redondeados */
  --radius-md: 8px;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  
  --input-height: 48px; /* Altura estándar para móviles */
  
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text-main);
  background-color: var(--bg-page);
  min-height: 100vh;
  padding-bottom: 4rem;
}

/* =========================================
   LAYOUT
   ========================================= */
.checkout-layout {
  max-width: 1140px; /* Ligeramente más ancho */
  margin: 0 auto;
  padding: 1rem;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-header h1 {
  font-weight: 900;
  font-size: 2.25rem;
  letter-spacing: -0.04em;
  color: #111;
  margin: 0;
}

.checkout-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2.5rem;
}

@media (min-width: 1024px) {
  .checkout-grid {
    grid-template-columns: 1.5fr 1fr; /* Más espacio al formulario */
    gap: 3rem;
    align-items: start;
  }
  .sticky-summary {
    position: sticky;
    top: 2rem;
  }
}

/* =========================================
   CARDS & SECTIONS
   ========================================= */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 1rem; /* Más padding interno */
  margin-bottom: 2rem;
  box-shadow: var(--shadow-card);
}

.loading-card {
  text-align: center;
  color: var(--text-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-icon {
  color: var(--text-light);
  font-size: 1.3em;
}

/* =========================================
   TABS (Tipos de Orden)
   ========================================= */
.tabs-wrapper {
  margin-bottom: 2rem;
}

.tabs-container {
  display: flex;
  background: #E5E7EB; /* Fondo gris para el track */
  border-radius: 12px;
  padding: 4px;
  gap: 4px;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 10px 16px;
  border-radius: 9px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-light);
  transition: all 0.2s ease;
  position: relative;
  user-select: none;
  background-color: white;
}

.tab-item:hover {
  color: #000;
}

.tab-item.is-active {
  background: #000000;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.hidden-radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

/* =========================================
   FORM ELEMENTS
   ========================================= */
.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

@media(min-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.full-width {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 100%;
}

label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-left: 2px;
}

/* Estilo unificado para inputs y triggers de select */
.input-modern {
  width: 100%;
  height: var(--input-height);
  padding: 0 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
  color: var(--text-main);
}

.input-modern:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 2px rgba(0,0,0,0.05);
}

.input-modern::placeholder {
  color: #9CA3AF;
}

textarea.input-modern {
  height: auto;
  min-height: 100px;
  padding-top: 0.75rem;
  resize: vertical;
}

/* Phone Group Special Layout */
.phone-control {
  display: flex;
  width: 100%;
  gap: 0.75rem;
}
.country-menu-wrapper {
  min-width: 110px;
}
.input-phone {
  flex: 1;
}

.country-option, .site-option, .pay-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 4px 0;
}
.flag-mini-ui {
  width: 20px;
  height: 14px;
  border-radius: 2px;
  object-fit: cover;
  box-shadow: 0 0 1px rgba(0,0,0,0.3);
}

/* =========================================
   ADDRESS CARD
   ========================================= */
.address-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  position: relative;
  overflow: hidden;
}

.address-card:hover {
  border-color: #000;
  background: #fdfdfd;
}

.icon-box-addr {
  width: 44px;
  height: 44px;
  background: #F3F4F6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  color: #6B7280;
  flex-shrink: 0;
}

.has-address .icon-box-addr, .pickup .icon-box-addr {
  background: #000;
  color: #fff;
}

.addr-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.addr-title {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-main);
}

.addr-text {
  font-size: 0.9rem;
  color: var(--text-light);
  margin-top: 2px;
}

.badge-delivery {
  background: #ECFDF5;
  color: #059669;
  padding: 2px 8px;
  border-radius: 100px;
  font-weight: 600;
  font-size: 0.75rem;
  display: inline-block;
  margin-top: 4px;
}

.action-arrow {
  color: #D1D5DB;
  transition: color 0.2s;
}
.address-card:hover .action-arrow {
  color: #000;
}

/* =========================================
   CUPONES
   ========================================= */
.coupon-wrapper {
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 1.5rem;
  background: #FAFAFA;
}

.coupon-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: background 0.2s;
}

.coupon-toggle:hover {
  background: #F3F4F6;
}

.coupon-left {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  font-weight: 600;
  font-size: 0.95rem;
}

.coupon-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
}

.switch {
  width: 40px;
  height: 22px;
  background: #D1D5DB;
  border-radius: 20px;
  position: relative;
  transition: 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.switch.on {
  background: #000;
}

.knob {
  width: 18px;
  height: 18px;
  background: #fff;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.switch.on .knob {
  transform: translateX(18px);
}

.coupon-content {
  padding: 1.25rem;
  border-top: 1px dashed var(--border-color);
  background: #fff;
}

.coupon-input-row {
  display: flex;
  gap: 0.75rem;
}

.input-coupon {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.btn-coupon {
  padding: 0 1.25rem;
  height: var(--input-height);
  border-radius: var(--radius-md);
  border: none;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}
.btn-coupon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.apply {
  background: #000;
  color: #fff;
}

.remove {
  background: #FEE2E2;
  color: #EF4444;
  width: var(--input-height);
  padding: 0;
}

.coupon-feedback {
  margin-top: 1rem;
  font-size: 0.9rem;
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.75rem;
  border-radius: var(--radius-md);
}

.coupon-feedback.positive {
  color: #065F46;
  background: #ECFDF5;
  border: 1px solid #A7F3D0;
}

.coupon-feedback.negative {
  color: #991B1B;
  background: #FEF2F2;
  border: 1px solid #FECACA;
}

.feedback-info {
  display: flex;
  flex-direction: column;
}

.discount-title {
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.85rem;
}

.mt-4 { margin-top: 1.5rem; }

/* ERROR & REDIRECT Styles (Se mantienen igual de funcionales) */
.field-error { font-size: 0.8rem; color: #EF4444; margin-top: 6px; font-weight: 500; }
.redirect-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(8px); z-index: 99999; display: flex; align-items: center; justify-content: center; }
.redirect-content { text-align: center; animation: popIn 0.5s ease-out; }
.redirect-spinner { position: relative; display: inline-flex; margin-bottom: 2rem; color: #ff6600; }
.rocket-icon { z-index: 2; animation: rocketFloat 1.5s ease-in-out infinite alternate; color: #ff6600; }
.pulse-ring { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; border-radius: 50%; border: 2px solid #ff6600; opacity: 0; animation: pulse 2s infinite; }
.redirect-title { font-size: 1.2rem; color: #64748b; margin: 0; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; }
.redirect-store { font-size: 2.5rem; font-weight: 900; color: #0f172a; margin: 0.5rem 0; line-height: 1.1; max-width: 90vw; }
.redirect-subtitle { font-size: 1rem; color: #94a3b8; margin-top: 1rem; }
@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes rocketFloat { from { transform: translateY(0); } to { transform: translateY(-10px); } }
@keyframes pulse { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; } 100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>