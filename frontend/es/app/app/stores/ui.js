// stores/ui.js
import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', {
  state: () => ({
    isSearchOpen: false
  }),
  actions: {
    toggleSearch() {
      this.isSearchOpen = !this.isSearchOpen
    },
    openSearch() {
      this.isSearchOpen = true
    },
    closeSearch() {
      this.isSearchOpen = false
    }
  }
})