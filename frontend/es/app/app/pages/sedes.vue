<template>
  <div class="main-container">
    <h1 class="sr-only">Nuestras Sedes Salchimonster</h1>

    <div class="container">
      <div v-if="pending && !sedes.length" class="loading-state">
        <div class="spinner"></div>
        <p>Cargando sedes...</p>
      </div>

      <article
        v-for="sede in filteredSedes"
        :key="sede.site_id"
        class="sede-card"
        @click="openSedeDialog(sede)"
        itemscope
        itemtype="https://schema.org/Restaurant"
      >
        <div class="sede-image-wrapper">
<img
  :src="getOptimizedSrc(sede)"
  :alt="`Fachada Restaurante Salchimonster ${sede.site_name}`"
  class="sede-image"
  loading="lazy"
  @error="(e) => onImgError(e, sede)"
/>
          
          <div class="map-floating-btn" @click.stop>
            <a
              :href="sede.maps"
              target="_blank"
              rel="noopener noreferrer"
              :aria-label="`Ver ubicación de ${sede.site_name} en Google Maps`"
            >
               <Icon name="mdi:google-maps" class="map-icon" />
            </a>
          </div>

          <div class="sede-overlay">
            <div class="sede-info">
              <p class="sede-location">
                <Icon name="mdi:map-marker" class="icon-small" />
                {{ cityName(sede.city_id) }}
              </p>
              
              <h3 class="sede-name" itemprop="name">
                SALCHIMONSTER {{ sede.site_name }}
              </h3>  

              <address class="sede-address" itemprop="address">
                {{ sede.site_address }}
              </address>

              <a
                v-if="waLink(sede)"
                :href="waLink(sede)"
                target="_blank"
                rel="noopener noreferrer"
                class="sede-action-link"
                @click.stop
              >
                <Icon name="mdi:whatsapp" class="whatsapp-icon" />
                <span itemprop="telephone">{{ displayPhone(sede.site_phone) }}</span>
              </a>
              <p v-else class="sede-phone-text">
                <Icon name="mdi:whatsapp" class="whatsapp-icon" />
                <span>{{ displayPhone(sede.site_phone) }}</span>
              </p>
            </div>
          </div>
        </div>
      </article>
    </div>

    <Transition name="fade">
      <div
        v-if="showDialog && selectedSede"
        class="dialog-overlay"
        @click.self="closeDialog"
        role="dialog"
        aria-modal="true"
      >
        <div class="dialog">
          <button class="dialog-close" @click="closeDialog" aria-label="Cerrar ventana">
            <Icon name="mdi:close" />
          </button>

          <h2 class="dialog-title">
            SALCHIMONSTER {{ selectedSede.site_name }}
          </h2>

          <div class="dialog-content">
            <div class="dialog-row">
              <Icon name="mdi:map-marker" class="dialog-icon" />
              <span>{{ cityName(selectedSede.city_id) }}</span>
            </div>

            <div class="dialog-row">
              <span class="dialog-label">Dirección:</span>
              <span class="dialog-value">{{ selectedSede.site_address }}</span>
            </div>

            <div class="dialog-row">
              <span class="dialog-label">Teléfono:</span>
              <a
                v-if="waLink(selectedSede)"
                :href="waLink(selectedSede)"
                target="_blank"
                rel="noopener"
                class="dialog-link"
              >
                {{ displayPhone(selectedSede.site_phone) }}
              </a>
              <span v-else>{{ displayPhone(selectedSede.site_phone) }}</span>
            </div>

            <div class="dialog-action" v-if="selectedSede.maps">
              <a
                :href="selectedSede.maps"
                target="_blank"
                rel="noopener"
                class="btn-maps"
              >
                <Icon name="mdi:google-maps" />
                Abrir en Google Maps
              </a>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useHead, useAsyncData, useSitesStore } from '#imports'
import { URI } from '@/service/conection'

const sitesStore = useSitesStore()
const CACHE_TTL = 30 * 60 * 1000 
const FALLBACK_IMG = 'https://gestion.salchimonster.com/images/logo.png'

const showDialog = ref(false)
const selectedSede = ref(null)

const {
  data: rawData,
  pending,
  refresh
} = useAsyncData(
  'sites-view-data',
  async () => {
    const [sitesRes, citiesRes] = await Promise.all([
      $fetch(`${URI}/sites`),
      $fetch(`${URI}/cities`)
    ])
    return { sites: sitesRes || [], cities: citiesRes || [] }
  },
  { server: true, default: () => ({ sites: [], cities: [] }) }
)

if (process.client) {
  const cachedWrapper = sitesStore.getSitesViewCache ? sitesStore.getSitesViewCache() : null
  if (cachedWrapper && cachedWrapper.data && cachedWrapper.timestamp) {
    if (Date.now() - cachedWrapper.timestamp < CACHE_TTL) {
      rawData.value = cachedWrapper.data
    }
  }
}

watch(rawData, (val) => {
  if (process.client && val?.sites?.length > 0 && sitesStore.setSitesViewCache) {
    sitesStore.setSitesViewCache({ data: val, timestamp: Date.now() })
  }
}, { immediate: true })

let refreshInterval = null
onMounted(async () => {
  if (!pending.value) refresh()
  refreshInterval = setInterval(() => refresh(), 10 * 60 * 1000)
})
onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

const sedes = computed(() => rawData.value?.sites || [])
const cities = computed(() => rawData.value?.cities || [])

const filteredSedes = computed(() => {
  return sedes.value.filter(s => 
    s.city_id && s.show_on_web && !s.comming_soon && 
    s.time_zone === 'America/Bogota' && s.site_id !== 32
  )
})

/* IMAGENES CON FALLBACK EN CASCADA */
const getOptimizedSrc = (sede) => {
  // Prioridad 1: Si existe img_id, usamos la ruta de foto de producto
  if (sede.img_id) {
    return `${URI}/read-photo-product/${sede.img_id}`
  }
  // Prioridad 2: Si no hay img_id, intentamos con la ruta basada en site_id
  return `${URI}/read-product-image/600/site-${sede.site_id}`
}

const onImgError = (event, sede) => {
  const imgElement = event.target
  const secondarySrc = `${URI}/read-product-image/600/site-${sede.site_id}`
  
  // Verificamos qué URL es la que falló para decidir el siguiente paso
  
  // Si la imagen actual YA ES el fallback (logo), no hacemos nada para evitar bucles
  if (imgElement.src === FALLBACK_IMG) return

  // Si la imagen que falló es la ruta secundaria (la que usa site-{id}), 
  // significa que ya fallaron las dos opciones. Vamos al logo.
  if (imgElement.src.includes(`site-${sede.site_id}`)) {
    imgElement.src = FALLBACK_IMG
  } 
  // Si no era la secundaria (significa que falló la img_id), intentamos la secundaria
  else {
    imgElement.src = secondarySrc
  }
}

 

/* UTILIDADES */
const byImgIdentifier = (identifier) => `${URI}/read-photo-product/${identifier}`
const cityName = (city_id) => cities.value.find(s => s.city_id === city_id)?.city_name ?? ''
const displayPhone = (raw = '') => raw?.trim() || '—'
const toE164CO = (raw = '') => {
  let d = String(raw).replace(/\D/g, '')
  if (!d) return ''
  if (d.startsWith('57')) return d
  if (d.length === 10 && d.startsWith('3')) return '57' + d
  return d
}
const waLink = (sede) => {
  const num = toE164CO(sede?.site_phone || '')
  if (!num) return ''
  const msg = `Hola, quiero más info sobre SALCHIMONSTER ${sede?.site_name ?? ''} en ${cityName(sede?.city_id)}.`
  return `https://wa.me/${num}?text=${encodeURIComponent(msg)}`
}

const openSedeDialog = (sede) => {
  selectedSede.value = sede
  showDialog.value = true
}
const closeDialog = () => {
  showDialog.value = false
  selectedSede.value = null
}

useHead(() => {
  const structuredData = filteredSedes.value.map(sede => ({
    "@context": "https://schema.org",
    "@type": "Restaurant",
    "name": `Salchimonster ${sede.site_name}`,
    "image": sede.img_id ? byImgIdentifier(sede.img_id) : FALLBACK_IMG,
    "address": {
      "@type": "PostalAddress",
      "streetAddress": sede.site_address,
      "addressLocality": cityName(sede.city_id),
      "addressCountry": "CO" 
    },
    "telephone": sede.site_phone,
    "url": sede.maps
  }))

  return {
    title: 'Nuestras Sedes | Salchimonster',
    meta: [{ name: 'description', content: 'Encuentra tu restaurante Salchimonster más cercano.' }],
    script: [{ type: 'application/ld+json', children: JSON.stringify(structuredData) }]
  }
})
</script>

<style scoped>
:root {
  --primary: var(--primary-color);
  --overlay-gradient: linear-gradient(to top, rgba(0, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0.6) 50%, transparent 100%);
}

.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }

.main-container { width: 100%; padding-bottom: 3rem; min-height: 60vh; }
.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 3rem; color: white; gap: 1rem;
}

.spinner {
  width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.3);
  border-top-color: var(--primary-color); border-radius: 50%; animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
  width: 100%; max-width: 1400px; margin: 0 auto; padding: 2rem;
}

/* Card Styles */
.sede-card {
  position: relative; border-radius: 1rem; overflow: hidden; cursor: pointer;
  background-color: #000; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  transition: all 0.5s ease;
}
.sede-card:hover { transform: translateY(-8px); box-shadow: 0 12px 24px rgba(0, 0, 0, 0.6); }

.sede-image-wrapper {
  position: relative; width: 100%; aspect-ratio: 3/4; background: #222; overflow: hidden;
}

/* Imagen Normal CSS */
.sede-image {
  width: 100%; 
  height: 100%; 
  object-fit: cover; 
  /* Eliminada la opacidad 0 y las transiciones de carga */
  display: block; 
}

.sede-card:hover .sede-image { transform: scale(1.05);  }

.map-floating-btn {
  position: absolute; top: 1rem; right: 1rem; z-index: 2;
  background: rgba(255, 255, 255, 0.9); border-radius: 50%; width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3); transition: background 0.2s, transform 0.2s;
}
.map-floating-btn:hover { background: #fff; transform: scale(1.1); }
.map-icon { font-size: 1.5rem; color: #333; }

.sede-overlay {
  position: absolute; inset: 0;
  background: var(--overlay-gradient, linear-gradient(to top, rgba(0,0,0,0.95), transparent));
  display: flex; flex-direction: column; justify-content: flex-end; padding: 1.5rem;
}
.sede-info { color: white; }
.sede-location {
  color: var(--primary-color); font-weight: 700; font-size: 0.9rem; margin-bottom: 0.25rem;
  display: flex; align-items: center; gap: 0.25rem; text-transform: uppercase; letter-spacing: 0.5px;
}
.sede-name { font-size: 1.5rem; font-weight: 800; margin: 0 0 0.5rem 0; line-height: 1.2; }
.sede-address { font-style: normal; font-size: 0.95rem; opacity: 0.9; margin-bottom: 1rem; display: block; }

.sede-action-link, .sede-phone-text {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(4px);
  padding: 0.5rem 1rem; border-radius: 2rem; color: white;
  text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: background 0.2s ease;
}
.sede-action-link:hover { background: rgba(37, 211, 102, 0.2); color: #4ade80; }
.whatsapp-icon { color: #4ade80; font-size: 1.2rem; }

/* Dialog Styles */
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(5px);
  z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.dialog {
  background: #1e1e1e; color: white; width: 100%; max-width: 500px;
  border-radius: 1rem; padding: 2rem; position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}
.dialog-close {
  position: absolute; top: 1rem; right: 1rem; background: transparent; border: none;
  color: white; font-size: 1.5rem; cursor: pointer; opacity: 0.7; transition: opacity 0.2s;
}
.dialog-close:hover { opacity: 1; }
.dialog-title {
  font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; color: var(--primary-color);
  border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem;
}
.dialog-row { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem; font-size: 1rem; }
.dialog-label { font-weight: 600; color: #aaa; min-width: 80px; }
.dialog-link { color: white; text-decoration: underline; text-decoration-color: var(--primary-color); text-underline-offset: 3px; }
.dialog-action { margin-top: 2rem; }
.btn-maps {
  display: flex; align-items: center; justify-content: center; gap: 0.5rem; width: 100%;
  padding: 0.8rem; background: var(--primary-color); color: black; font-weight: 700;
  border-radius: 0.5rem; text-decoration: none; transition: filter 0.2s;
}
.btn-maps:hover { filter: brightness(1.1); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

*{
  transition: all ease .3s;
}
</style>