<!-- components/SonandoPlayerSite1.vue -->
<template>


<div>


  <!-- Fondo borroso con el thumbnail de la canción actual -->
  <img
    style="position: fixed; left: -10%; top: 0; width: 120vw; height: 100vh; object-fit: cover; z-index: -1; filter: blur(10px);"
    :src="currentPlayback?.currentSong?.thumbnail"
    alt=""
  />

  <div class="main-container">
    <div class="salchimonster-container" style="overflow: hidden;">
      <h2 style="margin:0 2rem 0 1rem;">
        <Icon name="mdi:play" style="margin-right: 1rem;" />
        SONANDO EN
        <span>SM {{ siteStore?.sonando?.site_name || 'SITE 1' }}</span>
      </h2>

      <div style="display: flex; gap: 1rem; justify-content: center;">
        <button
          class="btn"
          type="button"
          @click="dialogPedirTema = true"
          style="margin: 1rem 0;"
        >
          <Icon name="mdi:skip-forward" class="btn-icon" />
          Pedir tema
        </button>
      </div>

      <!-- YouTube Player -->
      <div class="player-wrapper" style="pointer-events: none;">
        <div
          ref="playerElement"
          style="width: 100% !important; max-width: 100% !important;"
          id="youtube-player"
        ></div>
      </div>

      <!-- Info canción actual -->
      <div v-if="currentPlayback?.currentSong" class="current-song-info">
        <h2>{{ currentPlayback.currentSong.title }}</h2>
        <p><strong>Solicitada por:</strong> {{ currentPlayback.currentSong.requestedBy }}</p>
      </div>

      <!-- Barra de progreso -->
      <div class="progress-bar-container">
        <div class="progress-bar">
          <div class="progress-bar-fill" :style="{ width: progressValue + '%' }"></div>
        </div>
      </div>

      <!-- Controles -->
      <div class="controls-container">
        <button class="icon-button" type="button" disabled>
          <Icon name="mdi:skip-backward" />
        </button>

        <button
          v-if="!isLocalPaused"
          class="control-button"
          type="button"
          @click="pausePlayback"
        >
          <Icon name="mdi:pause" class="button-icon" />
          <span>Pausa</span>
        </button>
        <button
          v-else
          class="control-button"
          type="button"
          @click="resumePlayback"
        >
          <Icon name="mdi:play" class="button-icon" />
          <span>Reanudar</span>
        </button>

        <button
          class="icon-button"
          type="button"
          disabled
          @click="advanceToNextSong"
        >
          <Icon name="mdi:skip-forward" />
        </button>
      </div>

      <!-- Cola -->
      <div class="queue-container">
        <h3>Cola de Reproducción</h3>
        <ul class="queue-list">
          <li
            v-for="(song, index) in displayedQueue"
            :key="`${song.id}-${index}`"
            :class="['song', { 'current-song': (startIndex + index) === currentPlayback?.currentIndex }]"
            :style="{ opacity: getOpacity(index), transition: 'opacity 0.5s ease' }"
          >
            <img :src="song.thumbnail" alt="Thumbnail" class="thumbnail" />
            <div class="song-info">
              <span class="song-title">{{ song.title }}</span>
              <span class="requested-by">Solicitada por: {{ song.requestedBy }}</span>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Dialog: Solicitar Tema -->
  <div v-if="dialogPedirTema" class="dialog-overlay">
    <div class="dialog-box" style="max-width: 94%; width: 40rem; min-height: 90vh;">
      <header class="dialog-header">
        <h4 style="color: black;">Solicitar una Canción</h4>
        <div style="margin-top: 1rem;">
          <!-- Input único para canciones locales e YouTube -->
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Buscar canción..."
            style="width: 100%; color: black; padding: .5rem; border-radius: 6px; border: 1px solid #ccc;"
          />
        </div>
      </header>

      <section class="dialog-body">
        <!-- Si hay canciones locales filtradas -->
        <div v-if="filteredSongs.length > 0">
          <ul class="queue-list">
            <li
              class="song"
              style="transition: all none;"
              v-for="(song, index) in songsPaginated"
              :key="`${song.id}-${index}`"
              :class="{ 'selected-song': selectedAvailableSong === song }"
              @click="selectedAvailableSong = song"
            >
              <img :src="song.thumbnail" alt="Thumbnail" class="thumbnail" />
              <div class="song-info">
                <span style="color: black !important;">{{ song.title }}</span>
              </div>
            </li>
          </ul>

          <!-- Paginación -->
          <div
            style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;"
          >
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="currentPage === 0"
              @click="goToPrevPage"
            >
              <Icon name="mdi:chevron-left" /> Anterior
            </button>

            <span style="color: black !important;">
              {{ currentPage + 1 }} de {{ totalPages }}
            </span>

            <button
              type="button"
              class="btn btn-secondary"
              :disabled="currentPage >= totalPages - 1"
              @click="goToNextPage"
            >
              Siguiente <Icon name="mdi:chevron-right" />
            </button>
          </div>
        </div>

        <!-- Si NO hay locales pero sí resultados de YouTube -->
        <div v-else-if="youtubeSearchResults.length > 0">
          <p style="color: black; font-weight: bold;">Resultados de YouTube:</p>
          <ul class="queue-list">
            <li
              class="song"
              style="transition: all none;"
              v-for="(song, index) in youtubeSearchResults"
              :key="index"
              :class="{ 'selected-song': selectedYoutubeSong === song }"
              @click="selectedYoutubeSong = song"
            >
              <img :src="song.thumbnail" alt="Thumbnail" class="thumbnail" />
              <div class="song-info">
                <span style="color: black !important;">{{ song.title }}</span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Si no hay nada aún -->
        <div v-else>
          <h3 style="color: black;">
            No hay resultados, la estamos buscando en Youtube... espera un poco
          </h3>
          <div class="status-tag">
            <h2>Buscando en YouTube, ya casi la tengo...</h2>
          </div>
        </div>
      </section>

      <footer class="dialog-footer">
        <button
          type="button"
          class="btn btn-text"
          @click="dialogPedirTema = false"
        >
          Cancelar
        </button>

        <!-- Local -->
        <button
          v-if="filteredSongs.length > 0"
          type="button"
          class="btn"
          :disabled="!selectedAvailableSong"
          @click="openSolicitarNombreDialog"
        >
          <Icon name="mdi:check" class="btn-icon" />
          Solicitar
        </button>

        <!-- YouTube -->
        <button
          v-else-if="youtubeSearchResults.length > 0"
          type="button"
          class="btn"
          :disabled="!selectedYoutubeSong"
          @click="openSolicitarNombreDialogYouTube"
        >
          <Icon name="mdi:check" class="btn-icon" />
          Solicitar
        </button>
      </footer>
    </div>
  </div>

  <!-- Dialog: Nombre para canción local -->
  <div v-if="dialogSolicitarNombre" class="dialog-overlay">
    <div class="dialog-box" style="max-width: 94%; width: 30rem;">
      <header class="dialog-header">
        <h2 style="color: black;">Proporciona tu Nombre</h2>
      </header>

      <section class="dialog-body">
        <div class="solicitar-nombre-container">
          <h3 style="color: black !important;">{{ selectedAvailableSong?.title }}</h3>
          <img :src="selectedAvailableSong?.thumbnail" alt="Thumbnail" class="thumbnail-large" />
          <input
            type="text"
            style="width: 100%; color: black; padding: .5rem; border-radius: 6px; border: 1px solid #ccc;"
            v-model="requesterName"
            placeholder="Tu nombre"
          />
        </div>
      </section>

      <footer class="dialog-footer">
        <button
          type="button"
          class="btn btn-text"
          @click="dialogSolicitarNombre = false"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="btn"
          :disabled="!requesterName.trim()"
          @click="handleAddSongWithName"
        >
          <Icon name="mdi:check" class="btn-icon" />
          Solicitar
        </button>
      </footer>
    </div>
  </div>

  <!-- Dialog: Nombre para canción de YouTube -->
  <div v-if="dialogSolicitarNombreYouTube" class="dialog-overlay">
    <div class="dialog-box" style="max-width: 94%; width: 30rem;">
      <header class="dialog-header">
        <h2 style="color: black;">Proporciona tu Nombre</h2>
      </header>

      <section class="dialog-body">
        <div class="solicitar-nombre-container">
          <h3 style="color: black !important;">{{ selectedYoutubeSong?.title }}</h3>
          <img :src="selectedYoutubeSong?.thumbnail" alt="Thumbnail" class="thumbnail-large" />
          <input
            type="text"
            style="width: 100%; color: black; padding: .5rem; border-radius: 6px; border: 1px solid #ccc;"
            v-model="requesterNameYouTube"
            placeholder="Tu nombre"
          />
        </div>
      </section>

      <footer class="dialog-footer">
        <button
          type="button"
          class="btn btn-text"
          @click="dialogSolicitarNombreYouTube = false"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="btn"
          :disabled="!requesterNameYouTube.trim()"
          @click="handleAddYoutubeSongWithName"
        >
          <Icon name="mdi:check" class="btn-icon" />
          Solicitar
        </button>
      </footer>
    </div>
  </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
 import { usecartStore } from '#imports'

const API_BASE = 'https://backend-musica.salchimonster.com'
const WS_BASE = 'wss://backend-musica.salchimonster.com/ws'
const SITE_ID = 1

const siteStore = useSitesStore()

// Dialog refs
const dialogPedirTema = ref(false)
const dialogSolicitarNombre = ref(false)
const dialogSolicitarNombreYouTube = ref(false)

// Playback control
const isLocalPaused = ref(true)

function pausePlayback() {
  if (player && playerState.isPlayerReady) {
    player.pauseVideo()
    isLocalPaused.value = true
  }
}
function resumePlayback() {
  if (player && playerState.isPlayerReady && currentPlayback.value) {
    player.seekTo(currentPlayback.value.currentTime || 0, true)
    player.playVideo()
    isLocalPaused.value = false
  }
}

// Selected songs + requesters
const selectedAvailableSong = ref(null)
const requesterName = ref('')
const selectedYoutubeSong = ref(null)
const requesterNameYouTube = ref('')

// Input único
const searchTerm = ref('')

// debounce para YouTube
let searchDebounce = null

// Canciones disponibles localmente
const availableSongs = ref([])

const filteredSongs = computed(() => {
  const term = searchTerm.value.toLowerCase()
  if (!term) return availableSongs.value
  return availableSongs.value.filter(song =>
    song.title.toLowerCase().includes(term)
  )
})

// Paginación
const currentPage = ref(0)
const itemsPerPage = 100
const totalPages = computed(() =>
  filteredSongs.value.length
    ? Math.ceil(filteredSongs.value.length / itemsPerPage)
    : 1
)

function goToNextPage() {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++
  }
}
function goToPrevPage() {
  if (currentPage.value > 0) {
    currentPage.value--
  }
}
const songsPaginated = computed(() => {
  const start = currentPage.value * itemsPerPage
  const end = start + itemsPerPage
  return filteredSongs.value.slice(start, end)
})

// Resultados de YouTube
const youtubeSearchResults = ref([])

// watcher de búsqueda
watch(searchTerm, () => {
  youtubeSearchResults.value = []
  currentPage.value = 0
  clearTimeout(searchDebounce)

  if (!searchTerm.value.trim()) return

  searchDebounce = setTimeout(() => {
    if (filteredSongs.value.length === 0) {
      searchOnYouTube(searchTerm.value.trim())
    }
  }, 2000)
})

async function searchOnYouTube(query) {
  try {
    if (!query) return
    const resp = await fetch(`${API_BASE}/search_youtube?q=${encodeURIComponent(query)}`)
    if (!resp.ok) throw new Error('Error al buscar en YouTube')
    youtubeSearchResults.value = await resp.json()
  } catch (error) {
    console.error('Error al buscar en YouTube:', error)
    alert('No se pudieron obtener resultados de YouTube.')
  }
}

// abrir dialogs de nombre
function openSolicitarNombreDialog() {
  if (selectedAvailableSong.value) {
    dialogSolicitarNombre.value = true
  } else {
    alert('Por favor, selecciona una canción de la lista primero.')
  }
}
function openSolicitarNombreDialogYouTube() {
  if (selectedYoutubeSong.value) {
    dialogSolicitarNombreYouTube.value = true
  } else {
    alert('Por favor, selecciona una canción de los resultados de YouTube.')
  }
}

// WebSocket
let socket = null

async function handleAddSongWithName() {
  if (!selectedAvailableSong.value || !requesterName.value.trim()) {
    alert('Por favor, selecciona una canción y proporciona tu nombre.')
    return
  }
  try {
    const message = {
      type: 'add_song',
      song_id: selectedAvailableSong.value.id,
      requestedBy: requesterName.value.trim()
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
      selectedAvailableSong.value = null
      requesterName.value = ''
      dialogSolicitarNombre.value = false
      dialogPedirTema.value = false
    } else {
      alert('No estás conectado al servidor. Intenta recargar la página.')
    }
  } catch (error) {
    console.error('Error al agregar la canción a la cola:', error)
  }
}

async function handleAddYoutubeSongWithName() {
  if (!selectedYoutubeSong.value || !requesterNameYouTube.value.trim()) {
    alert('Por favor, selecciona una canción y proporciona tu nombre.')
    return
  }
  try {
    const message = {
      type: 'add_song_external',
      youtubeId: selectedYoutubeSong.value.videoId,
      title: selectedYoutubeSong.value.title,
      thumbnail: selectedYoutubeSong.value.thumbnail,
      requestedBy: requesterNameYouTube.value.trim()
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
      selectedYoutubeSong.value = null
      requesterNameYouTube.value = ''
      dialogSolicitarNombreYouTube.value = false
      dialogPedirTema.value = false
    } else {
      alert('No estás conectado al servidor. Intenta recargar la página.')
    }
  } catch (error) {
    console.error('Error al agregar la canción de YouTube a la cola:', error)
  }
}

// Estado de reproducción
const currentPlayback = ref(null)
const videoQueue = ref([])

const currentTime = ref(0)
const totalDuration = ref(0)

const playerState = reactive({
  isPlayerReady: false
})

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`
}
const formattedCurrentTime = computed(() => formatTime(currentTime.value))
const formattedTotalDuration = computed(() => formatTime(totalDuration.value))

const progressValue = computed(() => {
  if (totalDuration.value > 0) {
    return (currentTime.value / totalDuration.value) * 100
  }
  return 0
})

// Mostrar parte de la cola
const startIndex = computed(() => {
  if (!currentPlayback.value || currentPlayback.value.currentIndex === undefined) return 0
  return Math.max(currentPlayback.value.currentIndex - 4, 0)
})
const displayedQueue = computed(() => videoQueue.value.slice(startIndex.value))

function getOpacity(index) {
  const total = displayedQueue.value.length
  if (total === 1) return 1
  const minOpacity = 0.2
  const maxOpacity = 1
  const opacityRange = maxOpacity - minOpacity
  return minOpacity + (index / (total - 1)) * opacityRange
}

// YouTube Player
let player = null
const playerElement = ref(null)

function loadYouTubeAPI(onAPIReady) {
  if (typeof window === 'undefined') return
  if (window.YT && window.YT.Player) {
    onAPIReady()
    return
  }
  window.onYouTubeIframeAPIReady = () => {
    onAPIReady()
  }
  const tag = document.createElement('script')
  tag.src = 'https://www.youtube.com/iframe_api'
  document.body.appendChild(tag)
}

function createYouTubePlayer(element, videoId, onReady, onStateChange) {
  return new window.YT.Player(element, {
    videoId,
    playerVars: {
      autoplay: 1,
      controls: 1,
      disablekb: 0,
      fs: 1,
      playsinline: 1,
      iv_load_policy: 3,
      modestbranding: 1,
      rel: 0
    },
    events: {
      onReady,
      onStateChange
    }
  })
}

function onPlayerReady(event) {
  playerState.isPlayerReady = true
  if (currentPlayback.value?.isPlaying) {
    event.target.playVideo()
    if (currentTime.value > 0) {
      event.target.seekTo(currentTime.value, true)
    }
    isLocalPaused.value = false
  } else {
    event.target.pauseVideo()
    isLocalPaused.value = true
  }
}

function onPlayerStateChange(event) {
  if (typeof window === 'undefined' || !window.YT) return
  const PlayerState = window.YT.PlayerState
  switch (event.data) {
    case PlayerState.ENDED:
      advanceToNextSong()
      break
    case PlayerState.PAUSED:
      isLocalPaused.value = true
      break
    case PlayerState.PLAYING:
      isLocalPaused.value = false
      break
    default:
      break
  }
}

function loadCurrentSong(songId) {
  if (typeof window === 'undefined') return
  if (!songId) return
  if (!(window.YT && window.YT.Player)) return

  if (!player) {
    player = createYouTubePlayer(
      playerElement.value,
      songId,
      onPlayerReady,
      onPlayerStateChange
    )
  } else {
    player.loadVideoById({
      videoId: songId,
      startSeconds: currentTime.value || 0
    })
    if (currentPlayback.value?.isPlaying) {
      player.playVideo()
    } else {
      player.pauseVideo()
    }
  }
}

async function advanceToNextSong() {
  try {
    await fetch(`${API_BASE}/next/${SITE_ID}`, { method: 'POST' })
    // el backend enviará un queue_update por WS
  } catch (error) {
    console.error('Error al avanzar a la siguiente canción:', error)
  }
}

async function loadInitialData() {
  try {
    const [availableResp, queueResp, currentResp] = await Promise.all([
      fetch(`${API_BASE}/available`),
      fetch(`${API_BASE}/queue/${SITE_ID}`),
      fetch(`${API_BASE}/current/${SITE_ID}`)
    ])

    if (!availableResp.ok || !queueResp.ok || !currentResp.ok) {
      throw new Error('Error en las respuestas iniciales')
    }

    availableSongs.value = await availableResp.json()
    videoQueue.value = await queueResp.json()
    currentPlayback.value = await currentResp.json()

    currentTime.value = currentPlayback.value.currentTime || 0
    totalDuration.value = currentPlayback.value.totalDuration || 0

    if (currentPlayback.value.currentSong) {
      lastLoadedSongId.value = currentPlayback.value.currentSong.id
    }

    // Si la API de YouTube ya está cargada, cargamos la canción
    if (typeof window !== 'undefined' && window.YT && window.YT.Player && lastLoadedSongId.value) {
      loadCurrentSong(lastLoadedSongId.value)
    }
  } catch (error) {
    console.error('Error al cargar datos iniciales:', error)
  }
}

let lastLoadedSongId = ref(null)

function connectWebSocket() {
  if (typeof window === 'undefined') return

  if (socket) {
    socket.close()
    socket = null
  }

  const wsUrl = `${WS_BASE}/${SITE_ID}`
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    console.log(`Conectado al WebSocket de la sede: ${SITE_ID}`)
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'queue_update') {
        videoQueue.value = data.queue
        currentPlayback.value = data.status

        currentTime.value = data.status.currentTime
        totalDuration.value = data.status.totalDuration

        const currentSongId = data.status.currentSong ? data.status.currentSong.id : null
        if (currentSongId && currentSongId !== lastLoadedSongId.value) {
          lastLoadedSongId.value = currentSongId
          loadCurrentSong(currentSongId)
        }

        isLocalPaused.value = !data.status.isPlaying
      }
    } catch (error) {
      console.error('Error al parsear mensaje del WebSocket:', error)
    }
  }

  socket.onerror = (error) => {
    console.error('Error en el WebSocket:', error)
  }

  socket.onclose = () => {
    console.warn(`WebSocket cerrado para sede: ${SITE_ID}. Reintentando en 3s...`)
    setTimeout(() => {
      connectWebSocket()
    }, 3000)
  }
}

onMounted(async () => {
  await loadInitialData()

  connectWebSocket()

  loadYouTubeAPI(() => {
    if (lastLoadedSongId.value) {
      loadCurrentSong(lastLoadedSongId.value)
    }
  })
})

onUnmounted(() => {
  if (socket) {
    socket.close()
  }
})
</script>

<style scoped>
.salchimonster-container {
  max-width: 640px;
  padding-top: 3rem;
  margin: auto;
  padding: 20px;
  text-align: center;
}

* {
  color: white;
}

.player-wrapper {
  position: relative;
  width: 100%;
  margin-top: 1rem;
}

/* El iframe se ajusta al contenedor */
#youtube-player {
  position: relative;
  width: 100%;
  height: 56.25vw; /* 16:9 en función del ancho */
  max-height: 360px;
}

.current-song-info {
  margin-top: 20px;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

/* Barra de progreso nativa */
.progress-bar {
  width: 100%;
  height: 8px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background-color:var(--primary-color);
  width: 0;
  transition: width 0.3s ease;
}

.queue-container {
  margin-top: 30px;
  text-align: left;
}

.queue-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.queue-list li {
  display: flex;
  align-items: center;
  padding: 10px;
  transition: opacity 0.5s ease, background-color 0.3s ease;
  cursor: pointer;
}

.queue-list li.current-song {
  background-color: var(--primary-color, );
}

.queue-list li.selected-song {
  background-color:var(--primary-color);
  font-weight: bold;
}

.song:hover {
  background-color: rgba(0, 3, 182, 0.239);
}

.thumbnail {
  width: 80px;
  height: 60px;
  object-fit: cover;
  margin-right: 15px;
  border-radius: 4px;
}

.main-container {
  background-color: rgba(0, 0, 0, 0.591);
  min-height: 120vh;
  padding-top: 3rem;
  padding-bottom: 4rem;
}

.controls-container {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
  position: sticky;
  top: 0;
}

/* Botones básicos */
.btn {
  background-color:var(--primary-color);
  color: #ffffff;
  border: none;
  border-radius: 999px;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
}
.btn:hover {
  background-color: var(--primary-color);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-icon {
  font-size: 1.2rem;
}
.btn-secondary {
  background-color: #e0e0e0;
  color: #000;
}
.btn-text {
  background: transparent;
  color: #000;
  padding: 0.5rem 1rem;
}

.icon-button {
  background: rgba(0, 0, 0, 0.6);
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.icon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-button {
  background-color:var(--primary-color);
  color: #000;
  border-radius: 999px;
  border: none;
  padding: 0.4rem 1.1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
}
.control-button .button-icon {
  font-size: 1.3rem;
}

/* Dialogs nativos */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.dialog-box {
  background: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.4);
  max-height: 95vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  margin-bottom: 1rem;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  width: 100%;
  margin-top: 1.5rem;
}

.thumbnail-large {
  width: 100%;
  max-width: 300px;
  height: auto;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.solicitar-nombre-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

@media (max-width: 600px) {
  .solicitar-nombre-container {
    padding: 0 1rem;
  }
}

.status-tag {
  padding: 1rem;
  animation: anim_status_tag infinite 1s;
  color: black;
  background-color: rgba(255, 0, 0, 0.582);
  border-radius: 8px;
  margin-top: 1rem;
}

@keyframes anim_status_tag {
  20% {
    background-color: rgb(160, 45, 0);
  }
  50% {
    background-color: rgb(255, 115, 0);
  }
  80% {
    background-color: rgb(53, 0, 0);
  }
}
</style>
