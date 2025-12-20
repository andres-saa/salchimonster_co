// https://nuxt.com/docs/api/configuration/nuxt-config

import Aura from '@primeuix/themes/aura';


export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/eslint', '@nuxt/image', '@nuxt/ui','@primevue/nuxt-module'],
  css: ['~/assets/base.css'],
  
  primevue: {
        options: {
            theme: {
                preset: Aura
            }
        },
        components: {
        include: ['Button', 'DataTable', 'Select']
    }
    },
    
})