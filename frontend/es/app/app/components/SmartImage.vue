<script setup lang="ts">
import { ref, computed, watch } from 'vue';

// --- Definición de Props ---
interface Props {
  src: string;              // URL de la imagen
  alt?: string;             // Texto alternativo
  fallbackSrc?: string;     // URL de imagen si la principal falla
  ratio?: string;           // Aspect Ratio CSS (ej: '16/9', '1/1', '4/3')
  zoomable?: boolean;       // ¿Permitir clic para ver en grande?
  objectFit?: 'cover' | 'contain' | 'fill'; // Cómo se ajusta la imagen
}

const props = withDefaults(defineProps<Props>(), {
  alt: 'Imagen',
  // Puedes cambiar esta URL por una imagen local tuya (ej: '/assets/placeholder.png')
  fallbackSrc: 'https://via.placeholder.com/600x400?text=No+Image', 
  ratio: 'auto',
  zoomable: false,
  objectFit: 'cover'
});

// --- Estados ---
const isLoading = ref(true);
const hasError = ref(false);
const isZoomed = ref(false);

// --- Watchers ---
// Si cambia la URL (src), reseteamos los estados de carga
watch(() => props.src, () => {
  isLoading.value = true;
  hasError.value = false;
});

// --- Métodos ---
const onLoad = () => {
  // Pequeño delay artificial opcional para evitar parpadeos en cargas muy rápidas (cache)
  // O simplemente:
  isLoading.value = false;
};

const onError = () => {
  isLoading.value = false;
  hasError.value = true;
};

const toggleZoom = () => {
  if (props.zoomable && !hasError.value && !isLoading.value) {
    isZoomed.value = !isZoomed.value;
  }
};

// --- Computed Styles ---
const wrapperStyle = computed(() => ({
  aspectRatio: props.ratio,
}));
</script>

<template>
  <figure 
    class="smart-image-wrapper" 
    :style="wrapperStyle"
    :class="{ 'is-zoomable': zoomable && !hasError && !isLoading }"
    @click="toggleZoom"
  >
    
    <div v-if="isLoading" class="skeleton-loader"></div>

    <img
      v-if="!hasError"
      :src="src"
      :alt="alt"
      class="main-image"
      :class="{ 
        'is-loading': isLoading, 
        'is-loaded': !isLoading,
        [objectFit]: true 
      }"
      loading="lazy"
      @load="onLoad"
      @error="onError"
    />

    <div v-else class="error-placeholder">
      <img :src="fallbackSrc" alt="Error loading image" class="fallback-img" />
      </div>

  </figure>

  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="isZoomed" 
        class="lightbox-overlay" 
        @click.self="toggleZoom"
      >
        <button class="close-btn" @click="toggleZoom">&times;</button>
        <img :src="src" :alt="alt" class="lightbox-image" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* --- CONTENEDOR --- */
.smart-image-wrapper {
  position: relative;
  width: 100%;
  /* Fondo gris claro por si acaso */
  background-color: #e5e7eb; 
  overflow: hidden;
  margin: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px; /* Opcional: bordes redondeados */
}

.is-zoomable {
  cursor: zoom-in;
}

/* --- IMAGEN REAL --- */
.main-image {
  width: 100%;
  height: 100%;
  display: block;
  opacity: 0;
  transition: opacity 0.4s ease-in-out;
}

.main-image.is-loaded {
  opacity: 1;
}

/* Clases de ajuste */
.cover { object-fit: cover; }
.contain { object-fit: contain; }
.fill { object-fit: fill; }

/* --- SKELETON ANIMATION --- */
.skeleton-loader {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  z-index: 1;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* --- ERROR STATE --- */
.error-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f3f4f6;
  padding: 1rem;
}

.fallback-img {
  max-width: 50%;
  opacity: 0.5;
}

/* --- LIGHTBOX (ZOOM) --- */
.lightbox-overlay {
  position: fixed;
  inset: 0; /* top, right, bottom, left: 0 */
  z-index: 99999;
  background-color: rgba(0, 0, 0, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(5px);
  cursor: zoom-out;
}

.lightbox-image {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
  border-radius: 4px;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  color: white;
  font-size: 3rem;
  line-height: 1;
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 1;
}

/* --- TRANSICIONES VUE --- */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>