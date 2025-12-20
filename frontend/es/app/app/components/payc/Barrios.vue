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
                >
                <span class="tab-label">
                  {{ opt.name }}
                </span>
              </label>
            </div>
          </div>
          <div v-else class="card" style="text-align:center; color: #666;">
            <p>{{ lang === 'en' ? 'Loading delivery options...' : 'Cargando opciones de entrega...' }}</p>
          </div>

          <section class="card form-section">
            <h2 class="section-title">Datos Personales</h2>

            <div class="form-row">
              <div class="form-group full">
                <label>{{ t('name') }}</label>
                <InputText 
                  class="input-modern" 
                  v-model="user.user.name" 
                  :placeholder="t('name')" 
                />
              </div>
            </div>

            <div class="form-row split">
              <div class="form-group">
                <label>{{ t('phone') }}</label>
                <div class="phone-control-prime">
                  <Select 
                    v-model="user.user.phone_code" 
                    :options="countries" 
                    optionLabel="name"
                    filter 
                    :filterPlaceholder="t('search_country_or_code')"
                    class="country-select-prime"
                  >
                    <template #value="slotProps">
                      <div class="country-item-selected" v-if="slotProps.value">
                        <img :src="slotProps.value.flag" :alt="slotProps.value.name" class="flag-mini" />
                        <span>{{ slotProps.value.dialCode }}</span>
                      </div>
                      <span v-else>+57</span>
                    </template>
                    <template #option="slotProps">
                      <div class="country-item-option">
                        <img :src="slotProps.option.flag" :alt="slotProps.option.name" class="flag-mini" />
                        <div>{{ slotProps.option.name }} <small>({{ slotProps.option.dialCode }})</small></div>
                      </div>
                    </template>
                  </Select>
                  
                  <InputText
                    class="input-modern input-phone-prime"
                    v-model="user.user.phone_number"
                    @blur="formatPhoneOnBlur"
                    placeholder="300 000 0000"
                  />
                </div>
                <span v-if="phoneError" class="field-error">{{ phoneError }}</span>
              </div>

              <div class="form-group">
                <label>{{ t('email') }}</label>
                <InputText 
                  type="email" 
                  class="input-modern" 
                  v-model="user.user.email" 
                  :placeholder="t('email')" 
                />
              </div>
            </div>
          </section>

          <section class="card form-section">
            <h2 class="section-title">
              {{ isPickup ? (user.user.order_type?.id === 6 ? 'En el Local' : t('site_recoger')) : t('address') }}
            </h2>

            <div class="form-group">
              <label>{{ isPickup ? (lang === 'en' ? 'Selected Site' : 'Sede seleccionada') : (lang === 'en' ? 'Location (Neighborhood)' : 'Ubicación (Barrio/Sector)') }}</label>
              
              <div 
                class="address-card has-address" 
                @click="siteStore.setVisible('currentSite', true)"
              >
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

            <div class="form-group mt-3" v-if="!isPickup">
              <label>{{ lang === 'en' ? 'Exact Address' : 'Dirección exacta' }}</label>
              <InputText 
                class="input-modern" 
                v-model="user.user.address" 
                :placeholder="t('address_placeholder')" 
              />
            </div>
            
            <div v-if="isPickup && [33, 35, 36].includes(siteStore.location?.site?.site_id)" class="form-group mt-3">
              <label>{{ t('vehicle_plate') }}</label>
              <InputText class="input-modern" v-model="user.user.placa" placeholder="ABC-123" />
            </div>
          </section>

          <section class="card form-section">
            <h2 class="section-title">Pago & Detalles</h2>

            <div class="coupon-wrapper">
              <div class="coupon-toggle" @click="have_discount = !have_discount">
                <div class="coupon-left">
                  <Icon name="mdi:ticket-percent-outline" size="20" />
                  <span>{{ t('code') }}</span>
                </div>
                <div @click.stop>
                   <ToggleSwitch v-model="have_discount" />
                </div>
              </div>

              <div v-if="have_discount" class="coupon-content">
                <div class="coupon-input-row">
                  <InputText
                    class="input-modern"
                    v-model="temp_discount"
                    :placeholder="t('code_placeholder')"
                    :disabled="temp_code?.status === 'active'"
                  />
                  
                  <Button 
                    v-if="temp_code?.status === 'active'" 
                    severity="danger" 
                    text
                    class="btn-prime-icon"
                    @click="clearCoupon"
                  >
                    <Icon name="mdi:trash-can-outline" size="20" />
                  </Button>

                  <Button
                    v-else
                    :label="lang === 'en' ? 'Apply' : 'Aplicar'"
                    class="btn-prime-black"
                    @click="validateDiscount(temp_discount, { silent: false })"
                    :disabled="!temp_discount"
                  />
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
                    <span>{{ temp_code.status === 'invalid_site' ? 'No válido en esta sede' : (lang === 'en' ? 'Invalid code' : 'Código no válido') }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-group" v-if="computedPaymentOptions.length > 0">
              <label>{{ t('payment_method') }}</label>
              <div class="prime-select-wrapper">
                <Select 
                    v-model="user.user.payment_method_option" 
                    :options="computedPaymentOptions" 
                    optionLabel="name" 
                    class="input-modern w-full"
                    :placeholder="lang === 'en' ? 'Select an option' : 'Selecciona una opción'"
                >
                    <template #value="slotProps">
                        <div v-if="slotProps.value" class="flex align-items-center">
                            <Icon name="mdi:credit-card-outline" class="mr-2" style="vertical-align: middle; margin-right: 8px;" />
                            {{ slotProps.value.name }}
                        </div>
                        <span v-else>
                            {{ slotProps.placeholder }}
                        </span>
                    </template>
                    <template #option="slotProps">
                        <div class="flex align-items-center">
                             {{ slotProps.option.name }}
                        </div>
                    </template>
                </Select>
              </div>
            </div>

            <div class="form-group">
              <label>{{ t('notes') }}</label>
              <Textarea
                class="input-modern"
                rows="3"
                autoResize
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

/* ================= STORES & INIT ================= */
const user = useUserStore()
const siteStore = useSitesStore()
const store = usecartStore()

const sitePaymentsComplete = ref([])
const MAIN_DOMAIN = 'salchimonster.com'

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
    search_country_or_code: 'Buscar país...', address: 'Dirección de Entrega', code_placeholder: 'Ingresa el código'
  },
  en: {
    finalize_purchase: 'Checkout', name: 'Full Name', phone: 'Mobile Phone', site_recoger: 'Pickup Location',
    payment_method: 'Payment Method', notes: 'Order Notes', code: 'Have a coupon?',
    site_selector: 'Select Location', address_placeholder: 'Search address...', 
    delivery_price: 'Delivery Fee', cancel: 'Cancel', save: 'Confirm Location', email: 'Email',
    vehicle_plate: 'Vehicle Plate', additional_notes: 'Ex: Doorbell broken...',
    search_country_or_code: 'Search country...', address: 'Delivery Address', code_placeholder: 'Enter code'
  }
}
const t = (key) => DICT[lang.value]?.[key] || DICT.es[key] || key
const formatCOP = (v) => v === 0 ? 'Gratis' : new Intl.NumberFormat(lang.value === 'en' ? 'en-CO' : 'es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)

/* ================= LÓGICA DE TIPOS DE ORDEN ================= */
const computedOrderTypesVisible = computed(() => {
  const siteId = siteStore.location?.site?.site_id
  if (!siteId || !sitePaymentsComplete.value.length) return []
  const siteConfig = sitePaymentsComplete.value.find(s => String(s.site_id) === String(siteId))
  if (!siteConfig || !siteConfig.order_types) return []
  return siteConfig.order_types.filter(ot => ot.methods && ot.methods.length > 0)
})

const orderTypeIdStr = computed({
  get: () => user.user.order_type?.id ? String(user.user.order_type.id) : null,
  set: (idStr) => {
    const id = Number(idStr)
    const opt = computedOrderTypesVisible.value.find(o => o.id === id)
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
  const selectedOrderType = computedOrderTypesVisible.value.find(ot => Number(ot.id) === Number(typeId))
  return selectedOrderType?.methods || []
})

const ensureValidOrderTypeForCurrentSite = () => {
  const list = computedOrderTypesVisible.value
  if (list.length === 0) return
  const currentId = user.user.order_type?.id
  if (!currentId || !list.some(o => Number(o.id) === Number(currentId))) {
    user.user.order_type = list[0]
  }
}

watch(() => user.user.order_type, (newType) => {
  const currentMethodId = user.user.payment_method_option?.id
  const availableMethods = computedPaymentOptions.value
  if (!availableMethods.some(m => m.id === currentMethodId)) {
    user.user.payment_method_option = null
  }
})

const syncOrderTypeEffects = () => {
  const newType = user.user.order_type
  if (newType?.id == 2 || newType?.id == 6) {
    siteStore.location.tem_cost = siteStore.location.neigborhood.delivery_price
    siteStore.location.neigborhood.delivery_price = 0
  } else {
    const cost = user.user.site?.delivery_cost_cop ?? siteStore?.delivery_price ?? siteStore.location.tem_cost
    if (cost != null) siteStore.location.neigborhood.delivery_price = cost
  }
  const currentMethodId = user.user.payment_method_option?.id
  const availableMethods = computedPaymentOptions.value
  if (!availableMethods.some(m => m.id === currentMethodId)) {
    user.user.payment_method_option = null
  }
}

onMounted(() => {
  syncOrderTypeEffects()
})

watch(() => user.user.order_type, () => { syncOrderTypeEffects() })

/* ================= LÓGICA DE TELÉFONO (Simplificada gracias a PrimeVue Select) ================= */
const phoneError = ref('')
const countries = ref([])

// Ya no necesitamos la lógica manual de "showCountryDropdown" ni "countryQuery"
const initCountries = () => {
  countries.value = buildCountryOptions(lang.value).map(c => ({
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

/* ================= LÓGICA DE CUPONES ================= */
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
      if (Array.isArray(res.sites) && !res.sites.some(s => String(s.site_id) === String(site.site_id))) {
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
    if (temp_discount.value !== newCoupon.code) {
        temp_discount.value = newCoupon.code
    }
    temp_code.value = {
      ...newCoupon,
      status: 'active',
      discount_name: newCoupon.discount_name || newCoupon.name || 'Descuento'
    }
  } else {
    if(temp_code.value?.status === 'active') temp_code.value = {}
  }
}, { immediate: true, deep: true })

watch(() => store.coupon_ui?.draft_code, async () => {
  await autoApplyCouponIfNeeded()
})

/* ================= LÓGICA DE REDIRECCIÓN Y CAMBIO DE SEDE ================= */
watch(() => siteStore.location?.site?.site_id, async (newSiteId, oldSiteId) => {
  ensureValidOrderTypeForCurrentSite()
  await autoApplyCouponIfNeeded()
  if (newSiteId && oldSiteId && String(newSiteId) !== String(oldSiteId)) {
    const newSiteData = siteStore.location.site
    await handleSiteChangeRedirect(newSiteData)
  }
})

const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

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
  if (!user.user.phone_code) {
    const defaultCode = lang.value === 'en' ? 'US' : 'CO'
    user.user.phone_code = countries.value.find(c => c.code === defaultCode)
  }
  try {
    const spData = await (await fetch(`${URI}/site-payments-complete`)).json()
    sitePaymentsComplete.value = spData || []
    ensureValidOrderTypeForCurrentSite()
  } catch (e) { console.error(e) }
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
  padding-bottom: 2rem;
}

/* Redirección (Rocket) */
.redirect-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh;
  background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px);
  z-index: 99999; display: flex; align-items: center; justify-content: center;
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

/* CARDS & SECTIONS */
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

/* FORMULARIOS & OVERRIDES PRIMEVUE */
.form-row { margin-bottom: 1rem; }
.form-row.split { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media(min-width: 600px) { .form-row.split { grid-template-columns: 1fr 1fr; } }
label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: #374151; }

/* Clase para estilizar componentes de PrimeVue igual que el original */
.input-modern {
  width: 100%;
  border-radius: var(--radius-sm);
  /* PrimeVue usa variables a veces, forzamos nuestros colores */
  background: #fff;
}
/* Asegurar altura consistente */
:deep(.p-inputtext) {
    padding: 0.75rem 1rem;
    font-size: 0.95rem;
    border-color: var(--border);
}
:deep(.p-inputtext:focus), :deep(.p-select:focus) {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
}

/* TELÉFONO */
.phone-control-prime { display: flex; gap: 0.5rem; }

/* Ajustes para el Select de PrimeVue del país */
.country-select-prime {
    width: 120px !important;
}
:deep(.country-select-prime .p-select-label) {
    padding: 0.6rem 0.5rem !important; /* Ajuste fino para alinear con InputText */
    display: flex;
    align-items: center;
}
.country-item-selected, .country-item-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.flag-mini { width: 18px; border-radius: 2px; }

.field-error { font-size: 0.8rem; color: var(--error); margin-top: 4px; display: block; }

/* ADDRESS CARD */
.address-card {
  display: flex; align-items: center; gap: 1rem; padding: 1rem; border: 1px solid var(--border);
  border-radius: var(--radius-sm); cursor: pointer; transition: all 0.2s; background: #fff;
}
.address-card:hover { border-color: #000; box-shadow: var(--shadow-card); }
.icon-box-addr {
  width: 40px; height: 40px; background: #f3f4f6; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #666;
}
.has-address .icon-box-addr, .pickup .icon-box-addr { background: #000; color: #fff; }
.addr-info { flex: 1; display: flex; flex-direction: column; }
.addr-title { font-weight: 600; font-size: 0.95rem; }
.addr-text { font-size: 0.85rem; color: var(--text-light); }
.addr-meta { font-size: 0.8rem; margin-top: 4px; display: flex; align-items: center; gap: 5px; }
.badge-delivery { background: #ecfdf5; color: #047857; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
.action-arrow { color: #9ca3af; }

/* CUPONES */
.coupon-wrapper { border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; margin-bottom: 1.5rem; }
.coupon-toggle { display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 1rem; background: #f9fafb; cursor: pointer; }
.coupon-left { display: flex; gap: 0.5rem; align-items: center; font-weight: 600; font-size: 0.9rem; }

.coupon-content { padding: 1rem; border-top: 1px solid var(--border); }
.coupon-input-row { display: flex; gap: 0.5rem; align-items: stretch; }

/* Botón PrimeVue Negro */
.btn-prime-black {
    background: #000 !important;
    border: 1px solid #000 !important;
    color: #fff !important;
    font-weight: 600;
}
.btn-prime-icon {
    padding: 0 1rem !important;
}

.coupon-feedback { margin-top: 0.8rem; font-size: 0.85rem; display: flex; gap: 0.6rem; align-items: flex-start; font-weight: 500; padding: 0.6rem; border-radius: 6px; }
.coupon-feedback.positive { color: var(--success); background: #ecfdf5; }
.coupon-feedback.negative { color: var(--error); background: #fef2f2; }
.feedback-info { display: flex; flex-direction: column; }
.discount-title { font-weight: 700; color: #065f46; font-size: 0.9rem; text-transform: uppercase; }
.discount-amount { font-size: 0.85rem; color: #047857; margin-top: 2px; }

.prime-select-wrapper { width: 100%; }
.w-full { width: 100%; }

.mt-3 { margin-top: 1rem; }
</style>