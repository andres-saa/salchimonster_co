<script setup>
import { ref, computed, nextTick, watch } from 'vue'

const route = useRoute()
const router = useRouter()

// 📡 Traer data real del backend
const { data: rawCategoriesData } = await useFetch(
  'https://tezos-back.arhook.com/categories/31/5'
)

// Normalizar texto para buscar por query (?category=...)
const normalize = (str) =>
  String(str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // quita tildes
    .trim()

// "todo minúscula con la primera letra mayúscula"
const formatLabel = (str) => {
  const s = String(str || '').toLowerCase()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const categories = computed(() => rawCategoriesData.value || [])

// ID de categoría activa (para resaltar botón)
const activeCategoryId = ref(null)

// Refs de cada sección de categoría para hacer scroll
const categoryRefs = ref({}) // { [category_id]: HTMLElement }

// Asignar ref desde el template
const setCategoryRef = (id, el) => {
  if (!el) return
  categoryRefs.value[id] = el
}

// Scroll suave a una categoría por id
const scrollToCategoryId = (id) => {
  const el = categoryRefs.value[id]
  if (!el) return
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  })
}

// Cuando hago click en una categoría del top
const onClickCategory = (category) => {
  activeCategoryId.value = category.category_id

  // Actualiza la URL: /menu?category=PIZZA%20ESTOFADA
  router.push({
    path: route.path,
    query: {
      ...route.query,
      category: category.category_name
    }
  })

  // Hace scroll después de que el DOM se actualice
  nextTick(() => {
    scrollToCategoryId(category.category_id)
  })
}

// Lee la query ?category=... y hace scroll a la correspondiente
const scrollFromRoute = () => {
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

// Si cambia la query category, volvemos a hacer scroll
watch(
  () => route.query.category,
  () => {
    scrollFromRoute()
  },
  { immediate: true }
)

// Marcar la primera categoría como activa por defecto si no hay query
watch(
  categories,
  (list) => {
    if (!route.query.category && list.length && activeCategoryId.value == null) {
      activeCategoryId.value = list[0].category_id
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="menu-page">
    <!-- HERO DE FONDO -->
    <div class="menu-hero">
      <div class="menu-hero__overlay" />
      <div class="menu-hero__content">
        <h1 class="menu-hero__title">
          carta tezo's pizza
        </h1>
        <p class="menu-hero__subtitle">
          Elige tu categoría y recorre nuestras pizzas, combos y acompañantes.
        </p>
      </div>
    </div>

    <!-- BARRA DE CATEGORÍAS -->
    <div class="menu-categories-bar">
      <div class="menu-categories-bar__scroll">
        <button
          v-for="cat in categories"
          :key="cat.category_id"
          class="menu-categories-bar__item"
          :class="{ 'menu-categories-bar__item--active': cat.category_id === activeCategoryId }"
          @click="onClickCategory(cat)"
        >
          {{ formatLabel(cat.category_name) }}
        </button>
      </div>
    </div>

    <!-- CONTENIDO: LISTA DE CATEGORÍAS + PRODUCTOS -->
    <div class="menu-content">
      <section
        v-for="cat in categories"
        :key="cat.category_id"
        :ref="(el) => setCategoryRef(cat.category_id, el)"
        class="menu-category-section"
      >
        <header class="menu-category-section__header">
          <h2 class="menu-category-section__title">
            {{ formatLabel(cat.category_name) }}
          </h2>
          <p class="menu-category-section__count">
            {{ cat.products?.length || 0 }} productos
          </p>
        </header>

        <div class="menu-category-section__grid">
          <article
            v-for="prod in cat.products"
            :key="prod.id"
            class="menu-product-card"
          >
            <div class="menu-product-card__image-wrapper">
              <img
                class="menu-product-card__image"
                :src="`https://tezos-back.arhook.com/read-photo-product/${prod.img_identifier}/600`"
                :alt="formatLabel(prod.product_name)"
                loading="lazy"
              />
            </div>
            <div class="menu-product-card__body">
              <h3 class="menu-product-card__name">
                {{ formatLabel(prod.product_name) }}
              </h3>
              <p class="menu-product-card__desc">
                {{
                  prod.product_description
                    ? formatLabel(prod.product_description)
                    : 'Sin descripción'
                }}
              </p>
              <div class="menu-product-card__footer">
                <span class="menu-product-card__price">
                  ${{ prod.price.toLocaleString('es-CO') }}
                </span>

                <span
                  v-if="prod.is_combo"
                  class="menu-product-card__tag menu-product-card__tag--combo"
                >
                  Combo
                </span>
                <span
                  v-else-if="prod.max_flavor > 1"
                  class="menu-product-card__tag menu-product-card__tag--flavors"
                >
                  Hasta {{ prod.max_flavor }} sabores
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.menu-page {
  min-height: 100vh;
  background: #f3f4f6;
  color: #111827;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* HERO */
.menu-hero {
  position: relative;
  height: 220px;
  width: 100%;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.7), rgba(249, 250, 251, 0.95)),
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

/* BARRA CATEGORÍAS (CLARA) */
.menu-categories-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.menu-categories-bar__scroll {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.5rem 1rem;
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  scrollbar-width: none;
}

.menu-categories-bar__scroll::-webkit-scrollbar {
  display: none;
}

.menu-categories-bar__item {
  flex: 0 0 auto;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f3f4f6;
  color: #374151;
  font-size: 0.8rem;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    transform 0.1s ease,
    color 0.2s ease;
  white-space: nowrap;
}

.menu-categories-bar__item:hover {
  background: #fee2e2;
  border-color: #fecaca;
  color: #b91c1c;
  transform: translateY(-1px);
}

.menu-categories-bar__item--active {
  background:var(--primary-color);
  border-color: transparent;
  color: #ffffff;
}

/* CONTENIDO */
.menu-content {
  max-width: 1200px;
  margin: 1rem auto 2.5rem;
  padding: 0 1rem 1rem;
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
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
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
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 0.9rem;
}

/* CARD PRODUCTO (TEMA CLARO) */
.menu-product-card {
  background: #ffffff;
  border-radius: 1rem;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 190px;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    border-color 0.12s ease;
}

.menu-product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 35px rgba(15, 23, 42, 0.15);
  border-color: #fecaca;
}

.menu-product-card__image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1; /* 👈 1:1 */
  overflow: hidden;
  background: #f3f4f6;
}

.menu-product-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* BODY */
.menu-product-card__body {
  padding: 0.7rem 0.8rem 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex: 1;
}

.menu-product-card__name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #111827;
}

.menu-product-card__desc {
  margin: 0;
  font-size: 0.78rem;
  color: #6b7280;
  max-height: 3.2em;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* FOOTER */
.menu-product-card__footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.menu-product-card__price {
  font-size: 0.98rem;
  font-weight: 700;
  color: #b91c1c;
}

.menu-product-card__tag {
  font-size: 0.7rem;
  padding: 0.18rem 0.6rem;
  border-radius: 999px;
  text-transform: none;
  letter-spacing: 0.06em;
  border: 1px solid #d1d5db;
  color: #374151;
  background: #f9fafb;
}

.menu-product-card__tag--combo {
  border-color: #bbf7d0;
  color: #166534;
  background: #dcfce7;
}

.menu-product-card__tag--flavors {
  border-color: #bfdbfe;
  color:var(--secondary-color);
  background: #dbeafe;
}

/* RESPONSIVE */
@media (min-width: 1024px) {
  .menu-hero__title {
    font-size: 2.4rem;
  }
}
</style>
