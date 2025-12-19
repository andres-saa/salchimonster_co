<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useSitesStore, useSidebarStore, useUserStore, useUIStore, texts } from '#imports'

const uistore = useUIStore()
const route = useRoute()
const router = useRouter()
const siteStore = useSitesStore()
const sidebarStore = useSidebarStore()
const user = useUserStore()

const handleSearch = () => {
  uistore.isSearchOpen = true
}

// --- LÓGICA DE ESTADO (Abierto/Cerrado) ---
const isOpen = computed(() => {
  const st = siteStore.status
  if (!st) return false
  if (typeof st === 'string') return st === 'open'
  return st.status === 'open'
})

// Hora de apertura para el mensaje de cerrado
const nextOpeningTime = computed(() => {
  return siteStore.status?.next_opening_time || 'pronto'
})

// Idiomas
const languages = [
  { name: 'ES', label: 'Español', flag: 'https://flagcdn.com/w20/co.png' },
  { name: 'EN', label: 'English', flag: 'https://flagcdn.com/w20/us.png' }
]

// Idioma por defecto
if (!user.lang || !user.lang.name) {
  user.lang = languages[0]
}

// Dropdown idioma
const isLangOpen = ref(false)

// --- refs para menús / "Más" ---
const menusContainerRef = ref(null)
const moreButtonRef = ref(null)

const visibleMenus = ref([])
const overflowMenus = ref([])
const isMoreOpen = ref(false)
const windowWidth = ref(0)

// CONFIG: cuántos menús según ancho
const menuVisibilityConfig = [ 
   { maxWidth: 900, visible: 2 },
  { maxWidth: 1024, visible: 3 },
  { maxWidth: 1070, visible: 4 },
  { maxWidth: 1280, visible: 5 },
  { maxWidth: Infinity, visible: 'all' }
]

// --- LÓGICA DE AUTENTICACIÓN Y NAVEGACIÓN EXTERNA ---

// Helper para saber si está logueado
const isLoggedIn = computed(() => {
  return !!user.user?.token && !!user.user?.inserted_by
})

const isIframe = computed(() => {
  return user.user.iframe 
})

// Acción: Nuevo Pedido (Redirige al 3001)
const goToNewOrder = () => {
  const token = user.user.token
  const inserted_by = user.user.inserted_by
  const iframe = user.user?.iframe
  window.location.href = `http://localhost:3001?token=${token}&inserted_by=${inserted_by}&iframe=${iframe}`
}

// Acción: Cerrar Sesión
const handleLogout = () => {
  user.user.token = null
  user.user.inserted_by = null
  window.location.href = 'http://localhost:3001'
}

// --- LÓGICA DE PERFIL DE USUARIO Y JWT ---
const isProfileOpen = ref(false)

// Función segura para decodificar JWT
const parseJwt = (token) => {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    
    // Decodificación compatible con caracteres especiales (utf-8)
    const jsonPayload = decodeURIComponent(
      window.atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (e) {
    console.error('Error decodificando token:', e)
    return null
  }
}

// Datos computados del usuario desde el token
const userInfo = computed(() => {
  if (!user.user?.token || typeof window === 'undefined') return null
  return parseJwt(user.user.token)
})

// URL de la foto con timestamp para evitar caché
const userPhotoUrl = computed(() => {
  if (!userInfo.value?.dni) return 'https://cdn.icon-icons.com/icons2/1378/PNG/512/avatardefault_92824.png'
  return `https://backend.salchimonster.com/read-product-image/600/employer-${userInfo.value.dni}?timestamp=${new Date().getTime()}`
})

const toggleProfile = () => {
  isProfileOpen.value = !isProfileOpen.value
}

// --- MENÚS DINÁMICOS ---
const menusAll = computed(() => {
  const langKey = (user.lang?.name || 'es').toLowerCase()
  const t = texts[langKey]?.menus || {}

  const menusPublicos = [
    { label: t.domicilios || 'Domicilios', to: '/' },
    { label: t.sedes || 'Sedes', to: `/sedes` },
    { label: t.carta || 'Carta', to: `/carta` },
    { label: t.rastrear || 'Rastrear', to: `/rastrear` },
    { label: t.ayuda || 'Ayuda', to: `/pqr` },
    { label: t.colaboraciones || 'Colaboraciones', to: `/colaboraciones` },
    { label: t.sonando || 'Sonando', to: `/sonando` }
  ]

  const menusLogueados = [
    { label: 'Menu', to: '/' }, 
    { label: t.rastrear || 'Rastrear', to: `/rastrear` },
  ]

  return isLoggedIn.value ? menusLogueados : menusPublicos
})

// Redes por defecto
const defaultSocialLinks = [
  { name: 'facebook', url: 'https://www.facebook.com/salchimonsteresp?locale=es_LA', icon: 'mdi:facebook' },
  { name: 'instagram', url: 'https://www.instagram.com/salchimonsteresp/', icon: 'mdi:instagram' },
  { name: 'whatsapp', url: 'https://wa.me/573005089846', icon: 'mdi:whatsapp' },
  { name: 'tiktok', url: 'https://www.tiktok.com/@salchimonsterespana', icon: 'fa7-brands:tiktok' }
]

const socialLinks = computed(() => {
  const raw = siteStore.status?.networks || siteStore.current?.networks || siteStore.site?.networks
  if (!raw) return defaultSocialLinks
  if (Array.isArray(raw)) return raw
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : defaultSocialLinks
  } catch (e) {
    return defaultSocialLinks
  }
})

const isActiveRoute = (path) => route.path === path

const toggleSidebar = (event) => {
  event.stopPropagation()
  sidebarStore.toggle()
}

const handleResize = () => {
  if (typeof window !== 'undefined') {
    windowWidth.value = window.innerWidth
  }
}

const getVisibleCountForWidth = (width, totalMenus) => {
  const rule = menuVisibilityConfig.find((rule) => width <= rule.maxWidth) || menuVisibilityConfig[menuVisibilityConfig.length - 1]
  if (rule.visible === 'all') return totalMenus
  return Math.min(rule.visible, totalMenus)
}

const recalcMenus = () => {
  const allMenus = menusAll.value
  if (!windowWidth.value) {
    visibleMenus.value = allMenus; overflowMenus.value = []; isMoreOpen.value = false; return
  }
  if (windowWidth.value <= 900) {
    visibleMenus.value = allMenus; overflowMenus.value = []; isMoreOpen.value = false; return
  }

  const total = allMenus.length
  const visibleCount = getVisibleCountForWidth(windowWidth.value, total)
  visibleMenus.value = allMenus.slice(0, visibleCount)
  overflowMenus.value = allMenus.slice(visibleCount)
  if (!overflowMenus.value.length) isMoreOpen.value = false
}

const hasOverflow = computed(() => overflowMenus.value.length > 0)

onMounted(() => {
  handleResize()
  if (typeof window !== 'undefined') window.addEventListener('resize', handleResize)
  siteStore.initStatusWatcher()
  nextTick().then(() => recalcMenus())
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') window.removeEventListener('resize', handleResize)
})

watch([menusAll, windowWidth], () => { nextTick().then(() => recalcMenus()) }, { immediate: true })
</script>

<template>
  <div class="app-topbar-wrapper">
    
    <div v-if="!isOpen" class="closed-ribbon-container">
      <div class="marquee-track">
        <div class="marquee-content">
          <span v-for="n in 4" :key="'A'+n">
            🚨 ESTAMOS CERRADOS, ABRIMOS A LAS {{ nextOpeningTime }} &nbsp;&nbsp; • &nbsp;&nbsp;
          </span>
        </div>
        <div class="marquee-content">
          <span v-for="n in 4" :key="'B'+n">
            🚨 ESTAMOS CERRADOS, ABRIMOS A LAS {{ nextOpeningTime }} &nbsp;&nbsp; • &nbsp;&nbsp;
          </span>
        </div>
      </div>
    </div>

    <header class="app-topbar-container">
      <div class="header-inner">
        
        <NuxtLink to="/" class="logo-link">
          <div class="logo-sesion">
            <button 
              v-if="isLoggedIn" 
              @click.prevent="goToNewOrder" 
              class="new"
              type="button"
            >
              Nuevo pedido
            </button>

            <img src="https://gestion.salchimonster.com/images/logo.png" alt="Logo" class="logo-img" />
            <div class="title-block">
              <div class="site-info">
                <Icon name="mdi:map-marker" class="marker-icon" />
                <span class="site-name">
                  {{ siteStore?.location?.site?.site_name || 'Salchimonster' }}
                </span>
                <div v-if="isOpen" class="live-dot-container" title="Estamos Abiertos">
                  <div class="live-dot"></div>
                </div>
              </div>
            </div>
          </div>
        </NuxtLink>

        <nav class="menus" ref="menusContainerRef">
          <NuxtLink 
            v-for="item in visibleMenus" 
            :key="item.to" 
            :to="item.to" 
            class="menu-item"
            :class="{ 'menu-item--active': isActiveRoute(item.to) }"
          >
            {{ item.label }}
          </NuxtLink>

          <div v-if="overflowMenus.length" class="more-wrapper">
            <button type="button" class="more-button" ref="moreButtonRef" @click="isMoreOpen = !isMoreOpen">
              Más <Icon name="mdi:chevron-down" class="more-chevron" />
            </button>
            
            <transition name="fade-slide">
              <ul v-if="isMoreOpen" class="dropdown-menu more-dropdown">
                <li v-for="item in overflowMenus" :key="item.to">
                  <NuxtLink 
                    :to="item.to" 
                    class="dropdown-item"
                    :class="{ 'menu-item--active': isActiveRoute(item.to) }"
                    @click="isMoreOpen = false"
                  >
                    {{ item.label }}
                  </NuxtLink>
                </li>
              </ul>
            </transition>
          </div>

          <div class="social-icons">
            <a 
              v-for="net in socialLinks" 
              :key="net.name" 
              :href="net.url" 
              class="social-link" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              <Icon :name="net.icon" class="social-icon" />
            </a>
          </div>
        </nav>

        <div class="header-actions">
          
          <button type="button" class="action-btn search-btn" @click="handleSearch" title="Buscar">
            <Icon name="mdi:magnify" class="action-icon" />
          </button>

          <div v-if="isLoggedIn && userInfo" class="user-profile-wrapper">
            <button class="profile-trigger" @click="toggleProfile">
              <img :src="userPhotoUrl" alt="User" class="profile-avatar" />
              <span class="profile-name">{{ userInfo.name }}</span>
            </button>

            <transition name="fade-slide">
              <div v-if="isProfileOpen" class="profile-card">
                <div class="card-header">
                  <img :src="userPhotoUrl" alt="Profile" class="card-avatar-large" />
                  <div class="card-info">
                    <h4 class="card-name">{{ userInfo.name }}</h4>
                    <span class="card-role">{{ userInfo.rol }}</span>
                  </div>
                </div>
                <hr class="card-divider" />
                <div class="card-details">
                  <div class="detail-row">
                    <Icon name="mdi:card-account-details-outline" class="detail-icon" />
                    <span><strong>DNI:</strong> {{ userInfo.dni }}</span>
                  </div>
                  <div class="detail-row">
                    <Icon name="mdi:store-marker-outline" class="detail-icon" />
                    <span><strong>Sede:</strong> {{ userInfo.site_name }}</span>
                  </div>
                </div>
              </div>
            </transition>
          </div>


 
          <button 
            v-if="isLoggedIn && !isIframe" 
            @click.prevent="handleLogout" 
            class="new" 
            style="background-color: #333; margin-left: 0.5rem;"
            type="button"
          >
            cerrar
          </button>
          
          <button 
            type="button" 
            class="icon-button burger-button"
            :class="{ 'burger-visible': !hasOverflow }" 
            @click="toggleSidebar"
          >
            <Icon name="mdi:menu" class="header-icon" />
          </button>
        </div>

      </div>
    </header>
  </div>
</template>

<style scoped>
/* --- VARIABLES --- */
:root {
  --nav-height: 65px;
  --nav-height-mobile: 72px;
}

/* --- WRAPPER GLOBAL --- */
.app-topbar-wrapper {
  position: relative;
  width: 100%;
  z-index: 100;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* --- CINTA CERRADO --- */
.closed-ribbon-container {
  width: 100%;
  background: repeating-linear-gradient(
    45deg,
    #c62828,
    #c62828 10px,
    #d32f2f 10px,
    #d32f2f 20px
  );
  color: white;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 0.5rem 0;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  position: relative;
  display: flex;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.marquee-track {
  display: flex;
  white-space: nowrap;
  animation: marquee 30s linear infinite;
  width: max-content;
}

.marquee-content {
  display: flex;
  align-items: center;
}

@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* --- HEADER CONTAINER --- */
.app-topbar-container {
  width: 100%;
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  transition: all 0.3s ease;
}

.header-inner {
  max-width: 1920;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1.5rem;
  height: var(--nav-height);
}

/* --- LOGO Y SITE INFO --- */
.logo-link {
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
  transition: opacity 0.2s;
}
.logo-link:hover { opacity: 0.9; }

.logo-sesion {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-img {
  width: 42px;
  height: 42px;
  object-fit: cover;
}

.site-info {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--primary-color, #d32f2f);
}

.marker-icon {
  font-size: 1.2rem;
}

.site-name {
  font-weight: 800;
  font-size: 1rem;
  text-transform: capitalize;
  color: #333;
  line-height: 1.1;
}

/* Punto Verde */
.live-dot-container {
  display: flex;
  align-items: center;
  margin-left: 0.4rem;
}
.live-dot {
  width: 8px;
  height: 8px;
  background-color: #00e676;
  border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7);
  animation: blink-dot 2s infinite;
}
@keyframes blink-dot {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(0, 230, 118, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
}

/* --- MENÚ DE ESCRITORIO --- */
.menus {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
}

.menu-item {
  position: relative;
  color: #444;
  font-size: 0.95rem;
  font-weight: 600;
  text-decoration: none;
  padding: 0.5rem 0;
  transition: color 0.2s;
}

.menu-item:hover { color: var(--primary-color, #d32f2f); }

.menu-item--active {
  color: var(--primary-color, #d32f2f);
}
.menu-item--active::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  background-color: var(--primary-color, #d32f2f);
  border-radius: 2px;
  animation: slide-up 0.3s ease;
}

@keyframes slide-up {
  from { width: 0; opacity: 0; margin-left: 50%; }
  to { width: 100%; opacity: 1; margin-left: 0; }
}

/* --- BOTÓN 'MÁS' --- */
.more-wrapper { position: relative; }
.more-button {
  background: transparent;
  border: 1px solid #e0e0e0;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.more-button:hover { background: #f9f9f9; border-color: #ccc; }

/* --- DROPDOWNS --- */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  padding: 0.5rem;
  min-width: 160px;
  list-style: none;
  z-index: 200;
  border: 1px solid #f0f0f0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #333;
  text-decoration: none;
  transition: background 0.2s;
}
.dropdown-item:hover { background-color: #f5f5f5; }

/* --- REDES SOCIALES --- */
.social-icons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 1rem;
}
.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #555;
  transition: all 0.2s;
}
.social-link:hover {
  background-color: #f0f0f0;
  color: var(--primary-color, #d32f2f);
  transform: translateY(-2px);
}
.social-icon { font-size: 1.2rem; }

/* --- ACCIONES DERECHA --- */
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

/* --- PERFIL DE USUARIO (NUEVOS ESTILOS) --- */
.user-profile-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.profile-trigger {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: transparent;
  border: 1px solid transparent;
  padding: 0.3rem 0.6rem 0.3rem 0.3rem;
  border-radius: 2rem;
  cursor: pointer;
  transition: all 0.2s;
}

.profile-trigger:hover {
  background-color: rgba(0,0,0,0.05);
  border-color: #eee;
}

.profile-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #fff;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.profile-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #444;
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* OVERLAY CARD */
.profile-card {
  position: absolute;
  top: calc(100% + 14px);
  right: -20px;
  width: 290px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  padding: 1.5rem;
  z-index: 300;
  border: 1px solid #f0f0f0;
}

/* Flechita del overlay */
.profile-card::before {
  content: '';
  position: absolute;
  top: -6px;
  right: 35px;
  width: 12px;
  height: 12px;
  background: white;
  transform: rotate(45deg);
  border-top: 1px solid #f0f0f0;
  border-left: 1px solid #f0f0f0;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.card-avatar-large {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid var(--primary-color, #d32f2f);
  padding: 3px;
  background: white;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  align-items: center;
}

.card-name {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: #333;
}

.card-role {
  font-size: 0.75rem;
  color: white;
  background-color: var(--primary-color, #d32f2f);
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-divider {
  border: 0;
  border-top: 1px solid #eee;
  margin: 1rem 0;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.95rem;
  color: #555;
}

.detail-icon {
  font-size: 1.3rem;
  color: #888;
}

/* Botón Hamburguesa */
.burger-button {
  display: none; 
  background: transparent;
  border: none;
  cursor: pointer;
  color: #333;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background 0.2s;
}
.burger-button:hover { background-color: rgba(0,0,0,0.05); }
.header-icon { font-size: 1.8rem; }

/* Transiciones Vue */
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.2s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* --- RESPONSIVE --- */
@media (min-width: 901px) {
  .burger-visible { display: none; }
}

@media (max-width: 900px) {
  .menus { display: none; }
  .burger-button { display: inline-flex; justify-content: center; align-items: center; }
  .header-inner { padding: 0.5rem 1rem; height: var(--nav-height-mobile); }
  .logo-img { width: 48px; height: 48px; }
  .site-name { font-size: 1.1rem; }
  .marker-icon { font-size: 1.3rem; }
  .header-actions { gap: 0.5rem; }
  .header-icon { font-size: 2rem; color: var(--primary-color, #d32f2f); }
  
  /* Ajustes Profile Móvil */
  .profile-name { display: none; } /* Ocultar nombre para ahorrar espacio */
  .profile-trigger { padding: 0; }
  .profile-card { right: -50px; width: 260px; }
  .profile-card::before { right: 65px; }
}

@media (max-width: 400px) {
  .site-name { font-size: 0.95rem; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}

/* --- BOTONES DE ACCIÓN --- */
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  color: #555;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-right: 0.2rem;
}

.action-btn:hover {
  background-color: rgba(0, 0, 0, 0.04);
  color: var(--primary-color, #d32f2f);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.action-btn:active {
  transform: scale(0.95);
  background-color: rgba(0, 0, 0, 0.08);
}

.action-icon { font-size: 1.4rem; }

@media (max-width: 900px) {
  .action-btn { width: 44px; height: 44px; border: 1px solid #f0f0f0; }
  .action-icon { font-size: 1.5rem; }
  .search-btn { margin-right: 0.5rem; }
}

.new {
  border: none;
  border-radius: 0.3rem;
  padding: 0.6rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  cursor: pointer;
  background-color: var(--primary-color, #b91c1c);
  color: #ffffff;
}
</style>