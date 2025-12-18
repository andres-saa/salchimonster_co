// /stores/sidebar.ts (por ejemplo)
import { defineStore } from 'pinia'

export const useSidebarStore = defineStore('cart-bot', {
  state: () => ({
    side_bar_visible: false,
    visible_categoires: false
  }),

  actions: {
    toggle() {
      this.side_bar_visible = !this.side_bar_visible
      console.log('Sidebar visible:', this.side_bar_visible)
    },

    toggle_visible_categories() {
      this.visible_categoires = !this.visible_categoires
    }
  }
})
