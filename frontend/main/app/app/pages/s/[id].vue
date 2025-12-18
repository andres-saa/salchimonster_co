<template>
  <div class="wrap">
    <div class="card">
      <div class="logo">S</div>
      <h1>Redirigiendo…</h1>

      <p v-if="state === 'loading'">Estamos buscando tu link.</p>
      <p v-else-if="state === 'counting'">Validando visita…</p>
      <p v-else-if="state === 'redirecting'">Enviándote al destino…</p>
      <p v-else class="error">{{ errorMsg }}</p>

      <div v-if="targetUrl" class="small">
        Destino: <span class="mono">{{ safeShortUrl(targetUrl) }}</span>
      </div>

      <div v-if="state === 'error' && targetUrl" class="actions">
        <a class="btn" :href="targetUrl">Abrir manualmente</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'

const route = useRoute()

// === Estados de la UI ===
const state = ref<'loading' | 'counting' | 'redirecting' | 'error'>('loading')
const errorMsg = ref('No pudimos redirigirte.')
const targetUrl = ref<string>('')

// === Configuración ===
const slug = computed(() => String(route.params.id || '').trim())
const BACKEND_DATA_BASE = 'https://backend.salchimonster.com/data/'
const LINK_DB_PREFIX = 'url_shortener_v1_'
const STATS_DB_PREFIX = 'url_shortener_v1_stats_'

// URLs de acceso a datos
const linkDocUrl = (s: string) => `${BACKEND_DATA_BASE}${LINK_DB_PREFIX}${s}`
const statsDocUrl = (s: string) => `${BACKEND_DATA_BASE}${STATS_DB_PREFIX}${s}`

// === Helpers ===
const safeShortUrl = (u: string) => {
  try {
    const url = new URL(u)
    return url.hostname + (url.pathname && url.pathname !== '/' ? url.pathname : '')
  } catch { return u }
}
const isValidUrl = (u: string) => { try { new URL(u); return true } catch { return false } }

/**
 * Obtiene la fecha y hora actual en zona horaria Colombia
 * Retorna objeto con formato YYYY-MM-DD para la llave y string completo para log
 */
const getColombiaData = () => {
  const now = new Date()
  // Forzamos la zona horaria a Bogotá
  const coString = now.toLocaleString('en-US', { timeZone: 'America/Bogota' })
  const coDate = new Date(coString)

  const year = coDate.getFullYear()
  const month = String(coDate.getMonth() + 1).padStart(2, '0')
  const day = String(coDate.getDate()).padStart(2, '0')
  
  // Formato de hora militar HH:MM:SS
  const time = coDate.toLocaleTimeString('en-GB', { hour12: false }) 

  return {
    dateKey: `${year}-${month}-${day}`, // Para agrupar: "2025-12-17"
    fullTimestamp: `${year}-${month}-${day} ${time}` // Para log: "2025-12-17 14:30:05"
  }
}

// === 1. Obtener el Link (Server Side Friendly) ===
const { data, error } = await useAsyncData(`shortlink_${slug.value}`, async () => {
  if (!slug.value) return null
  const res: any = await $fetch(linkDocUrl(slug.value))
  return res?.data?.link ?? null
}, { server: true })

if (error.value || !data.value) {
  state.value = 'error'
  errorMsg.value = 'Este link no existe o está caído.'
} else {
  const link = data.value as any
  if (link?.deletedAt) {
    state.value = 'error'
    errorMsg.value = 'Este link fue eliminado.'
  } else if (!link?.url || !isValidUrl(link.url)) {
    state.value = 'error'
    errorMsg.value = 'El link no tiene un destino válido.'
  } else {
    targetUrl.value = link.url
    state.value = 'loading'
  }
}

// === 2. Lógica de Conteo y Redirección (CLIENT SIDE ONLY) ===
onMounted(async () => {
  if (!targetUrl.value || state.value === 'error') return

  state.value = 'counting'

  try {
    await processStats(slug.value)
  } catch (e) {
    console.error('Error stats:', e)
  }

  state.value = 'redirecting'
  window.location.replace(targetUrl.value)
})

const processStats = async (slugId: string) => {
  const STORAGE_KEY = `sm_last_visit_${slugId}`
  const TWELVE_HOURS = 12 * 60 * 60 * 1000
  const NOW = Date.now()

  // === AQUI OBTENEMOS LA HORA COLOMBIA ===
  const { dateKey, fullTimestamp } = getColombiaData()

  // 1. Verificar LocalStorage
  const lastVisit = Number(localStorage.getItem(STORAGE_KEY) || 0)
  const isUnique = !lastVisit || (NOW - lastVisit) > TWELVE_HOURS

  // 2. Obtener estadísticas
  const url = statsDocUrl(slugId)
  let stats: any = null
  
  try {
    const res: any = await $fetch(url)
    stats = res?.data?.stats || null
  } catch {
    stats = null
  }

  if (!stats) {
    stats = {
      slug: slugId,
      total: 0,
      unique: 0,
      daily: {}, 
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  }
  
  if (!stats.daily) stats.daily = {}

  // 3. Actualizar contadores
  stats.total = Number(stats.total || 0) + 1
  stats.updatedAt = new Date().toISOString() // Mantenemos ISO para sistema
  stats.lastClickCO = fullTimestamp // <--- GUARDAMOS HORA COLOMBIA LEGIBLE

  // Inicializar día actual (Usando fecha Colombia)
  if (!stats.daily[dateKey]) {
    stats.daily[dateKey] = { total: 0, unique: 0 }
  }
  stats.daily[dateKey].total = Number(stats.daily[dateKey].total || 0) + 1

  if (isUnique) {
    stats.unique = Number(stats.unique || 0) + 1
    stats.daily[dateKey].unique = Number(stats.daily[dateKey].unique || 0) + 1
    localStorage.setItem(STORAGE_KEY, String(NOW))
  }

  // 4. Limpieza (Pruning)
  const PRUNE_AFTER = 30 * 24 * 60 * 60 * 1000
  Object.keys(stats.daily).forEach(k => {
    const dt = Date.parse(k)
    if (dt && (NOW - dt) > PRUNE_AFTER) delete stats.daily[k]
  })

  // 5. Guardar
  await $fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: { stats }
  })
}
</script>

<style scoped>
/* Tus estilos existentes... */
.wrap{ min-height: 100vh; display:flex; align-items:center; justify-content:center; background:#f1f5f9; padding:24px; font-family: Inter, sans-serif; }
.card{ width:100%; max-width:520px; background:white; border:1px solid #e2e8f0; border-radius:16px; box-shadow: 0 10px 30px rgba(2,6,23,0.08); padding:22px; text-align:center; }
.logo{ width:44px;height:44px; border-radius:12px; margin:0 auto 10px auto; display:flex;align-items:center;justify-content:center; background:#4f46e5;color:white; font-weight:900; }
h1{ margin: 8px 0 6px 0; font-size: 1.1rem; }
p{ margin: 0; color:#64748b; }
.small{ margin-top: 14px; font-size: 0.85rem; color:#64748b; }
.mono{ font-family: monospace; }
.error{ color:#b91c1c; font-weight:700; margin-top: 10px; }
.actions{ margin-top: 14px; }
.btn{ display:inline-block; background:#0f172a; color:white; text-decoration:none; padding:10px 14px; border-radius:12px; font-weight:800; }
</style>