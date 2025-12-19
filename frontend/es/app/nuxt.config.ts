export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  // 1. ELIMINA 'i18n-iso-countries' de aquí. Deja transpile vacío o con tus otras libs.
  build: {
    transpile: [] 
  },
  
  // 2. AGREGA este alias para asegurar que apunte al archivo principal correcto
  alias: {
    'i18n-iso-countries': 'i18n-iso-countries/index.js'
  },

  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/ui',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
  ],
  
  sourcemap: {
    server: false,
    client: false
  },

  css: ['~/assets/base.css'],

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

  // 3. BORRA el bloque 'vite' que te di antes (ignoreDynamicRequires...).
  // El bloque 'image' se queda igual.
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