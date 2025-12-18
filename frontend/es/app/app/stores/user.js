import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore(
  'user',
  () => {
    const user = ref({
      name: '',
      neigborhood: '',
      address: '',
      phone_number: '',
      payment_method_option: '',
    })

    // getter "a mano"
    function fucion() {
      return 0
    }

    // helpers útiles
    function setUser(partial) {
      user.value = {
        ...user.value,
        ...partial,
      }
    }

    function resetUser() {
      user.value = {
        name: '',
        neigborhood: '',
        address: '',
        phone_number: '',
        payment_method_option: '',
      }
    }

    return {
      user,
      fucion,
      setUser,
      resetUser,
    }
  },
  {
    // persistencia al estilo pinia-plugin-persistedstate
    persist: {
      key: 'user',
      paths: ['user'],
      // si usas @pinia-plugin-persistedstate/nuxt puedes agregar:
      // storage: persistedState.localStorage,
    },
  },
)
