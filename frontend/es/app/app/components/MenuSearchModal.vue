<template>
  <Transition name="modal-fade">
    <div class="search-modal" v-if="uiStore.isSearchOpen">
      
      <div class="menu-background">
        
        <div class="search-sticky-header">
          <div class="header-content">
            <div class="search-bar-container">
              <i class="fas fa-search search-icon"></i>
              <input 
                ref="searchInputRef"
                type="text" 
                v-model="searchQuery"
                class="search-input"
                placeholder="¿Qué se te antoja hoy?"
                @input="onSearchInput"
              />
              <button v-if="searchQuery" @click="clearSearch" class="search-clear-btn">
                ✕
              </button>
            </div>
            
            <button class="close-modal-btn" @click="closeModal">
              Cerrar
            </button>
          </div>
        </div>

        <div v-if="showLoader" class="loading-container">
          <div class="spinner"></div>
          <p class="loading-text">Cargando nuestro menú...</p>
        </div>

        <div v-else class="menu-content">
          
          <div v-if="filteredCategories.length === 0 && !menuPending" class="no-results">
            <p>No encontramos productos que coincidan con "{{ searchQuery }}" ☹️</p>
            <button @click="clearSearch" class="reset-btn">Ver todo el menú</button>
          </div>

          <section
            v-for="(cat, index) in filteredCategories"
            :key="cat.category_id"
            :ref="(el) => setCategoryRef(cat.category_id, el)"
            class="menu-category-section"
          >
            <header class="menu-category-section__header">
              <h2
                class="menu-category-section__title"
                :style="shouldUseWhiteText(index) ? 'color:white' : ''"
              >
                {{ formatLabel(cat.category_name) }}
              </h2>
              <p
                class="menu-category-section__count"
                :style="shouldUseWhiteText(index) ? 'color:white' : ''"
              >
                {{ cat.products?.length || 0 }} productos
              </p>
            </header>

            <div class="menu-category-section__grid">
              <MenuProductCard
                v-for="prod in cat.products"
                :key="prod.id"
                :product="prod"
                :category-id="cat.category_id"
                :image-base-url="URI"
                :set-product-ref="setProductRef"
                @click="onClickProduct(cat, prod)"
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import {
  ref,
  computed,
  nextTick,
  watch,
  onMounted,
  onBeforeUnmount
} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUIStore } from '~/stores/ui' 
import MenuProductCard from '~/components/MenuProductCard.vue'
import { URI } from '~/service/conection'
import { useFetch, useSitesStore, useMenuStore } from '#imports'

const route = useRoute()
const router = useRouter()
const sitesStore = useSitesStore()
const menuStore = useMenuStore()
const uiStore = useUIStore()
const searchInputRef = ref(null)

// === LÓGICA DE BÚSQUEDA Y MODAL ===
const searchQuery = ref('')

const closeModal = () => {
  uiStore.closeSearch()
  searchQuery.value = '' // Opcional: limpiar búsqueda al cerrar
}

const clearSearch = () => {
  searchQuery.value = ''
  // No cerramos el modal al limpiar el texto, solo limpiamos el input
  if (searchInputRef.value) searchInputRef.value.focus()
}

const onSearchInput = () => {
  // Lógica simple de input
}

// === LOCK SCROLL: Bloquear el scroll de la página de fondo ===
watch(
  () => uiStore.isSearchOpen,
  (isOpen) => {
    if (process.client) {
      if (isOpen) {
        document.body.style.overflow = 'hidden'
        // Auto focus al input cuando se abre
        nextTick(() => {
          if (searchInputRef.value) searchInputRef.value.focus()
        })
      } else {
        document.body.style.overflow = ''
      }
    }
  },
  { immediate: true }
)

// === CONFIGURACIÓN BASE ===
const CACHE_TTL = 30 * 60 * 1000
const isRefreshing = ref(false)
let clientRefreshIntervalId = null

const doClientRefresh = async (refreshFn) => {
  try {
    isRefreshing.value = true
    await refreshFn()
  } finally {
    isRefreshing.value = false
  }
}

const siteId = computed(() => (sitesStore?.location?.site?.site_id) || 1)

// === FETCH DATA ===
const {
  data: rawCategoriesData,
  refresh,
  pending: menuPending
} = useFetch(
  () => `${URI}/tiendas/${siteId.value}/products`,
  {
    key: () => `menu-data-${siteId.value}`,
    server: true,
    default: () => ({ categorias: [] })
  }
)

if (process.client) {
  const cachedWrapper = menuStore.getMenuBySite(siteId.value)
  if (cachedWrapper && cachedWrapper.data && cachedWrapper.timestamp) {
    const age = Date.now() - cachedWrapper.timestamp
    if (age < CACHE_TTL) {
      rawCategoriesData.value = cachedWrapper.data
    }
  }
}

const sourceData = computed(() => rawCategoriesData.value)

watch(
  rawCategoriesData,
  (val) => {
    if (!process.client) return
    if (val && Array.isArray(val.categorias) && val.categorias.length) {
      menuStore.setMenuForSite(siteId.value, {
        data: val,
        timestamp: Date.now()
      })
    }
  },
  { immediate: true }
)

// === NORMALIZACIÓN ===
const normalize = (str) =>
  String(str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()

const formatLabel = (str) => {
  const s = String(str || '').toLowerCase()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

// === PROCESAMIENTO DE CATEGORÍAS (BASE) ===
const baseCategories = computed(() => {
  const raw = sourceData.value
  if (!raw || !Array.isArray(raw.categorias)) return []

  return raw.categorias
    .filter(
      (cat) =>
        cat.visible &&
        Array.isArray(cat.products) &&
        cat.products.length > 0
    )
    .map((cat) => {
      const category_id = Number(cat.categoria_id)
      const category_name = cat.categoria_descripcion || cat.english_name || ''

      const products = (cat.products || []).map((p) => ({
        ...p,
        id: p.producto_id,
        product_name:
          p.productogeneral_descripcionweb ||
          p.productogeneral_descripcion ||
          p.english_name ||
          '',
        price: Number(p.productogeneral_precio ?? 0),
        image_url:
          p.productogeneral_urlimagen ||
          (p.lista_productobase &&
            p.lista_productobase[0] &&
            p.lista_productobase[0].producto_urlimagen) ||
          ''
      }))

      return {
        ...cat,
        category_id,
        category_name,
        products
      }
    })
})

// === FILTRADO EN VIVO ===
const filteredCategories = computed(() => {
  const query = normalize(searchQuery.value)
  if (!query) return baseCategories.value
  return baseCategories.value
    .map(cat => {
      const matchingProducts = cat.products.filter(p => {
        const name = normalize(p.product_name)
        const desc = normalize(p.productogeneral_descripcion || p.productogeneral_descripcionweb)
        const eng = normalize(p.english_name)
        return name.includes(query) || desc.includes(query) || eng.includes(query)
      })
      return { ...cat, products: matchingProducts }
    })
    .filter(cat => cat.products.length > 0)
})

const showLoader = computed(() => {
  return menuPending.value && baseCategories.value.length === 0
})

const shouldUseWhiteText = (index) => index === 0

const onClickProduct = (category, product) => {
  // Al hacer clic, quizás quieras cerrar el buscador antes de navegar
  uiStore.closeSearch()
  router.push(`/producto/${product.id}`)
}

// === REFS / OBSERVERS ===
const activeCategoryId = ref(null)
const categoryRefs = ref({})
const productRefs = ref({})
const productObserver = ref(null)
const productCategoryObserver = ref(null)

onMounted(async () => {
  if (!process.client) return

  productObserver.value = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        const el = entry.target
        if (!el) return
        if (entry.isIntersecting) {
          el.classList.remove('menu-product-card--hidden')
          obs.unobserve(el)
        }
      })
    },
    { root: document.querySelector('.search-modal'), rootMargin: '0px 0px 20% 0px', threshold: 0.01 }
  )

  await doClientRefresh(refresh)

  clientRefreshIntervalId = window.setInterval(() => {
    doClientRefresh(refresh)
  }, 10 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (productObserver.value) productObserver.value.disconnect()
  if (clientRefreshIntervalId && process.client) window.clearInterval(clientRefreshIntervalId)
  // Asegurarnos de desbloquear el scroll si el componente se desmonta
  if (process.client) document.body.style.overflow = ''
})

const setCategoryRef = (id, el) => {
  if (!el) { delete categoryRefs.value[id]; return }
  categoryRefs.value[id] = el
}

const setProductRef = (productId, categoryId, el) => {
  if (!el) {
    const prevEl = productRefs.value[productId]
    if (prevEl && productObserver.value) productObserver.value.unobserve(prevEl)
    delete productRefs.value[productId]
    return
  }
  productRefs.value[productId] = el
  el.classList.add('menu-product-card--hidden')
  el.dataset.productId = String(productId)
  if (productObserver.value) productObserver.value.observe(el)
}

</script>

<style scoped>
/* === MODAL CONTAINER === */
.search-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh; /* Ocupa toda la pantalla */
  z-index: 9999; /* Por encima de todo */
  overflow-y: auto; /* El scroll ocurre DENTRO del modal */
  overscroll-behavior: contain; /* Evita scroll en la página de fondo */
}

/* === TRANSICIONES === */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* === FONDO DINÁMICO === */
.menu-background {
  min-height: 100%; /* Asegura que cubra el scroll */
  background-image:
    linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0.75) 0, /* Un poco más oscuro para que resalte como modal */
      rgb(255, 255, 255) 50vh,
      #ffffff 50vh 
    ),
    url('https://backend.salchimonster.com/read-photo-product/Ym5HMDik');
  background-repeat: no-repeat;
  background-size: 100% auto;
  background-attachment: local; /* Importante: local para que scrollee con el modal */
}

/* === HEADER (Ahora dentro del modal) === */
.search-sticky-header {
  position: sticky;
  top: 0;
  z-index: 10000;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.header-content {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.search-bar-container {
  position: relative;
  flex: 1; /* Toma el espacio disponible */
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 15px;
  color: #9ca3af;
  font-size: 1.1rem;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 12px 12px 12px 45px;
  border-radius: 99px;
  border: 1px solid #e5e7eb;
  background-color: #f3f4f6;
  font-size: 1rem;
  outline: none;
  transition: all 0.2s ease;
  color: #333;
}

.search-input:focus {
  background-color: #fff;
  border-color: #fbbf24;
  box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.2);
}

.search-clear-btn {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0 5px;
}

/* === BOTÓN CERRAR MODAL === */
.close-modal-btn {
  background: transparent;
  border: 1px solid #e5e7eb;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.close-modal-btn:hover {
  background: #f3f4f6;
  color: #000;
}

/* === CONTENIDO === */
.menu-content {
  max-width: 1300px;
  margin: 0 auto 2.5rem;
  padding: 0 1rem 1rem;
}

.no-results {
  text-align: center;
  padding: 4rem 1rem;
  color: white;
  font-weight: 500;
  font-size: 1.1rem;
}

.reset-btn {
  margin-top: 1rem;
  padding: 8px 16px;
  background: white;
  color: #111;
  border: none;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
}

/* SECCIÓN CATEGORÍA */
.menu-category-section {
  padding-top: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
}
.menu-category-section:last-of-type {
  border-bottom: none;
}

.menu-category-section__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.menu-category-section__title {
  font-size: 2rem;
  font-weight: 700;
  margin: 1rem 0;
  transition: color 0.3s ease;
}

.menu-category-section__count {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
}

/* GRID PRODUCTOS */
.menu-category-section__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 0.9rem;
  padding-bottom: 5rem;
}

/* LOADING */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
}
.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #ffaa00;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}
.loading-text {
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

@keyframes spin { to { transform: rotate(360deg); } }

/* RESPONSIVE */
@media (max-width: 768px) {
  .menu-background {
    background-size: contain;
  }
  .menu-content {
    padding: 0.5rem 0.5rem 1.5rem;
  }
  .menu-category-section__title { font-size: 1.5rem; }
  .menu-category-section__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.55rem;
  }
  .close-modal-btn {
    padding: 8px 12px;
    font-size: 0.9rem;
  }
}
</style>