<template>
  <!-- BACKDROP NATIVO -->
  <div
    v-if="localVisible"
    class="product-dialog-backdrop"
    @click.self="closeDialog"
  >
    <!-- Botón cerrar (desktop) -->
    <button
      type="button"
      class="dialog-close-btn"
      @click="closeDialog"
    >
      ✕
    </button>

    <!-- Flechas flotantes (solo desktop, ocultas en móvil vía CSS) -->
    <button
      type="button"
      class="dialog-nav-btn dialog-nav-btn--left"
      @click.stop="onPrevClick"
      aria-label="Producto anterior"
    >
      <Icon name="mdi:chevron-left" class="dialog-nav-btn__icon" />
    </button>

    <button
      type="button"
      class="dialog-nav-btn dialog-nav-btn--right"
      @click.stop="onNextClick"
      aria-label="Siguiente producto"
    >
      <Icon name="mdi:chevron-right" class="dialog-nav-btn__icon" />
    </button>

    <div class="main">
      <div class="product-dialog">
        <!-- Encabezado -->
        <header class="dialog-header">
          <p class="product-name">
            {{ displayName }}
          </p>

          <div class="header-price-block">
            <p
              v-if="showOriginalPrice"
              class="product-price product-price--old"
            >
              {{ formatoPesosColombianos(basePrice) }}
            </p>
            <p class="product-price">
              {{ formatoPesosColombianos(finalPrice) }}
            </p>
          </div>
        </header>

        <!-- CONTENIDO PRINCIPAL (scrollea solo esto) -->
        <div class="dialog-body" ref="dialogBodyRef">
          <!-- Imagen del producto -->
          <div class="photo">
            <img
              class="photo-img"
              :src="fullImageUrl"
              :alt="displayName"
            />
          </div>

          <!-- Lado derecho: descripción, modificadores, incluye -->
          <div class="dialog-content-right">
            <!-- DESCRIPCIÓN -->
            <section class="description-section">
              <p class="section-title">
                {{ lang === 'es' ? 'DESCRIPCIÓN' : 'DESCRIPTION' }}
              </p>
              <p class="section-text text-description">
                {{ productDescription }}
              </p>
            </section>

            <!-- GRUPOS DE MODIFICADORES (lista_agrupadores) -->
            <section
              v-for="group in currentProduct.lista_agrupadores || []"
              :key="group.modificador_id"
              class="addition-group"
            >
              <p class="addition-group-title">
                <strong>{{ group.modificador_nombre }}</strong>
              </p>

              <div class="addition-group-list">
                <div
                  v-for="mod in group.listaModificadores || []"
                  :key="mod.modificadorseleccion_id"
                  class="addition-item-row"
                >
                  <!-- Radio para exclusivo / Checkbox para múltiple -->
                  <input
                    v-if="Number(group.modificador_esmultiple) === 0"
                    type="radio"
                    class="addition-checkbox"
                    :name="`group-${group.modificador_id}`"
                    :value="mod.modificadorseleccion_id"
                    v-model="exclusive[group.modificador_id]"
                    @change="() => handleAdditionChange(mod, group.modificador_id)"
                  />
                  <input
                    v-else
                    type="checkbox"
                    class="addition-checkbox"
                    v-model="checkedAddition[mod.modificadorseleccion_id]"
                    @change="() => handleAdditionChange(mod, group.modificador_id)"
                  />

                  <div class="addition-item-content">
                    <span class="addition-name adicion">
                      {{ mod.modificadorseleccion_nombre }}
                    </span>

                    <div class="addition-actions">
                      <!-- Precio -->
                      <span
                        v-if="Number(mod.modificadorseleccion_precio) > 0"
                        class="addition-price"
                      >
                        <b
                          v-if="selectedAdditions[mod.modificadorseleccion_id]"
                        >
                          {{
                            formatoPesosColombianos(
                              Number(mod.modificadorseleccion_precio) *
                                Number(
                                  selectedAdditions[mod.modificadorseleccion_id]
                                    ?.modificadorseleccion_cantidad || 1
                                )
                            )
                          }}
                        </b>
                        <b v-else>
                          {{
                            formatoPesosColombianos(
                              Number(mod.modificadorseleccion_precio)
                            )
                          }}
                        </b>
                      </span>

                      <!-- Cantidad (solo grupos múltiples con precio y marcado) -->
                      <div
                        v-if="
                          Number(group.modificador_esmultiple) === 1 &&
                          Number(mod.modificadorseleccion_precio) > 0 &&
                          checkedAddition[mod.modificadorseleccion_id]
                        "
                        class="addition-qty-buttons"
                      >
                        <button
                          type="button"
                          class="qty-btn"
                          @click="decrement(mod, group.modificador_id)"
                        >
                          −
                        </button>
                        <input
                          class="qty-input"
                          type="text"
                          :value="
                            selectedAdditions[mod.modificadorseleccion_id]
                              ?.modificadorseleccion_cantidad || 1
                          "
                          readonly
                        />
                        <button
                          type="button"
                          class="qty-btn"
                          @click="increment(mod, group.modificador_id)"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <hr />
              </div>
            </section>

            <!-- INCLUYE (lista_productobase) -->
            <section
              v-if="(currentProduct.lista_productobase || []).length > 0"
              class="includes-section"
            >
              <h3 class="includes-title">
                <strong>
                  {{ lang === 'es' ? 'INCLUYE' : 'INCLUDE' }}
                </strong>
              </h3>

              <div class="product-base-grid">
                <div
                  v-for="base in currentProduct.lista_productobase || []"
                  :key="base.producto_id"
                  class="product-base-item"
                >
                  <div class="product-base-item-header">
                    <h3 class="m-0 p-0 text-2xl product-base-qty">
                      {{ Math.round(base.productocombo_cantidad) }} ×
                    </h3>
                    <img
                      class="product-base-img"
                      :src="`https://img.restpe.com/${base.producto_urlimagen}`"
                      :alt="base.producto_descripcion"
                    />
                    <button
                      v-if="
                        base.lista_productoCambio &&
                        base.lista_productoCambio.length > 0
                      "
                      type="button"
                      class="product-base-change-btn"
                      @click="changeProductBase(base)"
                    >
                      {{ lang === 'es' ? 'Cambiar' : 'Change' }}
                    </button>
                  </div>

                  <h3 class="m-0 p-0 product-base-desc">
                    {{ base.producto_descripcion }}
                  </h3>

                  <div
                    style="border-top:.3rem solid;margin-top:.5rem;opacity:.2"
                  ></div>
                </div>
              </div>
            </section>
          </div>
        </div>

        <!-- FOOTER: NAV + CANTIDAD + AGREGAR -->
        <footer class="dialog-footer">
        
          <!-- Control de cantidad -->
          <div class="cart-addition-quantity-control ">
            <button
              type="button"
              class="cart-addition-quantity-btn-minus"
              @click="quantity > 1 ? quantity-- : 0"
            >
              −
            </button>

            <span class="cart-addition-quantity-label p-0 text-center">
              {{ quantity }}
            </span>

            <button
              type="button"
              class="cart-addition-quantity-btn-plus"
              @click="quantity++"
            >
              +
            </button>
          </div>

          <!-- Agregar al carrito -->
          <button
            type="button"
            class="add-to-cart-btn"
            @click="addToCart"
          >
            {{
              lang === 'es'
                ? 'Agregar al carrito'
                : 'Add to cart'
            }}
          </button>

      
          <!-- Cerrar flotante (móvil) -->
          <button
            type="button"
            style="
              position: absolute;
              right: 0;
              top: 4rem;
              border-radius: 99px 0 0 99px;
            "
            class="footer-nav-btn footer-nav-btn--next"
            @click="closeDialog"
            aria-label="Cerrar"
          >
            <Icon name="mdi:close" class="footer-nav-btn__icon" />
          </button>
        </footer>

        <!-- MINI DIALOG PARA CAMBIAR PRODUCTO BASE -->
        <div
          v-if="showChangeDialog && productBaseToChange"
          class="change-base-backdrop"
          @click.self="showChangeDialog = false"
        >
          <div class="change-base-dialog">
            <header class="change-base-header">
              <h3 class="change-base-title">
                {{
                  lang === 'es'
                    ? 'Elige una alternativa para'
                    : 'Select alternative for'
                }}
                {{ productBaseToChange.producto_descripcion }}
              </h3>
              <button
                type="button"
                class="change-base-close"
                @click="showChangeDialog = false"
              >
                ✕
              </button>
            </header>

            <div class="change-base-options">
              <button
                v-for="option in productBaseToChange.lista_productoCambio || []"
                :key="option.producto_id"
                type="button"
                class="change-option-card"
                @click="selectAlternative(option)"
              >
                <img
                  class="change-option-img"
                  :src="`https://img.restpe.com/${option.producto_urlimagen}`"
                  :alt="option.producto_descripcion"
                />
                <p class="change-option-text">
                  {{ option.producto_descripcion }}
                </p>
              </button>
            </div>
          </div>
        </div>
        <!-- FIN MINI DIALOG -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { formatoPesosColombianos } from '@/service/utils/formatoPesos'
import { usecartStore } from '#imports'
import { useToast } from '@/composables/useToast'

const store = usecartStore()
const { showToast } = useToast()

const props = defineProps({
  product: {
    type: Object,
    required: true
  },
  visible: {
    type: Boolean,
    default: false
  },
  // idioma opcional
  lang: {
    type: String,
    default: 'es'
  }
})

const emit = defineEmits(['update:visible', 'added', 'next', 'prev'])

const currentProduct = computed(() => props.product || {})
const lang = computed(() => (props.lang || 'es').toLowerCase())

// v-model:visible
const localVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const dialogBodyRef = ref(null)

// ======== PRECIO / NOMBRE / DESCRIPCION ========

const discountAmount = computed(() =>
  Number(currentProduct.value.discount_amount || 0)
)

const discountPercent = computed(() =>
  Number(currentProduct.value.discount_percent || 0)
)

const hasDiscount = computed(
  () => discountAmount.value > 0 && discountPercent.value > 0
)

const basePrice = computed(() => {
  const p = currentProduct.value
  const presentationPrice = Number(
    p.lista_presentacion?.[0]?.producto_precio ?? 0
  )

  if (presentationPrice > 0) return presentationPrice

  const generalPrice = Number(p.productogeneral_precio ?? 0)
  if (generalPrice > 0) return generalPrice

  return Number(p.price ?? 0)
})

const finalPrice = computed(() => {
  const base = basePrice.value
  const disc = discountAmount.value
  const out = base - disc
  return out > 0 ? out : base
})

const showOriginalPrice = computed(
  () => hasDiscount.value && basePrice.value > 0
)

const displayName = computed(() => {
  const p = currentProduct.value
  if (lang.value === 'es') {
    return (
      p.productogeneral_descripcion ||
      p.productogeneral_descripcionweb ||
      p.product_name ||
      ''
    )
  }
  return p.english_name || p.product_name || ''
})

const productDescription = computed(() => {
  const p = currentProduct.value
  if (lang.value === 'es') {
    const d =
      p.productogeneral_descripcionadicional ||
      p.productogeneral_descripcionweb ||
      p.productogeneral_descripcion ||
      ''
    return d ? d.toLowerCase() : 'este producto aún no tiene descripción.'
  }
  const d = p.english_description || ''
  return d
    ? d.toLowerCase()
    : 'this product does not have a description yet.'
})

const fullImageUrl = computed(() => {
  const p = currentProduct.value

  if (p.productogeneral_urlimagen) {
    return `https://img.restpe.com/${p.productogeneral_urlimagen}`
  }

  if (p.image_url) {
    if (p.image_url.startsWith('http')) return p.image_url
    return `${p.image_url}`
  }

  if (p.img_identifier) {
    // por compatibilidad con el backend de Tezo
    return `${URI}/read-photo-product/${p.img_identifier}/600`
  }

  return '/placeholder.png'
})

// ======== MODIFICADORES (lista_agrupadores) ========

const selectedAdditions = ref({})
const checkedAddition = ref({})
const exclusive = ref({})
const quantity = ref(1)

const groupLimits = computed(() => {
  const p = currentProduct.value
  if (!p || !Array.isArray(p.lista_agrupadores)) return {}

  const limits = {}
  p.lista_agrupadores.forEach((g) => {
    const key = String(g.modificador_id)
    limits[key] = {
      min: Number(g.modificador_cantidadminima ?? 0),
      multiple: Number(g.modificador_esmultiple ?? 0) === 1,
      max:
        g.listaModificadores?.reduce(
          (acc, m) =>
            acc +
            Number(m.productogeneralmodificador_cantidadmaxima || 0),
          0
        ) || 0
    }
  })
  return limits
})

const groupCount = (groupId) => {
  const idStr = String(groupId)
  return Object.values(selectedAdditions.value).reduce(
    (acc, it) =>
      String(it.modificador_id) === idStr
        ? acc + Number(it.modificadorseleccion_cantidad || 0)
        : acc,
    0
  )
}

const faltaMinimos = () => {
  for (const [gId, lim] of Object.entries(groupLimits.value)) {
    if (groupCount(gId) < lim.min) return true
  }
  return false
}

const presetMinimums = () => {
  const p = currentProduct.value
  if (!p || !Array.isArray(p.lista_agrupadores)) return

  selectedAdditions.value = {}
  checkedAddition.value = {}
  exclusive.value = {}

  p.lista_agrupadores.forEach((g) => {
    const lim = groupLimits.value[String(g.modificador_id)]
    if (!lim || lim.min === 0) return

    g.listaModificadores
      .slice(0, lim.min)
      .forEach((mod, idx) => {
        if (!lim.multiple && idx > 0) return

        if (lim.multiple) {
          checkedAddition.value[mod.modificadorseleccion_id] = true
        } else {
          exclusive.value[g.modificador_id] =
            mod.modificadorseleccion_id
        }

        selectedAdditions.value[mod.modificadorseleccion_id] = {
          ...mod,
          modificadorseleccion_cantidad: 1,
          modificador_id: g.modificador_id
        }
      })
  })
}

const handleAdditionChange = (item, groupId) => {
  const key = String(groupId)
  const limits = groupLimits.value[key]
  if (!limits) return

  // Grupo exclusivo (radio)
  if (!limits.multiple) {
    // limpiar anteriores del grupo
    Object.keys(selectedAdditions.value).forEach((k) => {
      if (selectedAdditions.value[k].modificador_id === groupId) {
        delete selectedAdditions.value[k]
      }
    })

    exclusive.value[groupId] = item.modificadorseleccion_id
    selectedAdditions.value[item.modificadorseleccion_id] = {
      ...item,
      modificadorseleccion_cantidad: 1,
      modificador_id: groupId
    }
    return
  }

  // Grupo múltiple (checkbox)
  if (checkedAddition.value[item.modificadorseleccion_id]) {
    // activando
    if (groupCount(key) + 1 > limits.max && limits.max > 0) {
      checkedAddition.value[item.modificadorseleccion_id] = false
      showToast({
        title: 'Límite alcanzado',
        message: `Máximo ${limits.max} en este grupo`,
        severity: 'warn',
        duration: 3000
      })
      return
    }

    selectedAdditions.value[item.modificadorseleccion_id] = {
      ...item,
      modificadorseleccion_cantidad: 1,
      modificador_id: groupId
    }
  } else {
    // desactivando
    delete selectedAdditions.value[item.modificadorseleccion_id]
    if (groupCount(key) < limits.min) {
      // volver a activar
      checkedAddition.value[item.modificadorseleccion_id] = true
      selectedAdditions.value[item.modificadorseleccion_id] = {
        ...item,
        modificadorseleccion_cantidad: 1,
        modificador_id: groupId
      }
      showToast({
        title: 'Cantidad mínima',
        message: `Debes elegir al menos ${limits.min}`,
        severity: 'warn',
        duration: 3000
      })
    }
  }
}

const increment = (item, groupId) => {
  const key = String(groupId)
  const limits = groupLimits.value[key]
  if (!limits) return

  if (groupCount(key) + 1 > limits.max && limits.max > 0) {
    showToast({
      title: 'Límite alcanzado',
      message: `Máximo ${limits.max} en este grupo`,
      severity: 'warn',
      duration: 3000
    })
    return
  }

  selectedAdditions.value[item.modificadorseleccion_id]
    .modificadorseleccion_cantidad++
}

const decrement = (item, groupId) => {
  const key = String(groupId)
  const limits = groupLimits.value[key]
  if (!limits) return

  const entry =
    selectedAdditions.value[item.modificadorseleccion_id]
  if (!entry) return

  if (entry.modificadorseleccion_cantidad === 1) {
    if (groupCount(key) - 1 < limits.min) {
      showToast({
        title: 'Cantidad mínima',
        message: `Debes mantener al menos ${limits.min}`,
        severity: 'warn',
        duration: 3000
      })
      return
    }
    checkedAddition.value[item.modificadorseleccion_id] = false
    delete selectedAdditions.value[item.modificadorseleccion_id]
  } else {
    entry.modificadorseleccion_cantidad--
  }
}

// ======== INCLUYE (lista_productobase) ========

const productBaseToChange = ref(null)
const showChangeDialog = ref(false)

const changeProductBase = (productBase) => {
  productBaseToChange.value = productBase
  showChangeDialog.value = true
}

const selectAlternative = (option) => {
  if (!productBaseToChange.value) return

  const current = productBaseToChange.value

  const backup = {
    producto_id: current.producto_id,
    producto_descripcion: current.producto_descripcion,
    producto_precio: current.producto_precio,
    producto_urlimagen: current.producto_urlimagen,
    producto_cambio_id: current.producto_id
  }

  const list = current.lista_productoCambio || []
  const idx = list.findIndex(
    (item) => item.producto_id === option.producto_id
  )
  if (idx !== -1) {
    list.splice(idx, 1, backup)
  } else {
    list.push(backup)
  }

  current.producto_id = option.producto_id
  current.producto_descripcion = option.producto_descripcion
  current.producto_precio = option.producto_precio
  current.producto_urlimagen = option.producto_urlimagen

  showChangeDialog.value = false
}

// ======== SCROLL / NAV / ADD TO CART ========

const scrollDialogToTop = () => {
  if (!dialogBodyRef.value) return
  dialogBodyRef.value.scrollTo({
    top: 0
  })
}

const closeDialog = () => {
  localVisible.value = false
}

const addToCart = () => {
  if (faltaMinimos()) {
    showToast({
      title: lang.value === 'es' ? 'Falta elegir' : 'Missing selection',
      message:
        lang.value === 'es'
          ? 'Selecciona todas las opciones mínimas antes de continuar.'
          : 'Please select all required options before continuing.',
      severity: 'warn',
      duration: 3000
    })
    return
  }

  try {
    if (store && typeof store.addProductToCart === 'function') {
      store.addProductToCart(
        currentProduct.value,
        quantity.value,
        Object.values(selectedAdditions.value)
      )
    }

    showToast({
      title:
        lang.value === 'es'
          ? 'Producto agregado'
          : 'Product added',
      message:
        (currentProduct.value.productogeneral_descripcion ||
          currentProduct.value.product_name ||
          'Producto') + ' se agregó al carrito.',
      severity: 'success',
      duration: 3000
    })

    emit('added', {
      product: currentProduct.value,
      quantity: quantity.value,
      additions: Object.values(selectedAdditions.value)
    })

    localVisible.value = false
  } catch (err) {
    console.error('Error agregando al carrito', err)
    showToast({
      title: 'Error',
      message:
        lang.value === 'es'
          ? 'No pudimos agregar el producto al carrito. Intenta de nuevo.'
          : 'We could not add the product to the cart. Please try again.',
      severity: 'error',
      duration: 4000
    })
  }
}

const onPrevClick = () => {
  scrollDialogToTop()
  emit('prev')
}

const onNextClick = () => {
  scrollDialogToTop()
  emit('next')
}

// ======== WATCHERS ========

watch(
  () => localVisible.value,
  (open) => {
    if (open) {
      quantity.value = 1
      presetMinimums()
      nextTick(scrollDialogToTop)
    } else {
      exclusive.value = {}
      selectedAdditions.value = {}
      checkedAddition.value = {}
      quantity.value = 1
    }
  }
)

watch(
  () => props.product,
  () => {
    exclusive.value = {}
    selectedAdditions.value = {}
    checkedAddition.value = {}
    quantity.value = 1
    if (localVisible.value) {
      presetMinimums()
      nextTick(scrollDialogToTop)
    }
  }
)
</script>

<style scoped>
* {
  font-family: roboto;
}

.main {
  max-height: 100vh;
  width: 100vw;
  padding: 0.5rem;
  display: flex;
  height: 100vh;
  justify-content: center;
  align-items: flex-start;

}

/* BACKDROP */
.product-dialog-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  width: 100vw;
  max-height: 100vh;
  justify-content: center;
  align-items: flex-start;
  z-index: 99999;
  overflow: hidden;
}

/* Dialog general */
.product-dialog {
  position: relative;
  background-color: #ffffff;
  border-radius: 0.3rem;
  max-width: 1024px;
  width: 100%;
  
  max-height: calc(100vh - 2rem);
  margin: auto;
  padding: 2rem;
  box-shadow: 0 25px 80px rgba(15, 23, 42, 0.45);
  animation: fadeIn 0.15s ease-out;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Botón cerrar */
.dialog-close-btn {
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  position: absolute;
  right: 1rem;
  top: 1rem;
  border-radius: 0.3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 900;
  background-color: #00000000;
  color: #ffffff;
  font-weight: bold;
  font-size: 1.2rem;
  cursor: pointer;
}

.dialog-close-btn:hover {
  background-color: #dc2626;
}

/* Header */
.dialog-header {
  display: flex;
  justify-content: space-between;
  background-color: #ffffff;
  z-index: 99;
  height: min-content;
  padding: 0 1rem;
  margin-bottom: 1rem;
  flex: 0 0 auto;
}

.product-name {
  color: #000;
  font-weight: bold;
  text-transform: uppercase;
  font-size: 1.2rem;
  padding: 0;
  margin: 0;
  width: 75%;
  text-align: left;
}

.header-price-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.product-price {
  color: #000;
  font-weight: bold;
  text-transform: uppercase;
  padding: 0;
  font-size: 1.4rem;
  margin: 0;
  margin-left: 1rem;
  width: max-content;
  text-align: right;
}

.product-price--old {
  font-size: 0.9rem;
  color: #6b7280;
  text-decoration: line-through;
  opacity: 0.7;
}

/* Cuerpo */
.dialog-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  padding: 0;
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

/* Imagen */
.photo {
  display: flex;
  align-items: flex-start;
  max-height: 45rem;
  min-width: 100%;
  background-color: #ffffff;
  border-radius: 0.5rem;
  position: sticky;
  top: 0;
}

.photo-img {
  width: 100%;
  min-width: 100%;
  border-radius: 0.5rem;
  background-color: #ffffff;
  object-fit: cover;
  aspect-ratio: 1 / 1;
}

/* Lado derecho */
.dialog-content-right {
  display: flex;
  flex-direction: column;
  min-height: 100.075%;
}

/* Descripción */
.section-title {
  font-weight: bold;
  color: #000;
  margin: 1rem 0;
}

.section-text {
  color: #000;
  margin: 1rem 0;
}

/* GRUPOS DE MODIFICADORES */
.addition-group {
  margin-bottom: 1.5rem;
}

.addition-group-title {
  margin: 1rem 0;
  text-align: start;
}

.addition-group-list {
  margin-top: 0.5rem;
}

.addition-item-row {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.addition-checkbox {
  margin: 0.25rem 0;
  width: 1rem;
  height: 1rem;
}

.addition-item-content {
  display: flex;
  width: 100%;
  gap: 1rem;
  justify-content: space-between;
  align-items: center;
}

.addition-name {
  font-size: 0.875rem;
  text-transform: lowercase;
}

.addition-actions {
  display: flex;
  align-items: center;
}

.addition-price {
  padding-left: 0.5rem;
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
  font-size: 0.875rem;
}

.addition-qty-buttons {
  display: flex;
  align-items: center;
  margin-left: 0.5rem;
}

.qty-btn {
  width: 2rem;
  height: 1.5rem;
  border: none;
  font-weight: bold;
  border-radius: 0.2rem;
  background-color: #ef4444;
  color: #ffffff;
  cursor: pointer;
  font-size: 0.9rem;
  line-height: 1;
}

.qty-btn:hover {
  background-color: #dc2626;
}

.qty-input {
  width: 2rem;
  border: none;
  height: 1.5rem;
  padding: 0;
  text-align: center;
  font-size: 0.85rem;
}

/* INCLUYE */
.includes-title {
  padding: 1rem 0;
}

.product-base-grid {
  display: grid;
  gap: 1rem;
  padding: 0rem;
  grid-template-columns: repeat(1, 1fr);
}

.product-base-item {
  display: flex;
  border-radius: 0.5rem;
  background-color: #fff;
  flex-direction: column;
}

.product-base-item-header {
  display: flex;
  gap: 1rem;
  align-items: center;
  position: relative;
  border-radius: 0.5rem;
}

.product-base-qty {
  max-width: 100%;
  min-width: max-content;
}

.product-base-img {
  width: 4rem;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  box-shadow: 0rem 0rem 1rem #00000080;
  border-radius: 0.5rem;
}

.product-base-desc {
  max-width: 100%;
  text-transform: uppercase;
}

.product-base-change-btn {
  background-color: black;
  max-width: min-content;
  border: none;
  color: white;
  padding: 0.25rem 0.6rem;
  border-radius: 0.3rem;
  font-size: 0.75rem;
  cursor: pointer;
}

/* FOOTER */
.dialog-footer {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
  align-items: stretch;
  gap: 0.75rem;
  flex: 0 0 auto;
}

.add-to-cart-btn {
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

.add-to-cart-btn:hover {
  filter: brightness(1.05);
}

.footer-nav-btn {
  border: none;
  border-radius: 0.3rem;
  padding: 0.6rem 0.8rem;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  cursor: pointer;
  background-color: var(--primary-color, #b91c1c);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.footer-nav-btn__icon {
  font-size: 1.3rem;
}

/* Cantidad */
.cart-addition-quantity-label {
  width: 3rem;
  height: 1.5rem;
  font-weight: bold;
  text-align: center;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cart-addition-quantity-control {
  border: 1px solid var(--primary-color);
  align-items: center;
  display: flex;
  height: 100%;
  overflow: hidden;
  border-radius: 0.3rem;
}

.cart-addition-quantity-btn-minus,
.cart-addition-quantity-btn-plus {
  border: none;
  width: 2.5rem;
  height: 100%;
  background-color: var(--primary-color);
  color: #ffffff;
  font-weight: bold;
  cursor: pointer;
}

/* Flechas flotantes desktop */
.dialog-nav-btn {
  border: none;
  border-radius: 50%;
  height: 2rem;
  width: 2rem;
  padding: 0;
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  cursor: pointer;
  background-color: #ffffff;
  color: #000000;
  z-index: 901;
}

.dialog-nav-btn__icon {
  font-size: 1.5rem;
}

.dialog-nav-btn--left {
  left: 2rem;
  top: 50%;
  transform: translateY(-50%);
}

.dialog-nav-btn--right {
  right: 2rem;
  top: 50%;
  transform: translateY(-50%);
}

/* MINI DIALOG CAMBIO BASE */
.change-base-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 99999;
}

.change-base-dialog {
  background-color: #ffffff;
  border-radius: 0.75rem;
  padding: 1rem 1.2rem;
  max-width: 22rem;
  width: 100%;
  max-height: 80vh;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.45);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.change-base-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.change-base-title {
  margin: 0;
  font-size: 0.9rem;
}

.change-base-close {
  margin-left: auto;
  border: none;
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  background-color: #ef4444;
  color: white;
  font-weight: bold;
  cursor: pointer;
}

.change-base-options {
  margin-top: 0.5rem;
  display: grid;
  gap: 0.75rem;
}

.change-option-card {
  border: none;
  padding: 0.4rem;
  border-radius: 0.5rem;
  background-color: #ffffff;
  box-shadow: 0 0 1rem #00000030;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.change-option-img {
  width: 140px;
  height: 140px;
  padding: 10px;
  border-radius: 0.5rem;
  object-fit: contain;
}

.change-option-text {
  margin: 0.4rem 0 0;
  font-size: 0.85rem;
  text-align: center;
}

/* Animaciones */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.cargado {
  opacity: 0;
  animation: fadeIn 0.1s ease-out forwards;
}

.adicion::first-letter {
  text-transform: uppercase;
}

.text-description::first-letter {
  text-transform: uppercase;
}

/* Responsive */
@media (max-width: 1070px) {
  .dialog-body {
    grid-template-columns: 1fr;
    max-width: 40rem;
    margin: 0 auto;
  }

  .main {
    max-width: 40rem;
  }

  .photo {
    position: static;
  }

  .product-name {
    font-size: 1rem;
  }

  .dialog-header {
    padding-inline: 0.5rem;
  }

  .dialog-close-btn {
    right: 0.5rem;
    top: 0.5rem;
  }
}

/* Móvil */
@media (max-width: 768px) {
  .main {
    padding: 0;
    align-items: stretch;
  }

  .product-dialog {
    max-width: 100vw;
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    margin: 0;
    border-radius: 0;
    padding: 0;
  }

  .dialog-body {
    padding: 0 0.75rem 0.75rem 0.75rem;
    max-width: 100%;
  }

  .dialog-header {
    padding: 0.75rem;
    margin-bottom: 0;
  }

  .dialog-footer {
    padding: 0.75rem;
    margin: 0;
  }

  .dialog-close-btn {
    display: none;
  }

  .dialog-nav-btn {
    display: none;
  }

  .dialog-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .add-to-cart-btn {
    flex: 1;
    text-align: center;
  }
}

/* Scrollbars ocultos */
*::-webkit-scrollbar {
  display: none;
}
</style>
