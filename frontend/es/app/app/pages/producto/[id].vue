<template>
  <div class="page-wrapper">
    <button class="nav-btn nav-btn--back" @click="goBack" aria-label="Volver">
      <Icon name="mdi:arrow-left" size="24" />
    </button>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-container">
        <Icon name="mdi:loading" class="spin-icon" size="60" />
        <p class="loading-text">Cargando detalles...</p>
      </div>
    </div>

    <div v-else-if="currentProduct" class="product-container animate-fade-in">
      
      <div class="gallery-column">
        <div class="image-wrapper">
          <div v-if="!imageLoaded && !previewUrl" class="skeleton-loader"></div>
          <img v-if="previewUrl" :src="previewUrl" alt="" class="img-preview" aria-hidden="true" />
          <img 
            ref="mainImageRef"
            :src="highResUrl" 
            :alt="displayName" 
            class="img-main"
            :class="{ 'is-loaded': imageLoaded }"
            loading="eager"
            @load="onImageLoad"
          />
          <div class="desktop-nav-controls">
            <button @click="goToPrev" class="nav-arrow" title="Anterior">
              <Icon name="mdi:chevron-left" size="30" />
            </button>
            <button @click="goToNext" class="nav-arrow" title="Siguiente">
              <Icon name="mdi:chevron-right" size="30" />
            </button>
          </div>
        </div>
      </div>

      <div class="details-column">
        <header class="product-header">
          <h1 class="product-title">{{ displayName }}</h1>
          <div class="price-block">
            <span v-if="showOriginalPrice" class="price-old">{{ formatoPesosColombianos(basePrice) }}</span>
            <span class="price-current">{{ formatoPesosColombianos(finalPrice) }}</span>
          </div>
          <p class="product-description">{{ productDescription }}</p>
        </header>

        <hr class="divider" />

        <section v-if="(currentProduct.lista_productobase || []).length > 0" class="section-block">
          <h3 class="section-title">INCLUYE</h3>
          <div class="base-products-grid">
            <div v-for="base in currentProduct.lista_productobase" :key="base.producto_id" class="base-item-card">
              <div class="base-item-img">
                <img :src="`https://img.restpe.com/${base.producto_urlimagen}`" alt="foto" loading="lazy" />
              </div>
              <div class="base-item-info">
                <div class="base-qty-badge">{{ Math.round(base.productocombo_cantidad) }}x</div>
                <span class="base-name">{{ base.producto_descripcion }}</span>
              </div>
              <button v-if="base.lista_productoCambio?.length > 0" class="btn-change-base" @click="changeProductBase(base)">
                Cambiar
              </button>
            </div>
          </div>
          <hr class="divider" />
        </section>

        <section v-for="group in currentProduct.lista_agrupadores || []" :key="group.modificador_id" class="section-block">
          <div class="group-header">
            <h3 class="section-title">{{ group.modificador_nombre }}</h3>
            <span class="group-requirements">{{ getGroupRequirementText(group) }}</span>
          </div>

          <div class="modifiers-list">
            <div 
              v-for="mod in group.listaModificadores || []" 
              :key="mod.modificadorseleccion_id"
              class="modifier-row"
              :class="{ 'is-selected': isSelected(mod, group.modificador_id) }"
              @click="handleRowClick(mod, group.modificador_id)"
            >
              <div class="modifier-input-wrapper">
                <div 
                  class="custom-check" 
                  :class="{ 
                    'type-radio': Number(group.modificador_esmultiple) === 0,
                    'checked': isSelected(mod, group.modificador_id)
                  }"
                ></div>
              </div>

              <div class="modifier-info">
                <span class="modifier-name">{{ mod.modificadorseleccion_nombre }}</span>
                <span v-if="Number(mod.modificadorseleccion_precio) > 0" class="modifier-price">
                  +{{ formatoPesosColombianos(Number(mod.modificadorseleccion_precio)) }}
                </span>
              </div>

              <div v-if="Number(group.modificador_esmultiple) === 1 && checkedAddition[mod.modificadorseleccion_id]" class="modifier-qty-control" @click.stop>
                <button class="qty-btn-mini" @click="decrement(mod, group.modificador_id)">−</button>
                <span class="qty-val-mini">{{ selectedAdditions[mod.modificadorseleccion_id]?.modificadorseleccion_cantidad || 1 }}</span>
                <button class="qty-btn-mini" @click="increment(mod, group.modificador_id)">+</button>
              </div>
            </div>
          </div>
        </section>

        <div class="bottom-spacer"></div>
      </div>
    </div>

    <div v-else class="product-container animate-fade-in">
      <p style="padding: 2rem; text-align: center;">No encontramos este producto en esta sede.</p>
    </div>

    <footer class="sticky-footer" v-if="currentProduct">
      <div class="footer-inner">
        <div class="main-qty-control">
          <button class="qty-btn-main" @click="quantity > 1 ? quantity-- : null" :disabled="quantity <= 1">
            <Icon name="mdi:minus" />
          </button>
          <span class="qty-val-main">{{ quantity }}</span>
          <button class="qty-btn-main" @click="quantity++">
            <Icon name="mdi:plus" />
          </button>
        </div>

        <button class="add-cart-btn btn-mobile-only" @click="processAddToCart('ask')">
          <div class="btn-content">
            <span>Agregar</span>
            <span class="btn-total">{{ formatoPesosColombianos(calculateTotal()) }}</span>
          </div>
        </button>

        <div class="desktop-actions btn-desktop-only">
          <button class="add-cart-btn btn-secondary" @click="processAddToCart('menu')">
            Agregar y seguir comprando
          </button>
          <button class="add-cart-btn btn-primary" @click="processAddToCart('pay')">
            <div class="btn-content-pc">
              
              <span class="btn-total-pc"> Ir a pagar {{ formatoPesosColombianos(calculateTotal()) }}</span>
            </div>
          </button>
        </div>

      </div>
    </footer>

    <div v-if="showChangeDialog" class="modal-backdrop" @click.self="showChangeDialog = false">
      <div class="modal-card">
        <header class="modal-header">
          <h3>Cambiar {{ productBaseToChange?.producto_descripcion }}</h3>
          <button class="close-modal-btn" @click="showChangeDialog = false">✕</button>
        </header>
        <div class="modal-body grid-options">
          <button v-for="option in productBaseToChange?.lista_productoCambio || []" :key="option.producto_id" class="option-card" @click="selectAlternative(option)">
            <img :src="`https://img.restpe.com/${option.producto_urlimagen}`" alt="" loading="lazy" />
            <span>{{ option.producto_descripcion }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showPostActionModal" class="modal-backdrop" @click.self="completeMobileAction('menu')">
      <div class="modal-card modal-center-text">
        <header class="modal-header">
          <h3 class="success-title">
            <Icon name="mdi:check-circle" color="#10b981" size="24" style="margin-right: 5px;"/> 
            ¡Agregado con éxito!
          </h3>
          <button class="close-modal-btn" @click="completeMobileAction('menu')">✕</button>
        </header>
        <div class="modal-body flex-column-actions">
          <p class="modal-msg">¿Qué te gustaría hacer ahora?</p>
          
          <button class="action-btn btn-go-pay" @click="completeMobileAction('pay')">
            Ir a pagar
          </button>
          
          <button class="action-btn btn-keep-shopping" @click="completeMobileAction('menu')">
            Agregar más cosas
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatoPesosColombianos } from '@/service/utils/formatoPesos'
import { usecartStore, useFetch, useHead, useSitesStore } from '#imports'
import { useToast } from '@/composables/useToast'
import { URI } from '~/service/conection'

const route = useRoute()
const router = useRouter()
const store = usecartStore()
const { showToast } = useToast()
const sitesStore = useSitesStore()

// --- ESTADOS Y STORES ---
const siteId = computed(() => (sitesStore?.location?.site?.site_id) || 1)
const quantity = ref(1)
const selectedAdditions = ref({})
const checkedAddition = ref({})
const exclusive = ref({})
const productBaseToChange = ref(null)
const showChangeDialog = ref(false)
// Nuevo estado para el modal de decisión móvil
const showPostActionModal = ref(false)

// Estado de carga de imagen para transición
const imageLoaded = ref(false)
const mainImageRef = ref(null) 

const onImageLoad = () => { imageLoaded.value = true }
const checkImageState = () => { if (mainImageRef.value?.complete) imageLoaded.value = true }

onMounted(() => { checkImageState() })

// --- DATA FETCHING ---
const { data: rawCategoriesData, pending: loading } = useFetch(
  () => `${URI}/tiendas/${siteId.value}/products`,
  { key: () => `menu-data-${siteId.value}` }
)

// ... (CÓDIGO DE PRODUCTO, PRECIOS, IMÁGENES IGUAL QUE ANTES) ...
const currentProductId = computed(() => Number(route.params.id))
const flatProducts = computed(() => {
  const raw = rawCategoriesData.value
  if (!raw || !raw.categorias) return []
  const list = []
  raw.categorias.forEach((cat) => {
    if (cat.visible && cat.products) {
      cat.products.forEach((prod) => {
        list.push({ ...prod, categoryName: cat.categoria_descripcion })
      })
    }
  })
  return list
})
const currentProduct = computed(() => flatProducts.value.find((p) => Number(p.producto_id) === currentProductId.value) || null)

const basePrice = computed(() => {
  if (!currentProduct.value) return 0
  const p = currentProduct.value
  return Number(p.lista_presentacion?.[0]?.producto_precio || p.productogeneral_precio || p.price || 0)
})
const discountAmount = computed(() => Number(currentProduct.value?.discount_amount || 0))
const finalPrice = computed(() => basePrice.value - discountAmount.value)
const showOriginalPrice = computed(() => discountAmount.value > 0)
const displayName = computed(() => currentProduct.value?.productogeneral_descripcion || currentProduct.value?.product_name || '')
const productDescription = computed(() => currentProduct.value?.productogeneral_descripcionadicional || currentProduct.value?.productogeneral_descripcionweb || 'Sin descripción detallada.')

const previewUrl = computed(() => {
  const p = currentProduct.value
  if (!p) return ''
  if (p.img_identifier) return `${URI}/read-photo-product/${p.img_identifier}/400`
  if (p.productogeneral_urlimagen) return `https://img.restpe.com/${p.productogeneral_urlimagen}`
  if (p.image_url) return p.image_url
  return ''
})
const highResUrl = computed(() => {
  const p = currentProduct.value
  if (!p) return '/placeholder.png'
  if (p.img_identifier) return `${URI}/read-photo-product/${p.img_identifier}/600`
  if (p.productogeneral_urlimagen) return `https://img.restpe.com/${p.productogeneral_urlimagen}`
  if (p.image_url) return p.image_url
  return '/placeholder.png'
})

// ... (LÓGICA DE GRUPOS, LIMITES, HANDLERS IGUAL QUE ANTES) ...
const groupLimits = computed(() => {
  const p = currentProduct.value
  if (!p || !Array.isArray(p.lista_agrupadores)) return {}
  const limits = {}
  p.lista_agrupadores.forEach((g) => {
    const key = String(g.modificador_id)
    limits[key] = {
      min: Number(g.modificador_cantidadminima ?? 0),
      multiple: Number(g.modificador_esmultiple ?? 0) === 1,
      max: g.listaModificadores?.reduce((acc, m) => acc + Number(m.productogeneralmodificador_cantidadmaxima || 0), 0) || 0
    }
  })
  return limits
})
const getGroupRequirementText = (group) => {
  const limits = groupLimits.value[String(group.modificador_id)]
  if (!limits) return ''
  if (limits.min > 0 && limits.max > 0) return `Elige ${limits.min} (Máx ${limits.max})`
  if (limits.min > 0) return `Elige al menos ${limits.min}`
  return 'Opcional'
}
const isSelected = (mod, groupId) => !!selectedAdditions.value[mod.modificadorseleccion_id]
const groupCount = (groupId) => {
  const idStr = String(groupId)
  return Object.values(selectedAdditions.value).reduce((acc, it) => String(it.modificador_id) === idStr ? acc + Number(it.modificadorseleccion_cantidad || 0) : acc, 0)
}
const calculateTotal = () => {
  let total = finalPrice.value * quantity.value
  Object.values(selectedAdditions.value).forEach((item) => {
    total += Number(item.modificadorseleccion_precio || 0) * Number(item.modificadorseleccion_cantidad || 1) * quantity.value
  })
  return total
}
const handleRowClick = (mod, groupId) => {
  const limits = groupLimits.value[String(groupId)]
  if (!limits.multiple) {
    handleAdditionChange(mod, groupId)
    return
  }
  const isChecked = checkedAddition.value[mod.modificadorseleccion_id]
  checkedAddition.value[mod.modificadorseleccion_id] = !isChecked
  handleAdditionChange(mod, groupId)
}
const handleAdditionChange = (item, groupId) => {
  const key = String(groupId)
  const limits = groupLimits.value[key]
  if (!limits.multiple) {
    Object.keys(selectedAdditions.value).forEach((k) => {
      if (selectedAdditions.value[k].modificador_id === groupId) delete selectedAdditions.value[k]
    })
    exclusive.value[groupId] = item.modificadorseleccion_id
    selectedAdditions.value[item.modificadorseleccion_id] = { ...item, modificadorseleccion_cantidad: 1, modificador_id: groupId }
  } else {
    if (checkedAddition.value[item.modificadorseleccion_id]) {
      if (limits.max > 0 && groupCount(key) + 1 > limits.max) {
        checkedAddition.value[item.modificadorseleccion_id] = false
        showToast({ title: 'Límite alcanzado', message: `Máximo ${limits.max} opciones`, severity: 'warn' })
        return
      }
      selectedAdditions.value[item.modificadorseleccion_id] = { ...item, modificadorseleccion_cantidad: 1, modificador_id: groupId }
    } else {
      delete selectedAdditions.value[item.modificadorseleccion_id]
    }
  }
}
const increment = (item, groupId) => {
  const key = String(groupId)
  const limits = groupLimits.value[key]
  if (limits.max > 0 && groupCount(key) + 1 > limits.max) {
    showToast({ title: 'Límite', message: 'Máximo alcanzado', severity: 'warn' })
    return
  }
  selectedAdditions.value[item.modificadorseleccion_id].modificadorseleccion_cantidad++
}
const decrement = (item) => {
  const entry = selectedAdditions.value[item.modificadorseleccion_id]
  if (entry.modificadorseleccion_cantidad > 1) {
    entry.modificadorseleccion_cantidad--
  } else {
    checkedAddition.value[item.modificadorseleccion_id] = false
    delete selectedAdditions.value[item.modificadorseleccion_id]
  }
}
const changeProductBase = (base) => {
  productBaseToChange.value = base
  showChangeDialog.value = true
}
const selectAlternative = (option) => {
  const current = productBaseToChange.value
  const backup = {
    producto_id: current.producto_id,
    producto_descripcion: current.producto_descripcion,
    producto_precio: current.producto_precio,
    producto_urlimagen: current.producto_urlimagen,
    producto_cambio_id: current.producto_id
  }
  const list = current.lista_productoCambio || []
  const idx = list.findIndex((i) => i.producto_id === option.producto_id)
  if (idx !== -1) list.splice(idx, 1, backup)
  else list.push(backup)
  Object.assign(current, {
    producto_id: option.producto_id,
    producto_descripcion: option.producto_descripcion,
    producto_precio: option.producto_precio,
    producto_urlimagen: option.producto_urlimagen
  })
  showChangeDialog.value = false
}

// --- ADD TO CART & NAV MODIFICADO ---
const validateMinMaximums = () => {
  for (const [gId, lim] of Object.entries(groupLimits.value)) {
    if (groupCount(gId) < lim.min) return false
  }
  return true
}

/**
 * Procesa la adición al carrito y decide la navegación.
 * @param {string} mode - 'ask' (móvil, preguntar), 'pay' (ir a pagar), 'menu' (ir a inicio)
 */
const processAddToCart = (mode) => {
  if (!currentProduct.value) return
  
  if (!validateMinMaximums()) {
    showToast({ title: 'Faltan opciones', message: 'Por favor completa las opciones obligatorias.', severity: 'error' })
    return
  }

  // 1. Agregar al Store
  store.addProductToCart(currentProduct.value, quantity.value, Object.values(selectedAdditions.value))
  
  // 2. Lógica de redirección
  if (mode === 'ask') {
    // En móvil no redirigimos aun, abrimos el modal
    showPostActionModal.value = true
  } else if (mode === 'pay') {
    showToast({ title: 'Agregado', message: 'Yendo a pagar...', severity: 'success' })
    router.push('/pay')
  } else {
    // mode === 'menu'
    showToast({ title: 'Agregado', message: 'Producto agregado al carrito', severity: 'success' })
    router.push('/')
  }
}

// Función llamada desde el Modal Móvil para ejecutar la navegación final
const completeMobileAction = (destination) => {
  showPostActionModal.value = false
  if (destination === 'pay') {
    router.push('/pay')
  } else {
    router.push('/')
  }
}

const goBack = () => router.push('/')

// ... (Resto de la navegación igual)
const goToRelative = (step) => {
  const list = flatProducts.value
  const idx = list.findIndex((p) => Number(p.producto_id) === currentProductId.value)
  if (idx === -1) return
  const nextIdx = (idx + step + list.length) % list.length
  router.replace(`/producto/${list[nextIdx].producto_id}`)
}
const goToNext = () => goToRelative(1)
const goToPrev = () => goToRelative(-1)

watch(currentProduct, async (newVal) => {
  if (newVal) {
    imageLoaded.value = false 
    quantity.value = 1
    selectedAdditions.value = {}
    checkedAddition.value = {}
    exclusive.value = {}
    newVal.lista_agrupadores?.forEach((g) => {
      const lim = groupLimits.value[String(g.modificador_id)]
      if (lim && lim.min > 0 && !lim.multiple && g.listaModificadores?.length > 0) {
        handleAdditionChange(g.listaModificadores[0], g.modificador_id)
      }
    })
    await nextTick()
    checkImageState()
  }
}, { immediate: true })

useHead({ title: computed(() => currentProduct.value ? `${displayName.value} - Menú` : 'Cargando...') })
</script>

<style scoped>
/* ... (ESTILOS ANTERIORES SE MANTIENEN IGUAL) ... */
.page-wrapper {
  min-height: 100vh;
  padding-bottom: 90px;
  max-width: 1300px;
  margin: auto;
  font-family: 'Roboto', sans-serif;
  color: var(--text-main, #1f2937);
  position: relative;
}
.loading-overlay {
  position: fixed; inset: 0; background: var(--bg-page, #f9fafb);
  z-index: 40; display: flex; align-items: center; justify-content: center;
}
.spinner-container { display: flex; flex-direction: column; align-items: center; gap: 15px; color: var(--primary, #dc2626); }
.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.nav-btn {
  position: fixed; z-index: 50; background: white;
  border: 1px solid var(--border, #e5e7eb); box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  border-radius: 50%; width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s; color: var(--text-main, #1f2937);
}
.nav-btn:hover { background: #f3f4f6; transform: scale(1.05); }
.nav-btn--back { top: 4rem; left: 1rem; }
.product-container { display: grid; grid-template-columns: 1fr; max-width: 1200px; margin: 0 auto; }
@media (min-width: 1024px) {
  .product-container { grid-template-columns: 1fr 1fr; gap: 40px; padding: 40px; align-items: stretch; }
}
.gallery-column { width: 100%; position: relative; }
.image-wrapper {
  position: relative; background: #f3f4f6; width: 100%; aspect-ratio: 1/1;
  border-radius: 20px; overflow: hidden;
}
.skeleton-loader {
  position: absolute; inset: 0; background: #f3f4f6;
  background-image: linear-gradient(90deg, #f3f4f6 0px, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite linear; z-index: 5; 
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.img-preview {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  object-fit: cover; display: block; z-index: 1; filter: blur(10px); transform: scale(1.1);
}
.img-main {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  object-fit: cover; display: block; z-index: 2; opacity: 0; transition: opacity 0.5s ease;
}
.img-main.is-loaded { opacity: 1; }
@media (min-width: 1024px) {
  .image-wrapper { position: sticky; top: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); z-index: 10; }
}
.desktop-nav-controls { display: none; }
@media (min-width: 1024px) {
  .desktop-nav-controls {
    display: flex; justify-content: space-between; position: absolute;
    top: 50%; width: 100%; transform: translateY(-50%); padding: 0 10px; pointer-events: none; z-index: 10;
  }
  .nav-arrow {
    pointer-events: auto; background: rgba(255,255,255,0.8); backdrop-filter: blur(4px);
    border: none; border-radius: 50%; width: 40px; height: 40px;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s;
  }
  .nav-arrow:hover { transform: scale(1.1); background: white; }
}
.details-column { padding: 20px; background: white; }
@media (min-width: 1024px) { .details-column { padding: 1rem; background: transparent; } }
.product-title { font-size: 1.5rem; font-weight: 800; text-transform: uppercase; margin-bottom: 0.5rem; line-height: 1.2; }
.price-block { margin-bottom: 1rem; display: flex; align-items: baseline; gap: 10px; }
.price-current { font-size: 1.5rem; font-weight: 700; color: var(--primary, #dc2626); }
.price-old { font-size: 1rem; text-decoration: line-through; color: var(--text-light, #6b7280); }
.product-description { color: var(--text-light, #6b7280); font-size: 0.95rem; line-height: 1.5; }
.divider { border: 0; border-top: 1px solid var(--border, #e5e7eb); margin: 1.5rem 0; }
.section-block { margin-bottom: 2rem; }
.section-title { font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
.group-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.group-requirements { font-size: 0.75rem; background: #eee; padding: 2px 8px; border-radius: 10px; color: #555; font-weight: 600; }
.base-products-grid { display: grid; gap: 10px; margin-top: 10px; }
.base-item-card { display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid var(--border, #e5e7eb); border-radius: 12px; background: white; }
.base-item-img { width: 50px; height: 50px; border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.base-item-img img { width: 100%; height: 100%; object-fit: cover; }
.base-item-info { flex: 1; }
.base-qty-badge { font-size: 0.75rem; font-weight: bold; background: #f3f4f6; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 2px; }
.base-name { display: block; font-size: 0.9rem; font-weight: 500; }
.btn-change-base { background: black; color: white; border: none; font-size: 0.75rem; padding: 6px 12px; border-radius: 20px; font-weight: 600; cursor: pointer; }
.modifiers-list { display: flex; flex-direction: column; gap: 12px; }
.modifier-row { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid var(--border, #e5e7eb); border-radius: 12px; background: white; cursor: pointer; transition: all 0.2s ease; }
.modifier-row:hover { border-color: #ccc; }
.modifier-row.is-selected { border-color: var(--primary, #dc2626); background-color: #fff5f5; }
.custom-check { width: 20px; height: 20px; border: 2px solid #ccc; border-radius: 4px; position: relative; transition: all 0.2s; }
.custom-check.type-radio { border-radius: 50%; }
.custom-check.checked { background-color: var(--primary, #dc2626); border-color: var(--primary, #dc2626); }
.custom-check.checked::after { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; background: white; border-radius: 1px; }
.custom-check.type-radio.checked::after { border-radius: 50%; }
.modifier-info { flex: 1; display: flex; justify-content: space-between; align-items: center; font-size: 0.95rem; }
.modifier-price { font-weight: 600; font-size: 0.9rem; color: var(--text-light, #6b7280); }
.modifier-qty-control { display: flex; align-items: center; background: white; border: 1px solid var(--border, #e5e7eb); border-radius: 8px; overflow: hidden; }
.qty-btn-mini { background: #f9fafb; border: none; padding: 5px 10px; cursor: pointer; font-weight: bold; }
.qty-val-mini { padding: 0 5px; font-size: 0.85rem; font-weight: 600; }

/* FOOTER STYLES */
.sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; padding: 15px 20px; box-shadow: 0 -4px 20px rgba(0,0,0,0.08); z-index: 100; }
.footer-inner { max-width: 800px; margin: 0 auto; display: flex; gap: 15px; align-items: center; }

.main-qty-control { display: flex; align-items: center; border: 1px solid #e5e7eb; border-radius: 12px; padding: 5px; background: white; height: 50px; }
.qty-btn-main { width: 40px; height: 100%; border: none; background: transparent; font-size: 1.2rem; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--text-main, #1f2937); }
.qty-val-main { width: 30px; text-align: center; font-weight: 700; font-size: 1.1rem; }

/* Botones Comunes */
.add-cart-btn { flex: 1; border-radius: 12px; padding: 0 20px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: all 0.2s; height: 50px; border: none; display: flex; align-items: center; justify-content: center; }
.btn-content { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.btn-content-pc { display: flex; min-width: max-content; flex-direction: column; align-items: center; line-height: 1.1; }

/* Estilos de botones específicos */
.btn-primary { background: var(--primary, #dc2626); color: white; }
.btn-primary:hover { background: var(--primary-dark, #b91c1c); }

.btn-secondary { background: white; color: var(--text-main, #1f2937); border: 2px solid #e5e7eb; }
.btn-secondary:hover { border-color: var(--primary, #dc2626); color: var(--primary, #dc2626); }

/* Control de visibilidad PC vs Móvil */
.btn-mobile-only { display: flex; background: var(--primary, #dc2626); color: white; }
.btn-desktop-only { display: none; }

@media (min-width: 1024px) {
  .btn-mobile-only { display: none; }
  .btn-desktop-only { display: flex; flex: 1; gap: 15px; }
  .footer-inner { max-width: 900px; }
}

/* MODAL STYLES */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; padding: 20px; }
.modal-card { background: white; border-radius: 16px; width: 100%; max-width: 400px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.2); }
.modal-header { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 1rem; }
.success-title { display: flex; align-items: center; color: var(--text-main, #1f2937); }
.close-modal-btn { background: #f3f4f6; border: none; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; font-weight: bold; }
.modal-body { padding: 20px; max-height: 60vh; overflow-y: auto; }

/* Estilos específicos para el Modal Post-Add */
.modal-center-text { text-align: center; }
.modal-msg { margin-bottom: 20px; font-size: 1.1rem; color: #4b5563; }
.flex-column-actions { display: flex; flex-direction: column; gap: 12px; }
.action-btn { width: 100%; padding: 14px; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: transform 0.1s; }
.action-btn:active { transform: scale(0.98); }

.btn-go-pay { background: var(--primary, #dc2626); color: white; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3); }
.btn-keep-shopping { background: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb; }

/* Grid Options (Modal Cambio) */
.grid-options { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
.option-card { border: 1px solid #eee; background: white; padding: 10px; border-radius: 10px; cursor: pointer; display: flex; flex-direction: column; align-items: center; text-align: center; transition: transform 0.1s; }
.option-card:hover { transform: scale(1.03); border-color: #ccc; }
.option-card img { width: 80px !important; height: 80px !important; object-fit: contain; margin-bottom: 8px; display: block; }
.option-card span { font-size: 0.85rem; line-height: 1.2; }
</style>