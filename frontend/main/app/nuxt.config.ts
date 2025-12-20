// https://nuxt.com/docs/api/configuration/nuxt-config
import Aura from '@primevue/themes/aura';

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  
  // Agregamos el módulo de PrimeVue
  modules: [
    '@nuxt/eslint', 
    '@nuxt/image', 
    '@nuxt/ui', 
    '@primevue/nuxt-module'
  ],

  css: ['~/assets/base.css'],

  // Configuración de PrimeVue
  primevue: {
    options: {
      ripple: true, // Efecto de onda al hacer click
      inputVariant: 'filled', // Opcional: Estilo de inputs ('filled' o 'outlined')
      theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.my-app-dark', // O 'system'
            cssLayer: {
                name: 'primevue',
                order: 'tailwind-base, primevue, tailwind-utilities'
            }
        }
      }
    },
    
    components: {
        // Esto permite usar <Select> en lugar de <p-select> si prefieres
        // PrimeVue intenta auto-importar todo lo que uses.
        prefix: '', 
        exclude: ['Chart'] // Excluir componentes pesados si no los usas
    }
  }
})