<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia' // 1. Importar storeToRefs
import { useSitesStore } from '#imports'
import { useUserStore } from '#imports'


const user = useUserStore()
const siteStore = useSitesStore()

// 2. Extraer 'location' manteniendo la reactividad
const { location } = storeToRefs(siteStore)

const cityConfig = ref<any[]>([])
const loading = ref(true)

const API_URL = 'https://api.locations.salchimonster.com/data/cities_google_map_status'

onMounted(async () => {
  try {
    const res = await fetch(API_URL)
    const json = await res.json()
    if (json?.data?.cities) {
      cityConfig.value = json.data.cities
    }
  } catch (error) {
    console.error('Error cargando configuración de mapas:', error)
  } finally {
    loading.value = false
  }
})

// Computada corregida
const shouldUseGoogleMaps = computed(() => {
  // 3. Usamos location.value (ahora es una ref reactiva)
  // El ?. evita errores si location o site son nulos
  const currentCityId = location.value?.site?.city_id 

  if (!currentCityId) return false 

  // Asegurarnos que cityConfig ya cargó
  if (cityConfig.value.length === 0) return false

  const config = cityConfig.value.find(c => Number(c.city_id) === Number(currentCityId))

  return config ? Boolean(config.user_google_map_status) : false
})
</script>

<template>
  <div>
    <SiteDialog />

    <!-- <div style="font-size: 10px; color: gray;">
       Debug: ID Ciudad: {{ location?.site?.city_id }} | Google: {{ shouldUseGoogleMaps }}
    </div> -->

    <div v-if="loading" class="loading-container">
      <p>Cargando...</p>
    </div>

    <div v-else>
      <paycGoogle />
      <!-- <paycBarrios v-else /> -->
    </div>


  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  padding: 2rem;
  color: #666;
  font-family: 'Inter', sans-serif;
}
</style>