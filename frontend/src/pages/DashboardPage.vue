<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createApiClient } from '@/services/api-client.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const nomeUsuario = ref('')
const token = ref('')
const carregando = ref(false)
const mensagemFormulario = ref('')
const mensagemErro = ref(false)
const form = ref({
  destino: '',
  motivo: '',
  data_ida: '',
  data_volta: '',
})

function hidratarSessaoLegada() {
  const legacyToken = window.localStorage.getItem('token')
  const legacyNome = window.localStorage.getItem('nome_usuario')
  if (legacyToken && !authStore.getToken()) authStore.setToken(legacyToken)
  if (legacyNome && !authStore.nome) authStore.setNome(legacyNome)
}

function logout() {
  authStore.clearAll()
  window.localStorage.removeItem('token')
  window.localStorage.removeItem('nome_usuario')
  window.localStorage.removeItem('perfil')
  router.push('/')
}

const apiClient = createApiClient({
  baseUrl: '',
  getToken: () => token.value,
  onUnauthorized: () => logout(),
})

async function criarSolicitacao() {
  carregando.value = true
  mensagemFormulario.value = ''
  mensagemErro.value = false

  try {
    const payload = {
      ...form.value,
      data_ida: new Date(form.value.data_ida).toISOString(),
      data_volta: form.value.data_volta ? new Date(form.value.data_volta).toISOString() : null,
    }

    const dados = await apiClient.requestJson('/api/v1/viagens/solicitacoes', {
      method: 'POST',
      body: JSON.stringify(payload),
    })

    mensagemFormulario.value = `Solicitação #${dados.id} para ${dados.destino} criada com sucesso!`
    form.value = { destino: '', motivo: '', data_ida: '', data_volta: '' }
  } catch (err) {
    mensagemErro.value = true
    mensagemFormulario.value = err?.message || 'Falha ao criar solicitação.'
  } finally {
    carregando.value = false
  }
}

onMounted(() => {
  hidratarSessaoLegada()

  const tokenSalvo = authStore.getToken()
  const nomeSalvo = authStore.nome || 'Colaborador'
  if (!tokenSalvo) {
    router.push('/')
    return
  }

  token.value = tokenSalvo
  nomeUsuario.value = nomeSalvo
  authStore.setToken(tokenSalvo)
  authStore.setNome(nomeSalvo)
})
</script>

<template>
  <div class="min-h-screen bg-gray-100 vl-font-inter">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        <h1 class="text-2xl font-bold text-blue-600">Viagens<span class="text-yellow-500">Labs</span></h1>
        <div class="flex items-center gap-3">
          <span class="text-gray-600">Olá, {{ nomeUsuario || 'Colaborador' }}</span>
          <button
            type="button"
            class="bg-red-500 hover:bg-red-600 text-white text-sm font-bold py-2 px-3 rounded"
            @click="logout"
          >
            Sair
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <section class="bg-white p-6 rounded-lg shadow mb-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Nova Solicitação de Viagem</h2>

        <div
          v-if="mensagemFormulario"
          class="p-3 mb-4 text-sm rounded"
          :class="mensagemErro ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'"
        >
          {{ mensagemFormulario }}
        </div>

        <form @submit.prevent="criarSolicitacao">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700" for="dash-destino">Destino</label>
              <input
                id="dash-destino"
                v-model="form.destino"
                type="text"
                required
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700" for="dash-motivo">Motivo</label>
              <input
                id="dash-motivo"
                v-model="form.motivo"
                type="text"
                required
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700" for="dash-ida">Data de Ida</label>
              <input
                id="dash-ida"
                v-model="form.data_ida"
                type="datetime-local"
                required
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700" for="dash-volta">Data de Volta</label>
              <input
                id="dash-volta"
                v-model="form.data_volta"
                type="datetime-local"
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
            </div>
          </div>
          <div class="mt-6 text-right">
            <button
              type="submit"
              :disabled="carregando"
              class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
            >
              <span v-if="carregando">Enviando...</span>
              <span v-else>Enviar Solicitação</span>
            </button>
          </div>
        </form>
      </section>

      <section class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Minhas Solicitações</h2>
        <p class="text-gray-500">Em breve: aqui você verá o histórico de suas viagens.</p>
      </section>
    </main>
  </div>
</template>
