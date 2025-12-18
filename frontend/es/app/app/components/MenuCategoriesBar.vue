<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed } from 'vue'
import { useSitesStore } from '#imports' // 👈 Importamos el store

const props = defineProps({
  categories: {
    type: Array,
    default: () => []
  },
  activeCategoryId: {
    type: [Number, String, null], 
    default: null
  }
})

const emit = defineEmits(['select-category'])
const containerRef = ref(null)
const siteStore = useSitesStore() // 👈 Instancia del store

// ✅ 1. Lógica de estado (Copiada para consistencia)
const isOpen = computed(() => {
  const st = siteStore.status
  if (!st) return false
  if (typeof st === 'string') return st === 'open'
  return st.status === 'open'
})

// ✅ 2. Scroll Logic
const isPinned = ref(true)
const lastScrollY = ref(0)

const handleScroll = () => {
  if (typeof window === 'undefined') return
  const currentY = window.scrollY || window.pageYOffset || 0
  const delta = currentY - lastScrollY.value

  if (Math.abs(delta) < 5) {
    lastScrollY.value = currentY
    return
  }

  // Si bajamos > 80px, ocultamos el header principal, así que este sube a 0
  if (delta > 0 && currentY > 80) {
    isPinned.value = false
  } else {
    isPinned.value = true
  }
  lastScrollY.value = currentY
}

// ✅ 3. Calculamos la posición TOP dinámica
const categoriesBarTop = computed(() => {
  // Caso A: Usuario bajando scroll (Header principal oculto)
  if (!isPinned.value) return '0px'

  // Caso B: Usuario arriba o subiendo (Header principal visible)
  // Si está ABIERTO: dejamos espacio para el header (~5rem)
  // Si está CERRADO: dejamos espacio para header + cinta (~8.5rem)
  return isOpen.value ? '3.6rem' : '5.7rem'
})

const formatLabel = (str) => {
  const s = String(str || '').toLowerCase()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const onClickCategory = (category) => {
  emit('select-category', category)
}

const centerActiveCategoryPill = () => {
  const container = containerRef.value
  if (!container) return
  const activeId = props.activeCategoryId
  if (!activeId) return
  const activeEl = container.querySelector(`[data-cat-pill-id="${activeId}"]`)
  if (!activeEl) return

  const targetScrollLeft = activeEl.offsetLeft + activeEl.offsetWidth / 2 - container.clientWidth / 2
  container.scrollTo({ left: Math.max(0, targetScrollLeft), behavior: 'smooth' })
}

watch(() => props.activeCategoryId, () => {
  nextTick(() => { centerActiveCategoryPill() })
})

onMounted(() => {
  if (typeof window !== 'undefined') {
    lastScrollY.value = window.scrollY || 0
    window.addEventListener('scroll', handleScroll, { passive: true })
    centerActiveCategoryPill()
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('scroll', handleScroll)
  }
})
</script>

<template>
  <div 
    class="menu-categories-bar" 
    :style="{ top: categoriesBarTop }"
  >
    <div class="menu-categories-bar__scroll" ref="containerRef">
      <button
        v-for="cat in categories"
        :key="cat.category_id"
        class="menu-categories-bar__item"
        :class="{ 'menu-categories-bar__item--active': cat.category_id == activeCategoryId }"
        :data-cat-pill-id="cat.category_id"
        @click="onClickCategory(cat)"
      >
        <img 
          class="menu-categories-bar__img"
          :src="`https://img.restpe.com/${cat.products[0]?.productogeneral_urlimagen}`" 
          alt=""
        > 
        <span class="menu-categories-bar__text">{{ formatLabel(cat.category_name) }}</span>  
      </button>
    </div>
  </div>
</template>

<style scoped>
.menu-categories-bar {
  position: sticky;
  z-index: 99; /* Un poco menos que el TopBar (100) */
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  
  /* Transición suave sincronizada con el Layout/TopBar */
  transition: top 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.menu-categories-bar__scroll {
  margin: 0 auto;
  padding: 0.75rem 1rem;
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  scrollbar-width: none;
}
.menu-categories-bar__scroll::-webkit-scrollbar { display: none; }

.menu-categories-bar__item {
  padding: 0.4rem 0.8rem;
  display: flex;
  align-items: center;
  border-radius: 99px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.menu-categories-bar__text { padding-left: 0.5rem; }

.menu-categories-bar__img {
  height: 1.5rem;
  width: 1.5rem;
  border-radius: 50%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
}

.menu-categories-bar__item:hover {
  background: #fee2e2;
  border-color: #fecaca;
  color: #b91c1c;
  transform: translateY(-1px);
}

.menu-categories-bar__item--active {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
  /* En móvil, los espacios del topbar suelen ser iguales, 
     pero si tu TopBar cambia de altura en móvil, ajusta estos valores en el JS */
  .menu-categories-bar__scroll { padding: 0.75rem; gap: 0.6rem; }
  .menu-categories-bar__item { padding: 0.5rem 1rem; font-size: 1rem; }
  .menu-categories-bar__img { height: 1.8rem; width: 1.8rem; }
}
</style>