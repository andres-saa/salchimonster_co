// server/api/s-count.post.ts
export default defineEventHandler(async (event) => {
  const body = (await readBody(event).catch(() => null)) as any
  const slug = String(body?.slug || '').trim()
  const device = String(body?.device || '').trim()

  if (!slug || slug.length > 80) {
    setResponseStatus(event, 400)
    return { ok: false, error: 'slug requerido' }
  }
  if (!device || device.length < 16 || device.length > 128) {
    setResponseStatus(event, 400)
    return { ok: false, error: 'device requerido' }
  }

  const BACKEND_DATA_BASE = 'https://backend.salchimonster.com/data/'
  const STATS_PREFIX = 'url_shortener_v1_stats_'
  const statsUrl = `${BACKEND_DATA_BASE}${STATS_PREFIX}${slug}`

  const NOW = Date.now()
  const TWELVE_HOURS = 12 * 60 * 60 * 1000
  const PRUNE_AFTER = 30 * 24 * 60 * 60 * 1000 // 30 días
  const MAX_DEVICES = 2000 // cap para no inflar JSON

  const dayKey = new Date().toISOString().slice(0, 10) // YYYY-MM-DD

  // ---- Load current stats (best-effort) ----
  let stats: any = null
  try {
    const res: any = await $fetch(statsUrl)
    stats = res?.data?.stats || null
  } catch {
    stats = null
  }

  if (!stats) {
    stats = {
      slug,
      total: 0,     // ✅ TODOS los clicks (incluye repetidos)
      unique: 0,    // ✅ clicks únicos (regla 12h por device)
      devices: {},  // { [deviceHash]: lastUniqueAtMs }
      daily: {},    // { "YYYY-MM-DD": { total: n, unique: n } } últimos 30 días
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastHitAt: null
    }
  }

  if (!stats.devices || typeof stats.devices !== 'object') stats.devices = {}
  if (!stats.daily || typeof stats.daily !== 'object') stats.daily = {}

  // ---- Prune devices viejos (30 días) ----
  for (const [k, v] of Object.entries(stats.devices)) {
    const t = Number(v || 0)
    if (!t || (NOW - t) > PRUNE_AFTER) delete stats.devices[k]
  }

  // ---- Prune daily viejo (30 días) ----
  for (const [k, v] of Object.entries(stats.daily)) {
    const dt = Date.parse(String(k) + 'T00:00:00Z')
    if (!dt || (NOW - dt) > PRUNE_AFTER) delete stats.daily[k]
    else {
      // saneo básico
      if (!v || typeof v !== 'object') stats.daily[k] = { total: 0, unique: 0 }
      stats.daily[k].total = Number(stats.daily[k]?.total || 0)
      stats.daily[k].unique = Number(stats.daily[k]?.unique || 0)
    }
  }

  // ---- Always count TOTAL (repetidos incluidos) ----
  stats.total = Number(stats.total || 0) + 1
  stats.lastHitAt = new Date().toISOString()
  stats.updatedAt = new Date().toISOString()

  if (!stats.daily[dayKey]) stats.daily[dayKey] = { total: 0, unique: 0 }
  stats.daily[dayKey].total = Number(stats.daily[dayKey].total || 0) + 1

  // ---- Unique rule (12h per device) ----
  const lastUniqueAt = Number(stats.devices[device] || 0)
  const canCountUnique = !lastUniqueAt || (NOW - lastUniqueAt) >= TWELVE_HOURS

  let countedUnique = false
  if (canCountUnique) {
    stats.unique = Number(stats.unique || 0) + 1
    stats.devices[device] = NOW
    stats.daily[dayKey].unique = Number(stats.daily[dayKey].unique || 0) + 1
    countedUnique = true
  }

  // ---- Cap devices to MAX_DEVICES (keep most recent) ----
  const entries = Object.entries(stats.devices)
  if (entries.length > MAX_DEVICES) {
    entries.sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0))
    stats.devices = Object.fromEntries(entries.slice(0, MAX_DEVICES))
  }

  // ---- Save (best-effort) ----
  try {
    await $fetch(statsUrl, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: { stats }
    })
    alert('hola')
  } catch {
    // si falla guardar: NO rompas el redirect, igual responde
  }

  return {
    ok: true,
    total: Number(stats.total || 0),
    unique: Number(stats.unique || 0),
    repeated: Math.max(0, Number(stats.total || 0) - Number(stats.unique || 0)),
    countedUnique
  }
})
