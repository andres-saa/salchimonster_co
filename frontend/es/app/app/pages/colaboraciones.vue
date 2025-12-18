<!-- components/PrePagoVideo.vue -->
<template>
  <section class="prepago-wrapper">
    <div class="prepago-container">
      <div class="prepago-header">
        <p class="prepago-tagline">LA PRE-PAGO</p>
        <p class="prepago-title">SALCHIMONSTER X PAPI KEICY</p>
        <div class="prepago-divider">
          <span></span>
        </div>
      </div>

      <!-- Video de YouTube -->
      <div class="video-container">
        <iframe
          class="video-iframe"
          :src="embedUrl"
          title="Como hacer la salchipapa Pre-pago | Colaboración ​⁠​⁠@papi-keicy salchimonster la mejor de Colombia"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerpolicy="strict-origin-when-cross-origin"
          allowfullscreen
          loading="lazy"
        ></iframe>
      </div>
    </div>
  </section>
</template>

<script setup>
const videoId = 'VR6N9AhyRVQ' // ID del video
const embedUrl = `https://www.youtube.com/embed/${videoId}`
</script>

<style scoped>
/* Fondo general del bloque */
.prepago-wrapper {
  width: 100%;
  background: radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent),
    var(--p-primary-color, #1a1a1a);
  padding: 2.5rem 1rem 3rem;
  position: absolute;
  left: 0;
  display: flex;
  justify-content: center;
  min-height: 100vh;
}

/* Contenedor central */
.prepago-container {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  text-align: center;
  color: #ffffff;
}

/* Cabecera de textos */
.prepago-header {
  margin-bottom: 2rem;
}

.prepago-tagline {
  text-transform: uppercase;
  font-family: 'Titan One', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-weight: 400;
  letter-spacing: 0.12em;
  font-size: 1.1rem;
  margin: 0;
  color: #ffe35c;
}

.prepago-title {
  text-transform: uppercase;
  font-family: 'Titan One', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-weight: 400;
  font-size: 1.8rem;
  margin: 0.4rem 0 0.5rem;
  color: #ffffff;
}

/* Línea decorativa */
.prepago-divider {
  display: flex;
  justify-content: center;
  margin-top: 0.8rem;
}

.prepago-divider span {
  width: 120px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #ffe35c, #ff6a3d, #ff2b6a);
  box-shadow: 0 0 12px rgba(255, 106, 61, 0.6);
}

/* Contenedor del video, con card */
.video-container {
  margin: 2rem auto 0;
  border-radius: 1rem;
  padding: 0.5rem;
  background: linear-gradient(145deg, rgba(0, 0, 0, 0.65), rgba(255, 255, 255, 0.06));
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  max-width: 960px;
}

/* iframe responsivo */
.video-iframe {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0.8rem;
  border: none;
}

/* Responsive: pantallas medianas */
@media (min-width: 768px) {
  .prepago-wrapper {
    padding: 3rem 1.5rem 3.5rem;
  }

  .prepago-tagline {
    font-size: 1.2rem;
  }

  .prepago-title {
    font-size: 2.4rem;
  }

  .video-container {
    padding: 0.75rem;
  }
}

/* Responsive: pantallas grandes */
@media (min-width: 1024px) {
  .prepago-title {
    font-size: 3rem;
  }

  .prepago-tagline {
    font-size: 1.3rem;
  }

  .prepago-container {
    max-width: 1040px;
  }
}

/* Responsive: pantallas pequeñas */
@media (max-width: 480px) {
  .prepago-wrapper {
    padding: 2rem 0.75rem 2.5rem;
  }

  .prepago-title {
    font-size: 1.5rem;
  }

  .prepago-tagline {
    font-size: 1rem;
  }

  .video-container {
    margin-top: 1.5rem;
    padding: 0.4rem;
  }
}
</style>
