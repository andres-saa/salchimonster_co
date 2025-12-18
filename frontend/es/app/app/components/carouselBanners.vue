<template>
  <div class="banner-container">
    <!-- Slider con las imágenes -->
    <div class="slider" :style="sliderStyle">
      <div
        v-for="(banner, idx) in banners"
        :key="banner.id ?? idx"
        class="slide"
      >
        <img
          class="slide-image"
          :src="`${URI}/read-photo-product/${banner.img_identifier}`"
          :alt="banner.title ?? `Banner ${idx}`"
        />

        <!-- Botón dentro del banner -->
        <button
          class="banner-cta"
          type="button"
          @click="onBannerButtonClick(banner)"
        >
          <span>Haz tu pedido</span>
          <Icon name="mdi:cart-outline" class="banner-cta-icon" />
        </button>
      </div>
    </div>

    <!-- Botones de navegación (sólo si hay más de un banner) -->
    <button
      class="nav-btn nav-btn--left"
      v-if="banners.length > 1"
      type="button"
      @click="prevBanner"
    >
      <Icon name="mdi:chevron-left" class="nav-icon" />
    </button>

    <button
      class="nav-btn nav-btn--right"
      v-if="banners.length > 1"
      type="button"
      @click="nextBanner"
    >
      <Icon name="mdi:chevron-right" class="nav-icon" />
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { URI } from '@/service/conection'

// useFetch de Nuxt para evitar llamadas infinitas
const { data: bannersData } = await useFetch(`${URI}/banners`, {
  key: 'home-banners',
  default: () => [],
})

const currentIndex = ref(0)
const INTERVAL_TIME = 3000
const PAUSE_AFTER_INTERACTION = 10000 // 10 segundos

let intervalId = null
let resumeTimeoutId = null

const banners = computed(() => bannersData.value || [])

// 🆕 Controla si hay transición o no
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

const isJumping = ref(false)
const JUMP_ANIMATION_DURATION = 500 // ms, debe coincidir con el CSS


function jumpWithoutTransition(newIndex, withAppear = true) {
  isTransitionEnabled.value = false
  currentIndex.value = newIndex

  if (withAppear) {
    isJumping.value = true
    // Apaga la clase de animación después de que termine
    setTimeout(() => {
      isJumping.value = false
    }, JUMP_ANIMATION_DURATION)
  }

  // Rehabilitamos la transición en el siguiente frame
  requestAnimationFrame(() => {
    isTransitionEnabled.value = true
  })
}

// Lógica de cambio
function goToNext() {
  const total = banners.value.length
  if (!total) return

  if (currentIndex.value === total - 1) {
    jumpWithoutTransition(0, true) // con animación al volver al primero
  } else {
    currentIndex.value = currentIndex.value + 1
  }
}


function goToPrev() {
  const total = banners.value.length
  if (!total) return

  // 👉 aquí queremos animación de aparición en la última
  if (currentIndex.value === 0) {
    jumpWithoutTransition(total - 1, true) // con animación
  } else {
    currentIndex.value = currentIndex.value - 1
  }
}


// Handlers de interacción manual (pausan 10s)
function nextBanner() {
  stopAutoplay()       // detenemos autoplay
  goToNext()           // cambiamos de banner
  scheduleAutoplayResume() // lo reanudamos en 10s
}

function prevBanner() {
  stopAutoplay()
  goToPrev()
  scheduleAutoplayResume()
}

const sliderStyle = computed(() => {
  const translateX = -currentIndex.value * 100
  return {
    transform: `translateX(${translateX}%)`,
    // 🆕 Sólo aplicamos transición cuando isTransitionEnabled es true
    transition: isTransitionEnabled.value ? 'transform 1s ease' : 'none',
  }
})

// Ajusta esta acción a tu flujo real (menu, promo, etc)
function onBannerButtonClick(banner) {
  console.log('Click en banner:', banner)
  // Ejemplo:
  // const router = useRouter()
  // router.push('/menu')
}
</script>

<style scoped>
.banner-container {
  background-color: var(--primary-color);
  overflow: hidden;
  display: flex;
  align-items: center;
  position: relative;
  margin-top: 0;
  padding: 0;
  width: 100%;
}

/* Slider */
.slider {
  display: flex;
  width: 100%;
  padding: 0;
  margin: 0;
}

/* Slide */
.slide {
  position: relative;
  width: 100%;
  min-width: 100%;
}

/* Imagen */
.slide-image {
  width: 100%;
  min-width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  height: 100%;
}

/* Botón CTA del banner */
.banner-cta {
  position: absolute;
  bottom: 1.5rem;
  right: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  border: none;
  font-weight: 600;
  font-size: 0.95rem;
  background-color: #000000c0;
  color: #ffffff;
  cursor: pointer;
  backdrop-filter: blur(4px);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.banner-cta:hover {
  background-color: #000000e0;
}

.banner-cta-icon {
  font-size: 1.1rem;
}

/* Botones de navegación */
.nav-btn {
  position: absolute;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  padding: 0.5rem;
  background-color: #00000070;
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.nav-btn--left {
  left: 1rem;
}

.nav-btn--right {
  right: 1rem;
}

.nav-icon {
  font-size: 1.8rem;
}

/* Mobile */
@media (max-width: 600px) {
  .slide-image {
    aspect-ratio: 4 / 3;
  }

  .banner-cta {
    bottom: 1rem;
    right: 1rem;
    padding: 0.6rem 1.2rem;
    font-size: 0.85rem;
  }
}

/* Ajustes nav buttons */
@media (max-width: 1100px) {
  .nav-btn--right {
    right: 0.5rem;
  }
  .nav-btn--left {
    left: 0.5rem;
  }
}
</style>
