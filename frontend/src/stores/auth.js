import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * Store de autenticação — substitui VLAuthSession (window global).
 * Namespaced por 'portal' para compatibilidade com legado.
 */
export const useAuthStore = defineStore('auth', () => {
    const STORAGE_PREFIX = 'vl:portal:'

    // --- state ---
    const token = ref(localStorage.getItem(`${STORAGE_PREFIX}token`) ?? '')
    const nome = ref(localStorage.getItem(`${STORAGE_PREFIX}nome`) ?? '')
    const perfil = ref(localStorage.getItem(`${STORAGE_PREFIX}perfil`) ?? '')
    const username = ref(localStorage.getItem(`${STORAGE_PREFIX}username`) ?? '')

    // --- getters ---
    const isAuthenticated = computed(() => Boolean(token.value))

    // --- actions ---
    function setToken(value) {
        token.value = value
        localStorage.setItem(`${STORAGE_PREFIX}token`, value)
    }

    function setNome(value) {
        nome.value = value
        localStorage.setItem(`${STORAGE_PREFIX}nome`, value)
    }

    function setPerfil(value) {
        perfil.value = value
        localStorage.setItem(`${STORAGE_PREFIX}perfil`, value)
    }

    function setUsername(value) {
        username.value = value
        localStorage.setItem(`${STORAGE_PREFIX}username`, value)
    }

    function getToken() {
        return token.value
    }

    function clearAll() {
        token.value = ''
        nome.value = ''
        perfil.value = ''
        username.value = ''
        const keysToRemove = Object.keys(localStorage).filter(k =>
            k.startsWith(STORAGE_PREFIX),
        )
        keysToRemove.forEach(k => localStorage.removeItem(k))
    }

    return {
        token,
        nome,
        perfil,
        username,
        isAuthenticated,
        getToken,
        setToken,
        setNome,
        setPerfil,
        setUsername,
        clearAll,
    }
})
