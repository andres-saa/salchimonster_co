<template>
  <div class="menu-page">
    <CarouselBanners v-if="!isLoggedIn" />

    <MenuCategoriesBar
      :categories="categories"
      :active-category-id="activeCategoryId"
      :is-refreshing="isRefreshing"
      @select-category="onClickCategory"
    />

    <div class="menu-background">
      <div v-if="showLoader" class="loading-container">
        <div class="spinner"></div>
        <p class="loading-text">Cargando nuestro menú...</p>
      </div>

      <div v-else class="menu-content">
        <section
          v-for="(cat, index) in categories"
          :key="cat.category_id"
          :ref="(el) => setCategoryRef(cat.category_id, el)"
          class="menu-category-section"
        >
          <header class="menu-category-section__header">
            <h2
              class="menu-category-section__title"
              :style="index === 0 ? 'color:white' : ''"
            >
              {{ formatLabel(cat.category_name) }}
            </h2>
            <p
              class="menu-category-section__count"
              :style="index === 0 ? 'color:white' : ''"
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
import CarouselBanners from '~/components/carouselBanners.vue'
import MenuCategoriesBar from '~/components/MenuCategoriesBar.vue'
import MenuProductCard from '~/components/MenuProductCard.vue'
import { URI } from '~/service/conection'
import { useHead, useFetch, useSitesStore, useMenuStore, useUserStore } from '#imports'
const route = useRoute()
const router = useRouter()
const sitesStore = useSitesStore()
const menuStore = useMenuStore()
const userStore = useUserStore() // <--- Inicialízalo aquí
/* ==========================
   CONFIGURACIÓN DE CACHÉ
   ========================== */
const CACHE_TTL = 30 * 60 * 1000
const isLoggedIn = computed(() => {
  return !!userStore.user?.token && !!userStore.user?.inserted_by
})
/* ==========================
   ESTADO PARA REFRESCO EN CLIENTE
   ========================== */
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

/* ==========================
   SITE ID
   ========================== */
const siteId = computed(
  () => (sitesStore?.location?.site?.site_id) || 1
)

/* ==========================
   FETCH & HIDRATACIÓN INTELIGENTE
   ========================== */
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
    const now = Date.now()
    const age = now - cachedWrapper.timestamp

    if (age < CACHE_TTL) {
      console.log(
        `[Menu] Usando caché fresca (Edad: ${Math.round(age / 1000)}s)`
      )
      rawCategoriesData.value = cachedWrapper.data
    } else {
      console.log('[Menu] Caché expirada. Usando datos de red/SSR.')
    }
  }
}

/* ==========================
   DATA FUENTE & PERSISTENCIA
   ========================== */
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

/* ==========================
   NORMALIZACIÓN / LABEL
   ========================== */
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

/* ==========================
   ADAPTACIÓN DE LA DATA
   ========================== */
const categories = computed(() => {
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
      const category_name =
        cat.categoria_descripcion || cat.english_name || ''

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

/* ==========================
   ESTADO DE CARGA (NUEVO)
   ========================== */
// Mostramos loader si está pendiente Y no tenemos categorías previas (evita parpadeo si hay caché)
const showLoader = computed(() => {
  return menuPending.value && categories.value.length === 0
})

/* ==========================
   NAVEGACIÓN DE PRODUCTOS
   ========================== */
const onClickProduct = (category, product) => {
  router.push(`/producto/${product.id}`)
}

/* ==========================
   REFS / OBSERVERS
   ========================== */
const activeCategoryId = ref(null)
const categoryRefs = ref({})
const productRefs = ref({})

const productObserver = ref(null)
const productCategoryObserver = ref(null)

const isProgrammaticScroll = ref(false)
let programmaticScrollTimer = null

onMounted(async () => {
  if (!process.client) return

  productObserver.value = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        const el = entry.target
        if (!el) return
        if (entry.isIntersecting) {
          el.classList.remove('menu-product-card--hidden')
          el.classList.add('menu-product-card--visible')
          obs.unobserve(el)
        }
      })
    },
    { rootMargin: '0px 0px -10% 0px', threshold: 0.1 }
  )

  productCategoryObserver.value = new IntersectionObserver(
    (entries) => {
      if (isProgrammaticScroll.value) return
      const visibles = []
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return
        const el = entry.target
        if (!el) return
        const catId = Number(el.dataset.categoryId || '')
        if (!catId) return
        visibles.push({ catId, top: entry.boundingClientRect.top })
      })

      if (!visibles.length) return
      visibles.sort((a, b) => a.top - b.top)
      const best = visibles[0]
      if (best.catId && best.catId !== activeCategoryId.value) {
        activeCategoryId.value = best.catId
      }
    },
    { rootMargin: '-120px 0px -60% 0px', threshold: 0.3 }
  )

  // Nota: Observamos en un watcher o nextTick cuando carguen las categorías, 
  // ya que al inicio showLoader puede ser true y no hay elementos DOM aún.

  await doClientRefresh(refresh)

  clientRefreshIntervalId = window.setInterval(() => {
    doClientRefresh(refresh)
  }, 10 * 60 * 1000)
})

// Watch para reconectar observers cuando el loader desaparece y hay contenido
watch(showLoader, (isLoading) => {
    if (!isLoading) {
        nextTick(() => {
             // Re-verificar refs si es necesario o simplemente dejar que el v-for lo maneje
             // La lógica de setProductRef se encarga de conectar el observer
        })
    }
})

onBeforeUnmount(() => {
  if (productObserver.value) productObserver.value.disconnect()
  if (productCategoryObserver.value) productCategoryObserver.value.disconnect()
  if (programmaticScrollTimer && process.client) {
    window.clearTimeout(programmaticScrollTimer)
  }
  if (clientRefreshIntervalId && process.client) {
    window.clearInterval(clientRefreshIntervalId)
  }
})

const setCategoryRef = (id, el) => {
  if (!el) {
    delete categoryRefs.value[id]
    return
  }
  categoryRefs.value[id] = el
}

const setProductRef = (productId, categoryId, el) => {
  if (!el) {
    const prevEl = productRefs.value[productId]
    if (prevEl) {
      if (productObserver.value) productObserver.value.unobserve(prevEl)
      if (productCategoryObserver.value) productCategoryObserver.value.unobserve(prevEl)
    }
    delete productRefs.value[productId]
    return
  }
  productRefs.value[productId] = el
  el.classList.add('menu-product-card--hidden')
  el.dataset.productId = String(productId)
  el.dataset.categoryId = String(categoryId)
  if (productObserver.value) productObserver.value.observe(el)
  if (productCategoryObserver.value) productCategoryObserver.value.observe(el)
}

/* ==========================
   SCROLL A CATEGORÍA
   ========================== */
const HEADER_OFFSET = 7 * 16

const scrollToCategoryId = (id) => {
  if (!process.client) return

  const el = categoryRefs.value[id]
  if (!el) return

  const y = el.getBoundingClientRect().top + window.scrollY - HEADER_OFFSET
  isProgrammaticScroll.value = true
  if (programmaticScrollTimer) window.clearTimeout(programmaticScrollTimer)

  window.scrollTo({ top: y, behavior: 'smooth' })

  programmaticScrollTimer = window.setTimeout(() => {
    isProgrammaticScroll.value = false
  }, 400)
}

/* ==========================
   URL & NAVEGACIÓN
   ========================== */
const onClickCategory = (category) => {
  activeCategoryId.value = category.category_id
  router.push({
    path: route.path,
    query: { category: category.category_name }
  })
  nextTick(() => {
    scrollToCategoryId(category.category_id)
  })
}

const scrollFromRoute = () => {
  if (!process.client) return

  const q = route.query.category
  if (!q || typeof q !== 'string') return
  const target = categories.value.find(
    (c) => normalize(c.category_name) === normalize(q)
  )
  if (!target) return
  activeCategoryId.value = target.category_id
  nextTick(() => {
    scrollToCategoryId(target.category_id)
  })
}

watch(
  () => route.query.category,
  () => {
    scrollFromRoute()
  },
  { immediate: true, flush: 'post' }
)

watch(
  categories,
  (list) => {
    if (!list.length) return
    if (route.query.category && typeof route.query.category === 'string') {
      scrollFromRoute()
      return
    }
    if (activeCategoryId.value == null) {
      activeCategoryId.value = list[0].category_id
    }
  },
  { immediate: true, flush: 'post' }
)

/* ==========================
   SEO / META
   ========================== */
const pageTitle = computed(() => {
  const base = 'Carta Salchimonster'
  const categoryQ = route.query.category
  if (categoryQ && typeof categoryQ === 'string') {
    return `${formatLabel(categoryQ)} | ${base}`
  }
  return base
})

useHead(() => ({
  title: pageTitle.value
}))
</script>


<style scoped>
.menu-page {
  min-height: 100vh;
  /* background: #f3f4f6; */
  color: #111827;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI',
    sans-serif;

}

/* HERO (si lo quieres usar) */
.menu-hero {
  position: relative;
  height: 220px;
  width: 100%;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.95)),
    url('https://images.pexels.com/photos/4109087/pexels-photo-4109087.jpeg');
  background-size: cover;
  background-position: center;
}

.menu-hero__overlay {
  position: absolute;
  inset: 0;
}

.menu-hero__content {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 1.5rem;
    
}

.menu-hero__title {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  margin: 0 0 0.5rem;
  text-transform: none;
}

.menu-hero__subtitle {
  margin: 0;
  opacity: 0.8;
  max-width: 480px;
  font-size: 0.95rem;
}

/* CONTENIDO */
.menu-content {
  max-width: 1300px;
  margin: 0rem auto 2.5rem;
  padding:   1rem;
}

/* SECCIÓN CATEGORÍA */
.menu-category-section {
  padding-top: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.menu-category-section:last-of-type {
  border-bottom: none;
  padding-bottom: 0;
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
  margin:1rem 0;
  text-transform: none;
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

/* RESPONSIVE ESCRITORIO */
@media (min-width: 1024px) {
  .menu-hero__title {
    font-size: 2.4rem;
  }
}

/* 📱 RESPONSIVE MÓVIL */
@media (max-width: 768px) {
  .menu-hero {
    height: 180px;
  }

  .menu-hero__title {
    font-size: 1.4rem;
  }

  .menu-hero__subtitle {
    font-size: 0.8rem;
  }

  .menu-content {
    padding: 0.5rem 0.5rem 1.5rem;
    margin-bottom: 1.5rem;
  }

  .menu-category-section {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
  }

  .menu-category-section__title {
    font-size: 1.5rem;
  }

  .menu-category-section__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.55rem;
  }

}

  
.menu-background {
  min-height: 100vh;
  /* Primero el degradado encima, luego la imagen */
  background-image:
    linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0.596) 0,
      rgb(255, 255, 255) 50vh, /* hasta 300px transparente */
      #ffffff 50vh 
    ),
    url('https://backend.salchimonster.com/read-photo-product/Ym5HMDik');
    background-repeat: no-repeat;
    background-size: 100%
    ;
   
}

</style>
