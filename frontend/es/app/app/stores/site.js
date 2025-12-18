import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { URI } from '../service/conection'

export const useSitesStore = defineStore(
  'site-d3sdd422',
  () => {
    // ───────────── STATE ─────────────
    const location = ref({
      // Agregamos city para persistir la selección del diálogo
      city: null, 
      site: {
        site_id: 1,
        site_name: 'PRINCIPAL',
        site_address: null,
        site_phone: null,
        site_business_hours: null,
        site_business_hours: null,
        wsp_link: null,
        city_id: 8,
        maps: null,
        show_on_web: true,
        email_address: null,
        status: false,
        comming_soon: false,
      },
      neigborhood: {
        name: '',
        delivery_price: null,
        neighborhood_id: null,
      },
    })

    const visibles = ref({
      currentSite: false,
      loading: false,
    })

    const current_delivery = ref(0)

    // 🔥 Status completo de la sede actual
    const status = ref({
      status: 'unknown',          // 'open' | 'closed' | 'unknown'
      next_opening_time: null,    
      networks: null,             
    })

    let statusTimer = null

    // ───────────── ACTIONS ─────────────
    
    // Acción original (mantenemos comportamiento por si lo usas en otro lado)
    function setLocation(newLocation) {
      location.value = newLocation
      visibles.value.currentSite = true // Abre el modal por defecto
    }

    // ✅ NUEVA ACCIÓN: Usada por el SiteDialog para guardar y CERRAR el modal
    function updateLocation(data, price = 0) {
      location.value.city = data.city
      location.value.neigborhood = data.neigborhood
      location.value.site = data.site
      
      if (location.value.neigborhood) {
        location.value.neigborhood.delivery_price = price
      }
      // Actualizamos referencia de precio simple
      current_delivery.value = price
      
      // Cerramos el modal
      visibles.value.currentSite = false
    }

    function setVisible(item, value) {
      if (item === 'loading') {
        visibles.value.loading = true
        if (!value) {
          setTimeout(() => { visibles.value.loading = false }, 500)
        } else {
          visibles.value.loading = value
        }
      } else {
        visibles.value[item] = value
      }
    }

    async function setNeighborhoodPrice() {
      const neighborhoodId = location.value?.neigborhood?.neighborhood_id
      if (!neighborhoodId) return null

      try {
        const res = await fetch(`${URI}/neighborhood/${neighborhoodId}/`)
        if (!res.ok) return null
        const data = await res.json()
        location.value.neigborhood = data
        return data
      } catch (error) {
        console.error('Error fetching neighborhood:', error)
        return null
      }
    }

    function setNeighborhoodPriceCero() {
      if (!location.value.neigborhood) return
      location.value.neigborhood.delivery_price = 0
    }

    function fucion() { return 0 }

    // ───────────── STATUS ─────────────
    async function fetchSiteStatus(explicitSiteId) {
      const siteId = explicitSiteId || (location.value?.site?.site_id ? location.value.site.site_id : null)
      if (!siteId) return

      try {
        const res = await fetch(`${URI}/site/${siteId}/status`)
        if (!res.ok) throw new Error(`Error HTTP ${res.status}`)
        const data = await res.json()
        
        const raw = data.status || 'unknown'
        let normalized = 'unknown'
        if (raw === 'open') normalized = 'open'
        else if (raw === 'closed' || raw === 'close') normalized = 'closed'

        status.value = {
          status: normalized,
          next_opening_time: data.next_opening_time || null,
          networks: data.networks || status.value.networks || null,
        }
      } catch (err) {
        // console.error('Error status sede:', err) // opcional log
        status.value = {
          status: 'unknown',
          next_opening_time: null,
          networks: status.value.networks || null,
        }
      }
    }

    function initStatusWatcher() {
      if (statusTimer) return
      fetchSiteStatus()
      statusTimer = setInterval(() => { fetchSiteStatus() }, 30000)
    }

    watch(
      () => location.value?.site?.site_id,
      (newId, oldId) => {
        if (!newId || newId === oldId) return
        fetchSiteStatus(newId)
      },
      { immediate: true },
    )

    return {
      location,
      visibles,
      current_delivery,
      status,
      fucion,
      setLocation,
      updateLocation, // Exportamos la nueva acción
      setVisible,
      setNeighborhoodPrice,
      setNeighborhoodPriceCero,
      fetchSiteStatus,
      initStatusWatcher,
    }
  },
  {
    persist: {
      key: 'sidtest',
      paths: ['location'],
    },
  },
)