<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <ToastContainer />

    <CartBar />
    <MenuSearchModal></MenuSearchModal>
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

onMounted(async () => {
  let siteLoadedFromHash = false
  const hash = route.query.hash
  
  // ======================================================
  // 0) RECUPERAR / CAPTURAR CREDENCIALES
  // ======================================================
  
  // A. Intentar recuperar del LocalStorage primero (Para que sobreviva al F5)
  // Usamos una clave única, por ejemplo 'session_external_data'
  const storedSession = localStorage.getItem('session_external_data')
  if (storedSession) {
    try {
      const parsedSession = JSON.parse(storedSession)
      // Mezclamos con lo que ya tenga el usuario
      userStore.user = {
        ...userStore.user,
        ...parsedSession
      }
      console.log('💾 Sesión restaurada desde LocalStorage (F5 safe)')
    } catch (e) {
      console.error('Error leyendo sesión local', e)
    }
  }

  // B. Capturar de la URL (Tienen prioridad y sobreescriben LocalStorage)
  const qInsertedBy = route.query.inserted_by
  const qToken = route.query.token
  const qiframe = route.query.iframe
  
  // Validación estricta del iframe como Boolean
  const isIframe = qiframe === '1'

  // Si llegan credenciales nuevas en la URL...
  if (qInsertedBy && qToken) {
    const sessionData = { 
      inserted_by: qInsertedBy, 
      token: qToken, 
      iframe: isIframe // Guardamos el booleano real
    }

    console.log('🔗 Credenciales detectadas en URL. Actualizando Store y LocalStorage.')
    
    // 1. Actualizar Store
    userStore.user = {
      ...userStore.user,
      ...sessionData
    }

    // 2. Persistir en LocalStorage (Aquí está el truco para que no mueran al recargar)
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
          // Nota: Aquí damos prioridad a 'iframe' de la URL/LocalStorage sobre el Hash antiguo
          const currentIframeState = userStore.user.iframe 
          
          userStore.user = {
            ...userStore.user,
            ...restoredData.user,
            iframe: (currentIframeState !== undefined) ? currentIframeState : restoredData.user.iframe
          }
        }

        // C) Restaurar Location (Simplificado para el ejemplo)
        const metaCity = restoredData?.location_meta?.city
        if (metaCity) siteStore.location.city = metaCity
        // ... (Tu lógica de location neigborhood va aquí igual que antes) ...

        // D) Restaurar Carrito
        if (restoredData.cart) {
           const cartItems = Array.isArray(restoredData.cart) ? restoredData.cart : (restoredData.cart.items || [])
           if (cartItems.length > 0) cartStore.cart = Array.isArray(restoredData.cart) ? restoredData.cart : restoredData.cart
        }
        
        // E) Restaurar Cupón
        if (restoredData.discount) cartStore.applyCoupon(restoredData.discount)
        if (restoredData.coupon_ui && cartStore.setCouponUi) cartStore.setCouponUi(restoredData.coupon_ui)

        // F) Limpiar la URL (Hash + Params)
        const queryToClean = { ...route.query, hash: undefined }
        if (qInsertedBy && qToken) {
           queryToClean.inserted_by = undefined
           queryToClean.token = undefined
        }
        if (qiframe !== undefined) {
           queryToClean.iframe = undefined
        }

        router.replace({ query: queryToClean })

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
      
      // Limpieza de params
      const queryToClean = { ...route.query }
      let needsClean = false

      if (qInsertedBy && qToken) {
          queryToClean.inserted_by = undefined
          queryToClean.token = undefined
          needsClean = true
      }
      if (qiframe !== undefined) {
          queryToClean.iframe = undefined
          needsClean = true
      }

      if (needsClean) {
          router.replace({ query: queryToClean })
      }

    } catch (err) {
      console.error('Error cargando sede:', err)
    }
  }
})
</script>