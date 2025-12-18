<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <ToastContainer />
    <siteDialog />
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
  // 0) CAPTURA DE PARÁMETROS EXTERNOS (inserted_by / token)
  // ======================================================
  const qInsertedBy = route.query.inserted_by
  const qToken = route.query.token
  const qiframe = route.query.iframe

  // CAMBIO: Ahora usamos '&&' para exigir que ambos existan
  if (qInsertedBy && qToken) {
    console.log('🔗 Credenciales completas detectadas. Guardando en Store:', { inserted_by: qInsertedBy, token: qToken })
    
    userStore.user = {
      ...userStore.user,
      inserted_by: qInsertedBy,
      token: qToken,
      iframe:qiframe
    }
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

        // A) Restaurar Sede (Contexto visual)
        if (restoredData.site_location) {
          siteStore.location.site = restoredData.site_location
          siteStore.initStatusWatcher()
          siteLoadedFromHash = true
        }

        // B) Restaurar Usuario (Merge con lo que acabamos de guardar de los params)
        if (restoredData.user) {
          userStore.user = {
            ...userStore.user,
            ...restoredData.user
          }
        }

        // ======================================================
        // ✅ C) HIDRATAR LOCATION PARA CHECKOUT
        // ======================================================

        // 1) PRIORIDAD: location_meta
        const metaCity = restoredData?.location_meta?.city
        const metaNb = restoredData?.location_meta?.neigborhood

        if (metaCity) {
          siteStore.location.city = metaCity
        }

        if (metaNb) {
          siteStore.location.neigborhood = {
            ...(siteStore.location.neigborhood || {}),
            ...metaNb,
            neighborhood_id: metaNb.neighborhood_id ?? metaNb.id ?? (siteStore.location.neigborhood?.neighborhood_id),
            name: metaNb.name ?? siteStore.location.neigborhood?.name,
            delivery_price: metaNb.delivery_price ?? siteStore.location.neigborhood?.delivery_price
          }
        }

        // 2) FALLBACK: user.site
        const userSite = userStore.user?.site || restoredData?.user?.site
        const siteNb = userSite?.neighborhood || userSite?.neigborhood
        
        if (siteNb && !siteStore.location.neigborhood?.name) {
          siteStore.location.neigborhood = {
            ...(siteStore.location.neigborhood || {}),
            ...siteNb,
            neighborhood_id: siteNb.neighborhood_id ?? siteNb.id ?? (siteStore.location.neigborhood?.neighborhood_id),
            name: siteNb.name ?? siteStore.location.neigborhood?.name,
            delivery_price: siteNb.delivery_price ?? siteStore.location.neigborhood?.delivery_price
          }
        }

        // 3) COSTO
        const deliveryCostCop = userSite?.delivery_cost_cop
        if (deliveryCostCop != null) {
          if (!siteStore.location.neigborhood) siteStore.location.neigborhood = {}
          if (siteStore.location.neigborhood.delivery_price == null) {
            console.log('✅ Precio de domicilio hidratado desde Hash:', deliveryCostCop)
            siteStore.location.neigborhood.delivery_price = deliveryCostCop
          }
        }

        // 4) Dirección exacta
        if (restoredData?.user?.address && !userStore.user?.address) {
          userStore.user.address = restoredData.user.address
        }

        // C) Restaurar Carrito
        if (restoredData.cart) {
          const cartItems = Array.isArray(restoredData.cart)
            ? restoredData.cart
            : (restoredData.cart.items || [])

          if (cartItems.length > 0) {
            cartStore.cart = Array.isArray(restoredData.cart) ? restoredData.cart : restoredData.cart
          }
        }

        // D) Restaurar Cupón
        if (restoredData.discount) {
          console.log('🎟️ Cupón restaurado desde Hash:', restoredData.discount)
          cartStore.applyCoupon(restoredData.discount)
        }

        if (restoredData.coupon_ui && cartStore.setCouponUi) {
          cartStore.setCouponUi(restoredData.coupon_ui)
        }

        // E) Limpiar la URL (Hash + Params insertados)
        // Nota: Solo limpiamos inserted_by/token si realmente los procesamos (si existían ambos)
        const queryToClean = { ...route.query, hash: undefined }
        
        if (qInsertedBy && qToken) {
           queryToClean.inserted_by = undefined
           queryToClean.token = undefined
        }

        router.replace({ query: queryToClean })

      } else {
        console.warn('⚠️ El hash no retornó datos válidos o ya expiró.')
      }
    } catch (err) {
      console.error('❌ Error crítico restaurando datos por hash:', err)
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
            console.log(siteData)
          }
        }
      }
      
      // Si no hubo hash pero sí llegaron AMBOS params, limpiamos la URL
      if (qInsertedBy && qToken) {
         router.replace({ 
          query: { 
            ...route.query, 
            inserted_by: undefined,
            token: undefined
          } 
        })
      }

    } catch (err) {
      console.error('Error cargando sede desde subdominio:', err)
    }
  }
})
</script>