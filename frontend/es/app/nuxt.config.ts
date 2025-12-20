import Aura from '@primevue/themes/aura'; // 1. Importar el tema

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  build: {
    transpile: ['i18n-iso-countries']
  },

  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/ui',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
    '@primevue/nuxt-module' // 2. Agregar el módulo oficial
  ],

  // 3. Agregar CSS de PrimeIcons para que funcionen los iconos internos de los componentes
  css: [
    '~/assets/base.css',
    'primeicons/primeicons.css' 
  ],

  // 4. Configuración de PrimeVue
  primevue: {
    options: {
      theme: {
        preset: Aura, // Usa el tema Aura
        options: {
            darkModeSelector: '.dark', // Sincroniza el modo oscuro con Nuxt UI
        }
      },
      ripple: true // Efecto de onda en botones
    },
    autoImport: true // Importa componentes automáticamente (ej: <Button>, <InputText>)
  },

  fonts: {
    families: [
      {
        name: 'Roboto',
        provider: 'google',
        weights: [400, 500, 700],
        styles: ['normal'],
        subsets: ['latin'],
      },
    ],
  },

  runtimeConfig: {
    apiSecret: process.env.API_SECRET || 'dev-secret',
    public: {
      apiBase: process.env.API_BASE_URL || 'http://localhost:8000',
      googleMapsKey: process.env.NUXT_PUBLIC_GOOGLE_MAPS_KEY || '',
    },
  },

  // routeRules: {
  //   '/': { isr: 600 },
  //   '/sedes': { isr: 10 },
  //   '/pqr': { isr: 3600 } ,
  //   '/_nuxt/**': { headers: { 'cache-control': 's-maxage=31536000' } },
  // },

  image: {
    domains: [
      'img.restpe.com', 
      'backend.salchimonster.com',
      'gestion.salchimonster.com' 
    ],
    format: ['avif', 'webp'],
    quality: 75,
    screens: {
      'xs': 320,
      'sm': 640,
      'md': 768,
      'lg': 1024,
      'xl': 1280,
      'xxl': 1536
    },
    densities: [1, 2],
    presets: {
      default: {
        modifiers: {
          loading: 'lazy',
          fit: 'cover',
        }
      }
    }
  }
})