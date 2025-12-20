<template>
  <div class="app-layout">

    <SiteDialog></SiteDialog>
    <header
      class="app-layout__topbar"
      :style="{ top: topBarPosition }"
    >
     <TopBar v-if="!['gracias', 'pagar'].some(word => route.path.includes(word))" />
    </header>

    <div
      class="app-layout__shell"
      :class="{ 'app-layout__shell--full': isCartaRoute }"
    >
      <div style="position: fixed; left: 0; top: 0; z-index: -1;">
        <div style="width: 100vw; height: 100vh;"></div>
      </div>

      <aside
        class="app-layout__sidebar"
        :style="{ top: sidebarTopPosition }"
      >
        <Sidebar />
      </aside>

      <main
        class="app-layout__content"
        :class="{ 'app-layout__content--full': isCartaRoute }"
      >
        <slot  />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useSitesStore } from '#imports'

const route = useRoute()
const siteStore = useSitesStore() // 👈 Necesario para saber si hay cinta

/* 👇 LÓGICA DE ESTADO (Copiada para consistencia con TopBar) */
const isOpen = computed(() => {
  const st = siteStore.status
  if (!st) return false // Asumimos cerrado si no carga, o true, según prefieras
  if (typeof st === 'string') return st === 'open'
  return st.status === 'open'
})

/* 👇 LÓGICA DE SCROLL: OCULTAR AL BAJAR, MOSTRAR AL SUBIR */
const isPinned = ref(true)        // true = visible, false = oculto
const lastScrollY = ref(0)

const handleScroll = () => {
  if (typeof window === 'undefined') return

  const currentY = window.scrollY || window.pageYOffset || 0
  const delta = currentY - lastScrollY.value

  // evitar ruido de scroll muy pequeño
  if (Math.abs(delta) < 5) {
    lastScrollY.value = currentY
    return
  }

  // Lógica: Si bajamos más de 80px, ocultamos. Si subimos, mostramos.
  if (delta > 0 && currentY > 80) {
    isPinned.value = false
  } else {
    isPinned.value = true
  }

  lastScrollY.value = currentY
}

/* ✅ CÁLCULOS DINÁMICOS DE POSICIÓN CSS */

// 1. Posición del Header (Topbar)
const topBarPosition = computed(() => {
  if (isPinned.value) return '0' // Siempre visible en 0 si está "pinned"
  
  // Si no está pinned (scrolleando abajo), ocultamos:
  // Si está ABIERTO: ocultamos -5rem (tamaño aprox header normal)
  // Si está CERRADO: ocultamos -8rem (tamaño header + cinta roja)
  return isOpen.value ? '-5rem' : '-6rem'
})

// 2. Posición del Sidebar
const sidebarTopPosition = computed(() => {
  if (!isPinned.value) return '0' // Si el header se fue, el sidebar sube al techo

  // Si el header está visible, el sidebar debe bajar:
  // Si está ABIERTO: baja ~4.5rem
  // Si está CERRADO: baja ~7.5rem (para dejar ver la cinta)
  return isOpen.value ? '4.5rem' : '5.5rem'
})

/* ✅ detectar si estamos en /carta (o subrutas) */
const isCartaRoute = computed(() => {
  const path = route.path || ''
  const keywords = ['/carta', '/cart', '/sedes', '/franquicias', '/colaboraciones', '/sonando', '/producto', '/pay', '/gracias']
  return keywords.some(keyword => path.includes(keyword))
})

onMounted(() => {
  if (typeof window === 'undefined') return
  lastScrollY.value = window.scrollY || 0
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onBeforeUnmount(() => {
  if (typeof window === 'undefined') return
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
}

/* TOPBAR FULL-WIDTH */
.app-layout__topbar {
  flex: 0 0 auto;
  position: sticky;
  z-index: 1000;
  background: #ffffff71;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  /* Transición suave para el efecto de esconderse */
  transition: top 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* SHELL por defecto */
.app-layout__shell {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
}

@media (min-width: 2049px) {
  .app-layout__shell {
    max-width: 1600px;
    margin: 0 auto;
  }
  .app-layout__shell.app-layout__shell--full {
    max-width: none;
    margin: 0;
  }
}

/* === SIDEBAR === */
.app-layout__sidebar {
  width: 260px;
  color: #fff;
  overflow-y: auto;
  max-height: 100vh;
  position: fixed;
  z-index: 9999; /* Un poco menos que el topbar */
  scrollbar-width: none;
  -ms-overflow-style: none;
  /* Transición suave sincronizada con el header */
  transition: top 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.app-layout__sidebar::-webkit-scrollbar {
  display: none;
}

/* === CONTENIDO === */
.app-layout__content {
  width: 100%;
  padding: 0;
  padding-left: 260px; 
}

.app-layout__content--full {
  padding-left: 0;
}

/* === TRANSICIÓN NUXT (page) === */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* === RESPONSIVE === */
@media (max-width: 900px) {
  .app-layout {
    max-height: none;
  }

  .app-layout__shell {
    flex-direction: column;
    max-width: 100%;
    position: relative;
  }

  .app-layout__content,
  .app-layout__content--full {
    padding: 0;
    overflow-y: visible;
  }
  
  /* En móvil el sidebar suele comportarse diferente (overlay), 
     así que aquí reseteamos el top si es necesario */
}
</style>