<template>
  <div
    v-if="route.path === '/' || route.path === '/kids'"
    class="fixed-cart-bar background"
    :style="
      route.path !== '/kids'
        ? 'background: linear-gradient(to top, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0));'
        : ''
    "
  >
    <div
      v-if="store.cart.length > 0"
      @click="enviarAlCarro"
      :class="['cart-bar', { hidden: !showElement }]"
    >
      <button class="cart-button">
        <i class="cart-icon icono pi pi-shopping-cart"></i>

        <div
          v-for="product in store.cart.slice(0, 4)"
          :key="product.id"
          class="product-item"
        >
          <!-- Badge nativo, sin PrimeVue -->
          <span class="quantity-button">
            {{ product.pedido_cantidad }}
          </span>

          <img
            class="img-cart"
            @mouseover="() => (vueMenu = true)"
            :src="`${URI}/get-image?image_url=${product.productogeneral_urlimagen}`"
            alt="Product Image"
          />
        </div>

        <div v-if="store.cart.length > 4" class="extra-products">
          <p class="extra-products-text">
            +{{ store.cart.length - 4 }}
          </p>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from '#imports'
import { usecartStore } from '#imports'
import { URI } from '@/service/conection'

const store = usecartStore()
const route = useRoute()
const router = useRouter()

const showElement = ref(true)
const vueMenu = ref(false)

let scrollTimer

const handleScroll = () => {
  showElement.value = false
  clearTimeout(scrollTimer)
  scrollTimer = setTimeout(() => {
    showElement.value = true
  }, 200)
}

onMounted(() => {
  if (process.client) {
    window.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (process.client) {
    window.removeEventListener('scroll', handleScroll)
  }
  clearTimeout(scrollTimer)
})

const enviarAlCarro = () => {
  router.push('/cart')
}
</script>

<style scoped>
/* Container for the fixed cart bar */
.fixed-cart-bar {
  display: flex;
  cursor: pointer;
  position: fixed;
  bottom: 0;
  left: 0;
  justify-content: center;
  width: 100%;
  padding: 0 1rem;
  z-index: 999;
}

/* Cart bar styling */
.cart-bar {
  display: flex;
  gap: 2rem;
  border-radius: 1rem 1rem 0 0;
  align-items: center;
  position: relative;
  z-index: 1000;
  max-width: 30rem;
  width: 100%;
  justify-content: center;
  height: 3.5rem;
  background-color: #ffffff;
  box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.2);
  padding: 0 3rem;
  transition: transform 0.2, opacity 0.2;
}

/* Hidden state for cart bar */
.hidden {
  transform: translateY(5rem);
  opacity: 0;
}

/* Cart button styling */
.cart-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background-color: transparent;
  border: none;
  cursor: pointer;
}

/* Cart icon styling */
.cart-icon {
  font-size: 2rem;
  color: var(--p-primary-color);
}

/* Individual product item */
.product-item {
  position: relative;
}

/* Quantity badge styling (nativo) */
.quantity-button {
  width: 1.4rem;
  height: 1.4rem;
  font-size: 0.8rem;
  position: absolute;
  top: -0.3rem;
  right: -0.5rem;
  background-color: rgb(255, 0, 0);
  color: white;
  font-weight: bold;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Product image styling */
.img-cart {
  height: 3rem;
  object-fit: contain;
  transition: all 0.2 ease;
}

/* Extra products indicator */
.extra-products {
  width: auto;
  border-radius: 50%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.extra-products-text {
  font-weight: bold;
  font-size: 1.25rem;
}

/* Background gradient */
.background {
}

/* Transition for all elements */
* {
  transition: all 0.2s ease;
}

/* Hover effects */
.cart-button:hover .cart-icon {
  color: var(--p-primary-color);
}

/* Responsive adjustments */
@media (min-width: 767px) {
  .cart-bar {
    padding: 0 4rem;
  }
}
</style>
