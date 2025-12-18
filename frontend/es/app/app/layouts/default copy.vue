<template>
  <div class="app-layout">
    <!-- TOPBAR: PUEDE CRECER A TODO EL ANCHO -->
    <header class="app-layout__topbar">
      <TopBar />
    </header>

    <!-- CONTENEDOR LIMITADO (SIDEBAR + CONTENIDO) -->
    <div class="app-layout__shell">
      <aside class="app-layout__sidebar">
        <Sidebar />
      </aside>

      <main class="app-layout__content">
        <slot />
      </main>
    </div>


  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  /* max-height: 100vh; */
  position: relative;
  background-color: #f5f5f5;
}

/* TOPBAR FULL-WIDTH */
.app-layout__topbar {
  flex: 0 0 auto;
  position: sticky;
  top: 0;
  z-index: 20;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* SHELL: por defecto ocupa el 100% del ancho (hasta 2K) */
.app-layout__shell {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  display: flex;
}

/* En pantallas MÁS GRANDES que 2K, limitamos a 1920px y centramos */
@media (min-width: 2049px) {
  .app-layout__shell {
    max-width: 1920px;
    margin: 0 auto;
  }
}

/* === SIDEBAR === */
.app-layout__sidebar {
  width: 260px;
  background-color: #111827;
  color: #fff;
  overflow-y: auto;
  max-height: 100vh;
  position: fixed;
  top: 3rem;
  /* 🔹 Ocultar scrollbar (Chrome, Edge, Safari) */
  scrollbar-width: none;     /* Firefox */
  -ms-overflow-style: none;  /* IE/Edge antiguo */
}
.app-layout__sidebar::-webkit-scrollbar {
  display: none;             /* WebKit */
}

/* === CONTENIDO === */
.app-layout__content {
 
  padding: 0;
  padding-left: 260px;
}

/* === RESPONSIVE === */
@media (max-width: 768px) {
  .app-layout {
    max-height: none;
  }

  .app-layout__shell {
    flex-direction: column;
    max-width: 100%;
    position: relative;
  }

  /* 🔹 Sidebar oculta a la izquierda en móviles */
  .app-layout__sidebar {
    position: fixed;
    top: 0;           /* si tu topbar tiene altura fija, aquí la puedes compensar */
    left: 0;
    height: 100vh;
    max-height: 100vh;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 30;
  }

  /* Contenido ocupa todo el ancho */
  .app-layout__content {
    padding: 0;
    overflow-y: visible;
  }
}
</style>
