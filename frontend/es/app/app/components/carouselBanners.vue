<template>
  <div class="banner-container" v-if="banners.length > 0">
    <div class="slider" :style="sliderStyle">
      <div
        v-for="(banner, idx) in banners"
        :key="banner.id ?? idx"
        class="slide"
        :class="{ 'has-link': !!banner.link }"
        @click="onBannerClick(banner)"
      >
        <img
          class="slide-image"
          :src="`${URI}/read-photo-product/${banner.img_identifier}`"
          :alt="`Banner Colombia ${idx + 1}`"
          loading="lazy"
        />
      </div>
    </div>

    <button
      class="nav-btn nav-btn--left"
      v-if="banners.length > 1"
      type="button"
      @click.stop="prevBanner"
    >
      <Icon name="mdi:chevron-left" class="nav-icon" />
    </button>

    <button
      class="nav-btn nav-btn--right"
      v-if="banners.length > 1"
      type="button"
      @click.stop="nextBanner"
    >
      <Icon name="mdi:chevron-right" class="nav-icon" />
    </button>

    <div class="indicators" v-if="banners.length > 1">
      <span 
        v-for="(_, idx) in banners" 
        :key="idx"
        class="dot"
        :class="{ active: idx === currentIndex }"
      ></span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { URI } from '@/service/conection'

const router = useRouter()
const DB_ID = 'banners_master_v1'

// 1. Fetch al JSON maestro
const { data: dbData } = await useFetch(`${URI}/data/${DB_ID}`, {
  key: 'home-banners-master',
  // Evitamos cache agresivo para ver cambios recientes del gestor
  headers: { 'Cache-Control': 'no-cache' } 
})

// 2. Extraemos SOLO los banners de Colombia ('co')
const banners = computed(() => {
  // La estructura del backend suele ser { data: { co: [], us: [], es: [] } }
  const rawData = dbData.value?.data || {}
  return rawData.us || []
})

// --- LÓGICA DEL SLIDER (Tu código original optimizado) ---
const currentIndex = ref(0)
const INTERVAL_TIME = 4000
const PAUSE_AFTER_INTERACTION = 8000

let intervalId = null
let resumeTimeoutId = null

const isTransitionEnabled = ref(true)

onMounted(() => {
  startAutoplay()
})

onBeforeUnmount(() => {
  stopAutoplay()
  clearResumeTimeout()
})

function startAutoplay() {
  if (!intervalId && banners.value.length > 1) {
    intervalId = setInterval(() => {
      goToNext()
    }, INTERVAL_TIME)
  }
}

function stopAutoplay() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

function clearResumeTimeout() {
  if (resumeTimeoutId) {
    clearTimeout(resumeTimeoutId)
    resumeTimeoutId = null
  }
}

function scheduleAutoplayResume() {
  clearResumeTimeout()
  resumeTimeoutId = setTimeout(() => {
    resumeTimeoutId = null
    startAutoplay()
  }, PAUSE_AFTER_INTERACTION)
}

function goToNext() {
  if (!banners.value.length) return
  if (currentIndex.value === banners.value.length - 1) {
    currentIndex.value = 0 
  } else {
    currentIndex.value++
  }
}

function goToPrev() {
  if (!banners.value.length) return
  if (currentIndex.value === 0) {
    currentIndex.value = banners.value.length - 1
  } else {
    currentIndex.value--
  }
}

// Handlers manuales
function nextBanner() {
  stopAutoplay()
  goToNext()
  scheduleAutoplayResume()
}

function prevBanner() {
  stopAutoplay()
  goToPrev()
  scheduleAutoplayResume()
}

// 3. Manejo del Clic en la Imagen
function onBannerClick(banner) {
  if (!banner.link) return

  // Pausar slider si el usuario interactúa
  stopAutoplay()
  scheduleAutoplayResume()

  // Detectar si es link externo o interno
  if (banner.link.startsWith('http')) {
    window.open(banner.link, '_blank')
  } else {
    router.push(banner.link)
  }
}

const sliderStyle = computed(() => {
  const translateX = -currentIndex.value * 100
  return {
    transform: `translateX(${translateX}%)`,
    transition: isTransitionEnabled.value ? 'transform 0.6s cubic-bezier(0.25, 1, 0.5, 1)' : 'none',
  }
})
</script>

<style scoped>
.banner-container {
  background-color: #f1f1f1; /* Fondo neutro mientras carga */
  overflow: hidden;
  display: flex;
  align-items: center;
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9; /* Mantiene el espacio estable */
  border-radius: 0px;   /* Opcional: bordes redondeados */
}

/* Slider */
.slider {
  display: flex;
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  will-change: transform; /* Optimización de rendimiento */
}

/* Slide */
.slide {
  position: relative;
  width: 100%;
  min-width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.slide.has-link {
  cursor: pointer;
}

/* Imagen */
.slide-image {
  width: 100%;
  height: 100%;
  object-fit: cover; /* Asegura que la imagen llene todo el espacio sin deformarse */
  display: block;
}

/* Botones de navegación */
.nav-btn {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.3);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
  z-index: 2;
  opacity: 0; /* Ocultos por defecto para limpieza */
}

/* Mostrar botones al hacer hover en el contenedor */
.banner-container:hover .nav-btn {
  opacity: 1;
}

.nav-btn:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

.nav-btn--left {
  left: 1rem;
}

.nav-btn--right {
  right: 1rem;
}

.nav-icon {
  font-size: 2rem;
}

/* Indicadores (Puntos) */
.indicators {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.5rem;
  z-index: 2;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s;
}

.dot.active {
  background-color: white;
  transform: scale(1.2);
}

/* Mobile */
@media (max-width: 768px) {
  .banner-container {
    aspect-ratio: 4 / 3; /* Más cuadrado en móvil */
  }
  
  .nav-btn {
    opacity: 1; /* Siempre visibles en móvil */
    width: 32px;
    height: 32px;
  }
  
  .nav-icon {
    font-size: 1.5rem;
  }
}
</style>