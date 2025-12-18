<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useSidebarStore, useRoute } from '#imports'
import { texts } from '#imports'
import { useUserStore } from '#imports'

const route = useRoute()
const store = useSidebarStore()
const user = useUserStore()

// 🔹 Agregué iconos a tu menú para que se vea más moderno
const menus = computed(() => {
  const langKey = (user.lang?.name || 'es').toLowerCase()
  const t = texts[langKey]?.menus || {}

  return [
    { label: t.domicilios || 'Domicilios', to: '/', icon: 'mdi:home-variant' },
    { label: t.sedes || 'Sedes', to: `/sedes`, icon: 'mdi:store-marker' },
    { label: t.carta || 'Carta', to: `/carta`, icon: 'mdi:food-fork-drink' },
    { label: t.rastrear || 'Rastrear', to: `/rastrear`, icon: 'mdi:map-clock' },
    { label: t.ayuda || 'Ayuda', to: `/pqr`, icon: 'mdi:lifebuoy' },
    { label: t.colaboraciones || 'Colaboraciones', to: `/colaboraciones`, icon: 'mdi:handshake' },
    { label: t.sonando || 'Sonando', to: `/sonando`, icon: 'mdi:music-circle' }
  ]
})

// 🔹 Lista de publicaciones
const posts = ref([
  { type: 'instagram', to: 'https://www.instagram.com/p/DMVpYaJx0aL/', image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRbUpauKUZtgu5hNAaZi1I6wMJlbb8wX08K8KxeN2lZYiDEmICL0dkKUfN7GWop4jInRro&usqp=CAU' },
  { type: 'facebook', to: 'https://www.facebook.com/facebook/posts/10153231379946729', image: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSp4y5LQHclGpdypvXlLeKbrvA2jq6Ao1qK_w&s' },
  { type: 'youtube', to: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', image: 'https://i.ytimg.com/vi/Y5T5EHBLH1c/oardefault.jpg?sqp=-oaymwEYCJUDENAFSFqQAgHyq4qpAwcIARUAAIhC&rs=AOn4CLB2KZPEiel96qlJ6RpqA0ULUhkgnw' },
  { type: 'tiktok', to: 'https://www.tiktok.com/@salchimonster/video/1234567890', image: 'https://i.ytimg.com/vi/Y5T5EHBLH1c/oardefault.jpg?sqp=-oaymwEYCJUDENAFSFqQAgHyq4qpAwcIARUAAIhC&rs=AOn4CLB2KZPEiel96qlJ6RpqA0ULUhkgnw' }
])

const networkLabel = (type) => {
  const map = { instagram: 'Instagram', facebook: 'Facebook', youtube: 'YouTube', tiktok: 'TikTok' }
  return map[type] || 'Post'
}

const closeSidebar = () => {
  store.side_bar_visible = false
}

/* referencia al contenedor que scrollea */
const containerRef = ref(null)

/* LÓGICA DE SCROLL (Mantenemos tu lógica original de pin) */
const isPinned = ref(true)
const isAtTop = ref(true)
const lastScrollY = ref(0)
const lastToggleY = ref(0)
const MIN_SCROLL_DELTA = 5
const TOGGLE_DISTANCE = 60

const handleScroll = () => {
  const el = containerRef.value
  if (!el) return
  const currentY = el.scrollTop || 0
  const delta = currentY - lastScrollY.value
  isAtTop.value = currentY < 10

  if (Math.abs(delta) < MIN_SCROLL_DELTA) { lastScrollY.value = currentY; return }

  if (isPinned.value) {
    const scrolledDownSinceToggle = currentY - lastToggleY.value
    if (delta > 0 && currentY > 80 && scrolledDownSinceToggle > TOGGLE_DISTANCE) {
      isPinned.value = false; lastToggleY.value = currentY
    }
  } else {
    const scrolledUpSinceToggle = lastToggleY.value - currentY
    if ((delta < 0 && scrolledUpSinceToggle > TOGGLE_DISTANCE) || currentY < 10) {
      isPinned.value = true; lastToggleY.value = currentY
    }
  }
  lastScrollY.value = currentY
}
/* ✅ detectar si estamos en /carta (o subrutas) */
const isCartaRoute = computed(() => {
  const path = route.path || ''
  const keywords = ['/carta', '/cart', '/sedes', '/franquicias', '/colaboraciones', '/sonando', '/producto', '/pay', '/gracias']
  return keywords.some(keyword => path.includes(keyword))
})


watch(isCartaRoute, (val) => {
  if (val) store.side_bar_visible = false
}, { immediate: true })

onMounted(() => {
  const el = containerRef.value
  if (!el) return
  const y = el.scrollTop || 0
  lastScrollY.value = y; lastToggleY.value = y
  el.addEventListener('scroll', handleScroll, { passive: true })
})

onBeforeUnmount(() => {
  const el = containerRef.value
  if (!el) return
  el.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div>
    <div
      v-if="store.side_bar_visible"
      class="sidebar-backdrop"
      @click="closeSidebar"
    ></div>

    <aside
      ref="containerRef"
      class="container"
      :class="{
        'container--mobile-open': store.side_bar_visible,
        'container--drawer-desktop': isCartaRoute
      }"
    >
      <div class="mobile-header" v-if="store.side_bar_visible">
        <h3 class="mobile-header__title">Menú</h3>
        <button class="close-btn" @click="closeSidebar">
          <Icon name="mdi:close" />
        </button>
      </div>

      <nav class="mobile-menu">
        <NuxtLink
          v-for="item in menus"
          :key="item.to"
          :to="item.to"
          class="nav-button"
          @click="closeSidebar"
        >
          <div class="nav-button__icon-box">
            <Icon :name="item.icon" class="nav-button__icon" />
          </div>
          <span class="nav-button__text">{{ item.label }}</span>
          <Icon name="mdi:chevron-right" class="nav-button__arrow" />
        </NuxtLink>
      </nav>

      <div class="sidebar-divider" v-if="store.side_bar_visible">
        <span>Nuestras Redes</span>
      </div>

      <div class="posts-wrapper">
        <a
          v-for="(post, index) in posts"
          :key="post.to || index"
          class="post-item"
          :href="post.to"
          target="_blank"
          rel="noopener noreferrer"
        >
          <div class="post-card">
            <img
              :src="post.image"
              :alt="networkLabel(post.type)"
              class="post-image"
              loading="lazy"
            />
            
            <div class="post-gradient"></div>

            <div class="post-overlay" :class="`post-overlay--${post.type}`">
              <span class="cta-button">Ver en {{ networkLabel(post.type) }}</span>
            </div>

            <div class="post-badge" :class="`post-badge--${post.type}`">
              <Icon v-if="post.type === 'instagram'" name="mdi:instagram" />
              <Icon v-else-if="post.type === 'facebook'" name="mdi:facebook" />
              <Icon v-else-if="post.type === 'youtube'" name="mdi:youtube" />
              <Icon v-else-if="post.type === 'tiktok'" name="fa7-brands:tiktok" />
            </div>
          </div>
        </a>
      </div>
      
      <div style="height: 3rem;"></div>
    </aside>
  </div>
</template>

<style scoped>
/* =========================================
   1. CONTENEDOR PRINCIPAL
   ========================================= */
.container {
  padding-bottom: 1rem;
  background-color: #f8f9fa; /* Fondo gris muy suave, más moderno que blanco puro */
  width: 100%;
  height: 100vh;
  min-height: 100vh;
  overflow-y: auto;
  box-sizing: border-box;
  margin: 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.container::-webkit-scrollbar { display: none; }

/* =========================================
   2. MENÚ MÓVIL (Botones Grandes y Bonitos)
   ========================================= */
.mobile-menu {
  display: none; /* Por defecto oculto en desktop si no es drawer */
  flex-direction: column;
  gap: 0.8rem;
  padding: 1rem 1.2rem;
}

.mobile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 1.2rem 0.5rem;
  margin-bottom: 0.5rem;
}

.mobile-header__title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: #333;
}

.close-btn {
  background: #eee;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  cursor: pointer;
  color: #555;
  transition: all 0.2s;
}
.close-btn:active { transform: scale(0.9); background: #ddd; }

/* Botón de Navegación */
.nav-button {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 1rem;
  background-color: #ffffff;
  color: #444;
  text-decoration: none;
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid transparent;
}

.nav-button:active {
  transform: scale(0.98);
}

.nav-button__icon-box {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.8rem;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 1.4rem;
  transition: all 0.3s ease;
}

.nav-button__text {
  flex: 1;
  font-size: 1rem;
  font-weight: 600;
}

.nav-button__arrow {
  color: #ccc;
  font-size: 1.2rem;
}

/* Estado Activo del Botón */
.nav-button.router-link-active {
  background-color: #ffffff;
  border-color: var(--primary-color);
  box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}

.nav-button.router-link-active .nav-button__icon-box {
  background-color: var(--primary-color);
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.nav-button.router-link-active .nav-button__text {
  color: var(--primary-color);
  font-weight: 700;
}

.nav-button.router-link-active .nav-button__arrow {
  color: var(--primary-color);
}

.sidebar-divider {
  padding: 1rem 1.2rem 0.5rem;
  color: #999;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* =========================================
   3. POSTS SOCIALES (Estilo Tarjeta)
   ========================================= */
.posts-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  padding: 1.2rem;
}

.post-item {
  text-decoration: none;
  display: block;
}

.post-card {
  position: relative;
  border-radius: .5rem;
  overflow: hidden;
  aspect-ratio: 4/5; /* Formato vertical moderno */
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  transform: translateZ(0); /* Fix para safari border-radius */
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.post-item:hover .post-card {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0,0,0,0.15);
}

.post-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.post-item:hover .post-image {
  transform: scale(1.05);
}

.post-gradient {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 40%;
  background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
  pointer-events: none;
}

/* Overlay Colorido */
.post-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.3);
  opacity: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.3s ease;
  backdrop-filter: blur(3px);
}

.post-item:hover .post-overlay { opacity: 1; }

.cta-button {
  background: white;
  color: black;
  padding: 0.6rem 1.2rem;
  border-radius: 2rem;
  font-size: 0.85rem;
  font-weight: 700;
  transform: translateY(20px);
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.post-item:hover .cta-button { transform: translateY(0); }

/* Badges */
.post-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: white;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
  z-index: 5;
}

.post-badge--instagram { background: radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%, #d6249f 60%, #285AEB 90%); }
.post-badge--facebook { background: #1877f2; }
.post-badge--youtube { background: #ff0000; }
.post-badge--tiktok { background: #000000; border: 1px solid rgba(255,255,255,0.2); }

/* =========================================
   4. LOGICA RESPONSIVE / DRAWER
   ========================================= */

.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 9990;
  backdrop-filter: blur(4px); /* Blur moderno en el fondo */
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* MÓVILES */
@media (max-width: 900px) {
  .container {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 85%;
    max-width: 380px;
    background: #f8f9fa;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 9999;
    box-shadow: 5px 0 25px rgba(0,0,0,0.2);
  }

  .container.container--mobile-open { transform: translateX(0); }
  .mobile-menu { display: flex; }
  .sidebar-backdrop { display: block; }
}

/* DESKTOP (Drawer Mode para /carta) */
.container--drawer-desktop {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  width: 320px;
  background: white;
  transform: translateX(-100%);
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 9999;
  box-shadow: 5px 0 25px rgba(0,0,0,0.15);
}
.container--drawer-desktop.container--mobile-open { transform: translateX(0); }

/* En modo desktop normal (no drawer), ocultamos el menu móvil */
@media (min-width: 900px) {
  .container:not(.container--drawer-desktop) .mobile-menu { display: none; }
}
</style>