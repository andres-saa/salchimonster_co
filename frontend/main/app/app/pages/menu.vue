<template>
  <div class="carta-page">
    
    <div class="carta-body">

      <div v-if="loading" class="state-container loading">
        <div class="spinner"></div>
        <p>Cargando menú de Colombia...</p>
      </div>

      <div v-else-if="error" class="state-container error">
        <span class="icon">⚠️</span>
        <p>No pudimos cargar la carta.</p>
        <button @click="handleRetry" class="retry-btn">Reintentar</button>
      </div>

      <div v-else-if="!activeMenu || !activeCards.length" class="state-container empty">
        <span class="icon">🇨🇴</span>
        <p>La carta de Colombia no está disponible en este momento.</p>
      </div>

      <div v-else class="image-gallery">
        <div 
          v-for="card in activeCards" 
          :key="card.id"
          class="image-wrapper"
          :class="{ 
            'is-loaded': imageStates[card.id] === 'loaded',
            'horizontal-layout': isHorizontalLayout,
            'vertical-layout': !isHorizontalLayout
          }"
          @click="openZoom(bigUrl(card.img_identifier))"
        >
          <div v-if="imageStates[card.id] !== 'loaded'" class="skeleton-loader"></div>

          <img
            :src="bigUrl(card.img_identifier)"
            :alt="`Menú Colombia`"
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
      aria-label="Ver promociones"
    >
      <div class="glow-ring"></div> 
      <div class="fab-content">
        <img
          class="fab-icon"
          :src="`${URI}/read-photo-product/5Dqs9XtT`"
          alt="Promos"
        >
      </div>
    </a>

  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'

const URI = 'https://backend.salchimonster.com'

// --- ESTADOS UI ---
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
  lazy: true,
  server: false,
  timeout: 15000,
  retry: 1
})

const handleRetry = async () => {
  error.value = null
  await refresh()
}

// 1. CORRECCIÓN JSON: Acceso profundo a data.data
const menuData = computed(() => {
  if (!rawResponse.value) return []
  return rawResponse.value.data?.data || []
})

// --- RESPONSIVE & HELPERS ---
const isMobile = computed(() => windowWidth.value < 600)

const updateWidth = () => {
  if (typeof window === 'undefined') return
  windowWidth.value = window.innerWidth
}

const bigUrl = (id) => `${URI}/read-photo-product/${id}`
const plainUrl = (id) => `${URI}/read-photo-product/${id}`
const normalize = (s) => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim()

// --- LÓGICA PRINCIPAL (COLOMBIA) ---

// 2. Encontrar el objeto de datos para Colombia
const activeMenu = computed(() => {
  if (!menuData.value.length) return null
  // Busca ID "colombia" o nombre "Colombia"
  return menuData.value.find(m => m.id === 'es-general' || normalize(m.name).includes('España')) || null
})

// Variable reactiva para controlar estilos según la orientación elegida
const isHorizontalLayout = ref(false)

// 3. Obtener imágenes
const activeCards = computed(() => {
  const menu = activeMenu.value
  if (!menu || !menu.cartas) return []

  const lang = 'es'

  // Helper para sacar array seguro
  const getCards = (orientation) => {
    if (menu.cartas[orientation] && Array.isArray(menu.cartas[orientation][lang])) {
      return menu.cartas[orientation][lang]
    }
    return []
  }

  const listHorizontal = getCards('horizontal')
  const listVertical = getCards('vertical')

  // LÓGICA DE PRIORIDAD (Standard):
  // 1. Si es móvil y hay verticales -> Usar Vertical
  if (isMobile.value && listVertical.length > 0) {
    isHorizontalLayout.value = false
    return listVertical.sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
  }

  // 2. Si es Desktop (o móvil sin verticales), probar Horizontal
  if (listHorizontal.length > 0) {
    isHorizontalLayout.value = true
    return listHorizontal.sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
  }

  // 3. Fallback final a vertical
  if (listVertical.length > 0) {
    isHorizontalLayout.value = false
    return listVertical.sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
  }

  return []
})

// --- EVENTOS UI ---
const onImageLoad = (id) => { imageStates[id] = 'loaded' }
const onImageError = (event, id) => {
  imageStates[id] = 'error'
  if (event.target.src !== plainUrl(id)) event.target.src = plainUrl(id)
}
const openZoom = (url) => { zoomedImage.value = url; document.body.style.overflow = 'hidden' }
const closeZoom = () => { zoomedImage.value = null; document.body.style.overflow = '' }
const onScroll = () => {
  if (!isScrolling.value) isScrolling.value = true
  clearTimeout(hideTimer)
  hideTimer = setTimeout(() => { isScrolling.value = false }, 180)
}

// --- LIFECYCLE ---
onMounted(() => {
  if (typeof window !== 'undefined') {
    updateWidth()
    window.addEventListener('resize', updateWidth, { passive: true })
    window.addEventListener('scroll', onScroll, { passive: true })
  }
})
onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateWidth)
    window.removeEventListener('scroll', onScroll)
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
  padding: 0;
  padding-bottom: 80px; /* Espacio para el FAB si es necesario */
}

/* 2. CONTENEDOR TOTALMENTE FLUIDO */
.carta-body {
  width: 100%;
  margin: 0;
  padding: 0;
  max-width: none;
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
  /* IMPORTANTE: Reset total de bordes */
  border-radius: 0 !important; 
  margin: 0 !important;
  box-shadow: none !important;
  border: none !important;
}

/* 5. IMAGEN OCUPA EL 100% DEL ANCHO */
.main-image {
  width: 100%;
  height: auto; /* Crece hacia abajo según su ratio */
  display: block;
  object-fit: contain; /* Se asegura que se vea todo el ancho */
  opacity: 0;
  transition: opacity 0.5s ease;
  border-radius: 0 !important;
}
.image-wrapper.is-loaded .main-image { opacity: 1; }

/* Estados */
.state-container {
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  min-height: 50vh; color: #666; gap: 1rem; text-align: center; padding: 2rem;
}
.spinner {
  width: 40px; height: 40px; border: 4px solid rgba(0,0,0,0.1);
  border-top-color: #ff0055; border-radius: 50%; animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Lightbox */
.lightbox-overlay {
  position: fixed; inset: 0; z-index: 10000; background-color: rgba(0, 0, 0, 0.95);
  display: flex; justify-content: center; align-items: center; backdrop-filter: blur(5px);
}
.lightbox-image { max-width: 100vw; max-height: 100vh; object-fit: contain; }
.close-btn {
  position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2);
  border: none; color: white; font-size: 2rem; width: 50px; height: 50px;
  border-radius: 50%; cursor: pointer; z-index: 10;
  display: flex; align-items: center; justify-content: center;
}

/* FAB */
.promo-fab {
  position: fixed; right: 20px; bottom: 30px; width: 70px; height: 70px; z-index: 9000;
  display: flex; align-items: center; justify-content: center; text-decoration: none;
  border-radius: 50%; transform: translateX(0); transition: transform 0.3s ease, opacity 0.3s ease;
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