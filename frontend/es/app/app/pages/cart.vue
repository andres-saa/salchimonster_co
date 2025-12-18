<template>
  <div class="cart-wrapper">
    
    <div class="header-section" v-if="store.cart.length > 0">
      <h1 class="page-title">Tu carrito</h1>
      <p class="subtitle">{{ store.cart.length }} items agregados</p>
    </div>

    <div class="cart-container" v-if="store.cart.length > 0">
      
      <div class="cart-items-column">
        <TransitionGroup name="list">
          <div
            class="product-card"
            v-for="product in store.cart"
            :key="product.pedido_productoid || product.signature"
          >
            <div class="product-main-content">
              
              <div class="product-image-wrapper">
                <img
                  class="product-img"
                  :src="`https://img.restpe.com/${product.productogeneral_urlimagen}`"
                  :alt="product.pedido_nombre_producto"
                  loading="lazy"
                />
              </div>

              <div class="product-details">
                <div class="product-header">
                  <h3 class="product-name">
                    {{ formatName(product.pedido_nombre_producto) }}
                  </h3>
                  
                  <button
                    class="btn-delete desktop-only"
                    @click="store.removeProductFromCart(product.signature)"
                    title="Eliminar producto"
                  >
                    <Icon name="mdi:trash-can-outline" />
                  </button>
                </div>

                <div class="product-actions">
                  <div class="qty-control">
                    <button 
                      class="qty-btn" 
                      @click="store.decrementProduct(product.signature)"
                    >
                      <Icon name="mdi:minus" size="14" />
                    </button>
                    <span class="qty-display">{{ product.pedido_cantidad }}</span>
                    <button 
                      class="qty-btn" 
                      @click="store.incrementProduct(product.signature)"
                    >
                      <Icon name="mdi:plus" size="14" />
                    </button>
                  </div>

                  <div class="price-display">
                    <span 
                      v-if="product.pedido_descuento > 0" 
                      class="price-old"
                    >
                      {{ formatoPesosColombianos(product.pedido_precio * product.pedido_cantidad) }}
                    </span>
                    <span class="price-final">
                      {{ formatoPesosColombianos((product.pedido_precio - product.pedido_descuento) * product.pedido_cantidad) }}
                    </span>
                  </div>
                </div>
              </div>

              <button
                class="btn-delete mobile-only"
                @click="store.removeProductFromCart(product.signature)"
              >
                <Icon name="mdi:close" />
              </button>
            </div>

            <div
              v-if="product.modificadorseleccionList?.length > 0"
              class="additions-section"
            >
              <div class="additions-header">
                <span>Adicionales y cambios</span>
              </div>

              <div
                class="addition-row"
                v-for="item in product.modificadorseleccionList"
                :key="item.modificadorseleccion_id || item.id"
              >
                <div class="addition-info">
                  <span class="addition-qty-badge">{{ item.modificadorseleccion_cantidad }}x</span>
                  <span class="addition-name">
                    {{ formatName(item.modificadorseleccion_nombre) }}
                  </span>
                </div>

                <div class="addition-actions">
                  <span v-if="item.pedido_precio > 0" class="addition-price">
                    + {{ formatoPesosColombianos(item.pedido_precio * item.modificadorseleccion_cantidad * product.pedido_cantidad) }}
                  </span>
                  
                  <div class="qty-control small">
                    <button 
                      class="qty-btn" 
                      @click="store.decrementAdditional(product.signature, item)"
                    >
                      <Icon name="mdi:minus" size="10" />
                    </button>
                    <span class="qty-display">
                      {{ item.modificadorseleccion_cantidad * product.pedido_cantidad }}
                    </span>
                    <button 
                      class="qty-btn" 
                      @click="store.incrementAdditional(product.signature, item)"
                    >
                      <Icon name="mdi:plus" size="10" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <div class="cart-summary-column">
        <div class="summary-wrapper sticky-content">
          <resumen />
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon-bg">
        <Icon name="mdi:cart-outline" class="empty-icon" />
      </div>
      <h2 class="empty-title">Tu carrito está vacío</h2>
      <p class="empty-text">¡Antójate de algo delicioso y agrégalo aquí!</p>
      <NuxtLink to="/" class="btn-primary">
        Ir al menú
      </NuxtLink>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeMount } from 'vue'
import { usecartStore, useSitesStore, useUserStore } from '#imports'
import { formatoPesosColombianos } from '@/service/utils/formatoPesos'

const store = usecartStore()
const siteStore = useSitesStore()
const user = useUserStore()

// --- FUNCIÓN HELPER PARA TEXTO (Sentence case) ---
const formatName = (str) => {
  if (!str) return ''
  const lower = str.toLowerCase()
  return lower.charAt(0).toUpperCase() + lower.slice(1)
}

onBeforeMount(() => {
  if (!siteStore.location.site?.site_id) {
    siteStore.visibles.currentSite = true
  }
})

// Lógica de actualización (Manteniendo tu lógica original)
const update = () => { /* Hook para recalcular si es necesario */ }

watch(() => store.cart?.additions, () => update(), { deep: true })

onMounted(async () => {
  if (user.user.payment_method_option?.productogeneral_id != 7) {
    siteStore.setNeighborhoodPrice()
  } else {
    siteStore.setNeighborhoodPriceCero()
  }
})
</script>

<style scoped>
/* --- VARIABLES --- */
.cart-wrapper {
  --primary: #000000;
  --bg-page: #f9fafb; /* Fondo gris muy suave para la página */
  --bg-card: #ffffff;
  --text-main: #1f2937;
  --text-muted: #6b7280;
  --border: #e5e7eb;
  --danger: #ef4444;
  --danger-bg: #fef2f2;
  --radius: 12px;
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
  min-height: 80vh;
}

/* --- HEADER --- */
.header-section {
  text-align: center;
  margin-bottom: 2.5rem;
}
.page-title {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 0.2rem;
}
.subtitle {
  color: var(--text-muted);
  font-size: 0.95rem;
}

/* --- GRID LAYOUT --- */
.cart-container {
  display: grid;
  grid-template-columns: 1.6fr 1fr; /* 60% productos, 40% resumen */
  gap: 2.5rem;
  align-items: start;
}

/* --- TARJETA DE PRODUCTO --- */
.product-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  margin-bottom: 1.5rem;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative; /* Para botón mobile */
}

.product-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

.product-main-content {
  padding: 1.25rem;
  display: flex;
  gap: 1.25rem;
  align-items: center;
}

/* Imagen */
.product-image-wrapper {
  flex-shrink: 0;
}
.product-img {
  width: 5.5rem;
  height: 5.5rem;
  object-fit: cover;
  border-radius: 50%; /* Manteniendo tu estilo redondo */
  border: 2px solid #f3f4f6;
}

/* Detalles */
.product-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.product-name {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.3;
  margin: 0;
  /* FormatName se encarga del texto, pero aseguramos estilo base */
}

/* Acciones (Cantidad y Precio) */
.product-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Control de Cantidad (Pill) */
.qty-control {
  display: inline-flex;
  align-items: center;
  background: #f3f4f6;
  border-radius: 99px;
  padding: 2px;
}

.qty-control.small {
  padding: 1px;
  background: #ffffff;
  border: 1px solid var(--border);
}

.qty-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  color: var(--text-main);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  transition: all 0.2s;
}

.qty-control.small .qty-btn {
  width: 24px;
  height: 24px;
  background: #f9fafb;
  box-shadow: none;
  border: 1px solid transparent;
}

.qty-btn:active { transform: scale(0.9); }
.qty-btn:hover { background: var(--primary); color: white; }

.qty-display {
  font-weight: 700;
  min-width: 30px;
  text-align: center;
  font-size: 0.9rem;
}
.qty-control.small .qty-display { font-size: 0.8rem; min-width: 24px; }

/* Precios */
.price-display {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.price-old {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-decoration: line-through;
}
.price-final {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-main);
}

/* Botón Eliminar */
.btn-delete {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-delete:hover {
  background-color: var(--danger-bg);
  color: var(--danger);
}

/* --- ADICIONALES --- */
.additions-section {
  background-color: #f8fafc;
  border-top: 1px solid var(--border);
  padding: 0.75rem 1.25rem;
}

.additions-header {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.addition-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.addition-info {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  color: var(--text-main);
}
.addition-qty-badge {
  font-weight: 700;
  font-size: 0.8rem;
  background: #e2e8f0;
  padding: 1px 6px;
  border-radius: 4px;
}

.addition-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.addition-price {
  font-size: 0.85rem;
  font-weight: 600;
}

/* --- EMPTY STATE --- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 1rem;
  text-align: center;
}
.empty-icon-bg {
  width: 100px;
  height: 100px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}
.empty-icon { font-size: 3rem; color: var(--text-muted); opacity: 0.5; }
.empty-title { font-size: 1.5rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.5rem; }
.empty-text { color: var(--text-muted); margin-bottom: 2rem; }

.btn-primary {
  background: var(--primary);
  color: white;
  padding: 12px 24px;
  border-radius: 50px;
  text-decoration: none;
  font-weight: 600;
  transition: transform 0.2s;
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

/* --- RESPONSIVE UTILS --- */
.mobile-only { display: none; }
.sticky-content { position: sticky; top: 1rem; }

/* Animación de lista */
.list-enter-active, .list-leave-active { transition: all 0.3s ease; }
.list-enter-from, .list-leave-to { opacity: 0; transform: translateX(-20px); }

/* --- MEDIA QUERIES --- */
@media (max-width: 900px) {
  .cart-container {
    grid-template-columns: 1fr; /* Una columna */
    gap: 1.5rem;
  }
  
  .desktop-only { display: none; }
  .mobile-only { display: flex; position: absolute; top: 0.5rem; right: 0.5rem; }

  .product-main-content {
    padding: 1rem;
    gap: 1rem;
  }

  .product-header {
    padding-right: 1.5rem; /* Espacio para la X de cerrar */
  }

  .product-img {
    width: 4rem;
    height: 4rem;
  }

  .qty-btn {
    width: 36px; /* Más grande para el dedo */
    height: 36px;
  }
}
</style>