<template>
  <div class="carta-page">
    
    <div class="carta-body">

      <div v-if="loading" class="state-container loading">
        <div class="spinner"></div>
        <p>Cargando carta de España...</p>
      </div>

      <div v-else-if="error" class="state-container error">
        <span class="icon">⚠️</span>
        <p>No pudimos cargar la información.</p>
        <button @click="handleRetry" class="retry-btn">Reintentar</button>
      </div>

      <div v-else-if="!activeMenu || !activeCards.length" class="state-container empty">
        <span class="icon">🇪🇸</span>
        <p>Cargando carta de España...</p>
      </div>

      <div v-else class="image-gallery">
        <div 
          v-for="card in activeCards" 
          :key="card.id"
          class="image-wrapper"
          :class="{ 'is-loaded': imageStates[card.id] === 'loaded' }"
          @click="openZoom(bigUrl(card.img_identifier))"
        >
          <div v-if="imageStates[card.id] !== 'loaded'" class="skeleton-loader"></div>

          <img
            :src="bigUrl(card.img_identifier)"
            :alt="`Carta España`"
            class="main-image"
            loading="lazy"
            @load="onImageLoad(card.id)"
            @error="onImageError($event, card.id)"
          />
        </div>
      </div>
    
    </div>

    <Teleport to="body">
      <Transition name="fade">
        <div v-if="zoomedImage" class="lightbox-overlay" @click="closeZoom">
          <button class="close-btn">&times;</button>
          <img :src="zoomedImage" class="lightbox-image" @click.stop />
        </div>
      </Transition>
    </Teleport>

    <a
      href="https://local.bot.salchimonster.com/ubicacion/1"
      class="promo-fab"
      :class="{ 'is-hidden': isScrolling }"
    >
      <div class="glow-ring"></div> 
      <div class="fab-content">
        <img class="fab-icon" :src="`${URI}/read-photo-product/5Dqs9XtT`" alt="Promos">
      </div>
    </a>

  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const URI = 'https://backend.salchimonster.com'

// --- ESTADOS ---
const windowWidth = ref(1024)
const isScrolling = ref(false)
let hideTimer = null

const zoomedImage = ref(null)
const imageStates = reactive({})

// --- FETCH DATA ---
const {
  data: rawResponse,
  pending: loading,
  error,
  refresh
} = await useFetch(`${URI}/data/cata-tiendas-sm`, {
  lazy: true, server: false, timeout: 15000, retry: 1
})

const handleRetry = async () => { error.value = null; await refresh() }

// Acceso profundo a data.data
const menuData = computed(() => rawResponse.value?.data?.data || [])

// --- HELPERS ---
const isMobile = computed(() => windowWidth.value < 600)
const updateWidth = () => { if (typeof window !== 'undefined') windowWidth.value = window.innerWidth }
const bigUrl = (id) => `${URI}/read-photo-product/${id}`
const plainUrl = (id) => `${URI}/read-photo-product/${id}`
const normalize = (s) => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim()

// --- LÓGICA ESPAÑA ---
const activeMenu = computed(() => {
  if (!menuData.value.length) return null
  return menuData.value.find(m => m.id === 'co-general' || normalize(m.name).includes('colombia')) || null
})

const activeCards = computed(() => {
  const menu = activeMenu.value
  if (!menu || !menu.cartas) return []
  const lang = 'es'

  const getCards = (orientation) => {
    return (menu.cartas[orientation] && Array.isArray(menu.cartas[orientation][lang])) 
      ? menu.cartas[orientation][lang] 
      : []
  }

  const listHorizontal = getCards('horizontal')
  const listVertical = getCards('vertical')

  // Lógica simplificada: Devuelve lo que encuentre, priorizando vertical en móvil si existe,
  // pero como en tu JSON vertical está vacío, usará horizontal.
  if (isMobile.value && listVertical.length > 0) return listVertical
  if (listHorizontal.length > 0) return listHorizontal
  if (listVertical.length > 0) return listVertical
  
  return []
})

// --- UI EVENTOS ---
const onImageLoad = (id) => { imageStates[id] = 'loaded' }
const onImageError = (e, id) => { imageStates[id] = 'error'; if (e.target.src !== plainUrl(id)) e.target.src = plainUrl(id) }
const openZoom = (url) => { zoomedImage.value = url; document.body.style.overflow = 'hidden' }
const closeZoom = () => { zoomedImage.value = null; document.body.style.overflow = '' }
const onScroll = () => {
  if (!isScrolling.value) isScrolling.value = true
  clearTimeout(hideTimer)
  hideTimer = setTimeout(() => { isScrolling.value = false }, 180)
}

onMounted(() => {
  if (user && (!user.lang?.name || user.lang.name !== 'es')) {
     if(!user.lang) user.lang = {}
     user.lang = { name: 'es', label: 'Español', flag: 'https://flagcdn.com/w20/es.png' }
  }
  if (typeof window !== 'undefined') {
    updateWidth()
    window.addEventListener('resize', updateWidth, { passive: true })
    window.addEventListener('scroll', onScroll, { passive: true })
  }
})
onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateWidth); window.removeEventListener('scroll', onScroll)
  }
  clearTimeout(hideTimer)
})
</script>

<style scoped>
/* 1. RESET Y FONDO BLANCO */
.carta-page {
  background-color: #ffffff;
  min-height: 100vh;
  width: 100%;
  margin: 0;
  padding: 0; /* Sin padding global */
}

/* 2. CONTENEDOR TOTALMENTE FLUIDO */
.carta-body {
  width: 100%;
  margin: 0;
  padding: 0;
  max-width: none; /* Quitamos límite de ancho */
}

/* 3. GALERÍA SIN ESPACIOS */
.image-gallery {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 0;     /* Pegadas verticalmente */
  padding: 0; /* Sin relleno lateral */
}

/* 4. WRAPPER SIN BORDES REDONDEADOS */
.image-wrapper {
  position: relative;
  width: 100%;
  display: block;
  background: #f4f4f4;
  cursor: zoom-in;
  /* IMPORTANTE: */
  border-radius: 0 !important; 
  margin: 0 !important;
  box-shadow: none !important;
  border: none !important;
}

/* 5. IMAGEN OCUPA EL 100% DEL ANCHO */
.main-image {
  width: 100%;
  height: auto; /* Mantiene proporción, crece hacia abajo */
  display: block;
  object-fit: contain; /* Asegura que se vea completa a lo ancho */
  opacity: 0;
  transition: opacity 0.5s ease;
  border-radius: 0 !important; /* Aseguramos cero borde en la img también */
}
.image-wrapper.is-loaded .main-image { opacity: 1; }

/* Estados de carga/error (centrados) */
.state-container {
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  min-height: 50vh; color: #666; gap: 1rem; text-align: center; padding: 2rem;
}
.spinner {
  width: 40px; height: 40px; border: 4px solid rgba(0,0,0,0.1);
  border-top-color: #ff0055; border-radius: 50%; animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Lightbox y FAB se mantienen igual */
.lightbox-overlay {
  position: fixed; inset: 0; z-index: 10000; background-color: rgba(0,0,0,0.95);
  display: flex; justify-content: center; align-items: center;
}
.lightbox-image { max-width: 100vw; max-height: 100vh; object-fit: contain; }
.close-btn {
  position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2);
  border: none; color: white; font-size: 2rem; width: 50px; height: 50px;
  border-radius: 50%; cursor: pointer; z-index: 11;
  display: flex; align-items: center; justify-content: center;
}
.promo-fab {
  position: fixed; right: 20px; bottom: 30px; width: 60px; height: 60px; z-index: 9000;
  border-radius: 50%; transition: transform 0.3s ease, opacity 0.3s ease;
}
.promo-fab.is-hidden { transform: translateX(150%); opacity: 0.5; pointer-events: none; }
.fab-content {
  position: relative; width: 100%; height: 100%; border-radius: 50%; overflow: hidden;
  background: white; border: 2px solid white; z-index: 2; display: flex;
  justify-content: center; align-items: center; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}
.fab-icon { width: 100%; height: 100%; object-fit: cover; }
.glow-ring {
  position: absolute; inset: -5px; border-radius: 50%;
  background: linear-gradient(45deg, #ff0055, #00ddff, #ff0055);
  background-size: 400%; z-index: 1; opacity: 0.7; filter: blur(8px);
  animation: glowing 3s linear infinite;
}
@keyframes glowing { 0% { background-position: 0 0; } 50% { background-position: 400% 0; } 100% { background-position: 0 0; } }
</style>