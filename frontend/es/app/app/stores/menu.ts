// stores/menu.ts
import { defineStore } from 'pinia'

interface MenuPayload {
  categorias: any[]
  [key: string]: any
}

interface MenuEntry {
  data: MenuPayload
  updatedAt: number
}

export const useMenuStore = defineStore('menu', {
  state: () => ({
    menusBySite: {} as Record<number, MenuEntry>
  }),

  getters: {
    getMenuBySite: (state) => (siteId: number) =>
      state.menusBySite[siteId]?.data || null,

    getUpdatedAtBySite: (state) => (siteId: number) =>
      state.menusBySite[siteId]?.updatedAt || 0
  },

  actions: {
    setMenuForSite(siteId: number, data: MenuPayload) {
      const now = Date.now()
      const current = this.menusBySite[siteId]   // 👈 aquí va this, NO state

      if (!current || now >= current.updatedAt) {
        this.menusBySite[siteId] = {
          data,
          updatedAt: now
        }
      }
    }
  },

  // 🔒 Persistencia: pinia-plugin-persistedstate
  persist: {
    key: 'menu-store',
    paths: ['menusBySite']
  }
})
