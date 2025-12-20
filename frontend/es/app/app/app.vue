<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <ToastContainer />

    <CartBar />
    <MenuSearchModal />
  </div>
</template>

<script setup>
import { onMounted } from '#imports'
import { useRoute, useRouter } from '#imports'
import { useSitesStore, useUserStore, usecartStore } from '#imports'
import { useSedeFromSubdomain } from '#imports'
import { URI } from './service/conection'

const siteStore = useSitesStore()
const userStore = useUserStore()
const cartStore = usecartStore()
const sede = useSedeFromSubdomain()
const route = useRoute()
const router = useRouter()

function cleanQueryParams({ removeHash = false, removeCredentials = false, removeIframe = false } = {}) {
  const q = { ...route.query }
  let changed = false

  if (removeHash && q.hash !== undefined) {
    q.hash = undefined
    changed = true
  }

  if (removeCredentials) {
    if (q.inserted_by !== undefined) { q.inserted_by = undefined; changed = true }
    if (q.token !== undefined) { q.token = undefined; changed = true }
  }

  if (removeIframe && q.iframe !== undefined) {
    q.iframe = undefined
    changed = true
  }

  if (changed) router.replace({ query: q })
}

function restoreLocationFromMeta(meta) {
  if (!meta) return

  // ciudad
  if (meta.city) siteStore.location.city = meta.city

  // modo (google | barrios)
  if (meta.mode) siteStore.location.mode = meta.mode

  // ========= GOOGLE MODE =========
  if (meta.mode === 'google') {
    siteStore.location.formatted_address = meta.formatted_address || ''
    siteStore.location.place_id = meta.place_id || ''
    siteStore.location.lat = meta.lat ?? null
    siteStore.location.lng = meta.lng ?? null
    siteStore.location.address_details = meta.address_details ?? null

    const price = meta.delivery_price ?? meta.price ?? 0

    // barrio "vacío" pero EXISTE y con precio
    siteStore.location.neigborhood = {
      name: '',
      delivery_price: price,
      neighborhood_id: null,
      id: null,
      site_id: null,
    }

    siteStore.current_delivery = price
    return
  }

  // ========= BARRIOS MODE =========
  // si manda neigborhood completo
  if (meta.neigborhood) {
    const nb = meta.neigborhood
    const price = nb.delivery_price ?? meta.delivery_price ?? 0

    siteStore.location.neigborhood = {
      name: nb.name || '',
      delivery_price: price,
      neighborhood_id: nb.neighborhood_id ?? nb.id ?? null,
      id: nb.id ?? nb.neighborhood_id ?? null,
      site_id: nb.site_id ?? null,
    }

    siteStore.current_delivery = price
  } else {
    // fallback seguro
    siteStore.location.neigborhood = {
      name: '',
      delivery_price: 0,
      neighborhood_id: null,
      id: null,
      site_id: null,
    }
    siteStore.current_delivery = 0
  }
}

onMounted(async () => {
  let siteLoadedFromHash = false

  const hash = route.query.hash

  // ======================================================
  // 0) RECUPERAR / CAPTURAR CREDENCIALES (F5 safe)
  // ======================================================
  const storedSession = localStorage.getItem('session_external_data')
  if (storedSession) {
    try {
      const parsedSession = JSON.parse(storedSession)
      userStore.user = {
        ...userStore.user,
        ...parsedSession,
      }
      console.log('💾 Sesión restaurada desde LocalStorage (F5 safe)')
    } catch (e) {
      console.error('Error leyendo sesión local', e)
    }
  }

  // URL params (prioridad)
  const qInsertedBy = route.query.inserted_by
  const qToken = route.query.token
  const qiframe = route.query.iframe

  const isIframe = qiframe === '1'

  if (qInsertedBy && qToken) {
    const sessionData = {
      inserted_by: qInsertedBy,
      token: qToken,
      iframe: isIframe,
    }

    console.log('🔗 Credenciales detectadas en URL. Actualizando Store y LocalStorage.')

    userStore.user = {
      ...userStore.user,
      ...sessionData,
    }

    localStorage.setItem('session_external_data', JSON.stringify(sessionData))
  }

  // ======================================================
  // 1) CARGA POR HASH (Desde el Dispatcher)
  // ======================================================
  if (hash) {
    try {
      console.log('🔄 Hash detectado, recuperando sesión...')
      const response = await fetch(`${URI}/data/${hash}`)

      if (response.ok) {
        const jsonResponse = await response.json()
        const restoredData = jsonResponse?.data || {}

        // A) Restaurar Sede
        if (restoredData.site_location) {
          siteStore.location.site = restoredData.site_location
          siteStore.initStatusWatcher()
          siteLoadedFromHash = true
        }

        // B) Restaurar Usuario
        if (restoredData.user) {
          // prioridad iframe (URL/LocalStorage) sobre hash viejo
          const currentIframeState = userStore.user.iframe
          userStore.user = {
            ...userStore.user,
            ...restoredData.user,
            iframe: (currentIframeState !== undefined) ? currentIframeState : restoredData.user.iframe,
          }
        }

        // C) Restaurar Location meta (GOOGLE / BARRIOS)
        restoreLocationFromMeta(restoredData?.location_meta)

        // D) Restaurar Carrito
        if (restoredData.cart) {
          const cartItems = Array.isArray(restoredData.cart)
            ? restoredData.cart
            : (restoredData.cart.items || [])

          if (cartItems.length > 0) {
            cartStore.cart = Array.isArray(restoredData.cart)
              ? restoredData.cart
              : restoredData.cart
          }
        }

        // E) Restaurar Cupón
        if (restoredData.discount) cartStore.applyCoupon(restoredData.discount)
        if (restoredData.coupon_ui && cartStore.setCouponUi) cartStore.setCouponUi(restoredData.coupon_ui)

        // F) Limpiar URL (hash + credenciales + iframe)
        cleanQueryParams({
          removeHash: true,
          removeCredentials: !!(qInsertedBy && qToken),
          removeIframe: qiframe !== undefined,
        })

      } else {
        console.warn('⚠️ El hash no retornó datos válidos.')
      }
    } catch (err) {
      console.error('❌ Error restaurando hash:', err)
    }
  }

  // ======================================================
  // 2) CARGA NORMAL (Por Subdominio)
  // ======================================================
  if (!siteLoadedFromHash) {
    try {
      const currentSede = typeof sede === 'string' ? sede : sede?.value

      if (currentSede) {
        const response = await fetch(`${URI}/sites/subdomain/${currentSede}`)
        if (response.ok) {
          const data = await response.json()
          const siteData = data?.[0] || data
          if (siteData) {
            siteStore.location.site = siteData
            siteStore.initStatusWatcher()
          }
        }
      }

      // Limpieza de params (credenciales + iframe)
      const needsCredClean = !!(qInsertedBy && qToken)
      const needsIframeClean = qiframe !== undefined
      if (needsCredClean || needsIframeClean) {
        cleanQueryParams({
          removeCredentials: needsCredClean,
          removeIframe: needsIframeClean,
        })
      }
    } catch (err) {
      console.error('Error cargando sede:', err)
    }
  }
})
</script>
