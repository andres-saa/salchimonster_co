import Aura from '@primeuix/themes/aura';
import { definePreset } from '@primeuix/themes';


const MyPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#fff7ed',
      100: '#ffedd5',
      200: '#fed7aa',
      300: '#fdba74',
      400: '#fb923c',
      500: '#f97316', // TU COLOR PRINCIPAL
      600: '#ea580c',
      700: '#c2410c',
      800: '#9a3412',
      900: '#7c2d12',
      950: '#431407'
    }
  }
});




export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  build: {
    transpile: ['i18n-iso-countries']
  },
  
  modules: [
    '@nuxt/eslint',
    '@nuxt/image', // Asegúrate de usar <NuxtImg> en lugar de <img> en tus componentes
    '@nuxt/ui',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
    '@primevue/nuxt-module'

  ],
  primevue: {
        options: {
            theme: {
                preset: MyPreset
            }, 
            darkModeSelector: false,

        },
      
        components: {
        include: ['Button', 'DataTable', 'Select']
    }
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

  // 🧊 ISR / SWR: Configuración de caché
  routeRules: {
    // Home se regenera cada 10 min
    '/': { isr: 600 },
    // Sedes se regenera cada 10 min (600s)
    '/sedes': { isr: 10 },
 
    // Reemplaza '/ayuda' por la ruta donde usas este componente
    '/pqr': { isr: 3600 } ,
 
    // Opcional: Cachear assets estáticos agresivamente
    '/_nuxt/**': { headers: { 'cache-control': 's-maxage=31536000' } },
  },

  // 🖼️ OPTIMIZACIÓN EXTREMA DE IMÁGENES
  image: {
    // Dominios externos permitidos para optimización.
    // IMPORTANTE: Agregué el dominio de tu backend que vi en el código anterior.
    domains: [
      'img.restpe.com', 
      'backend.salchimonster.com',
      'gestion.salchimonster.com' 
    ],
    
    // Prioridad: AVIF (más ligero) -> WebP (estándar) -> JPG/PNG (fallback)
    format: ['avif', 'webp'],
    
    // Calidad 75 es el punto dulce entre peso visual y tamaño de archivo.
    // 80 suele ser demasiado alto para web móvil.
    quality: 75,
    
    // Generación de tamaños responsivos exactos
    screens: {
      'xs': 320,
      'sm': 640,
      'md': 768,
      'lg': 1024,
      'xl': 1280,
      'xxl': 1536
    },
    
    // Evita generar imágenes 3x innecesarias que consumen datos
    densities: [1, 2],
    
    // Configuración predeterminada para el componente <NuxtImg>
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