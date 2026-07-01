<script setup>
import { onMounted, reactive, ref } from 'vue'
import { createApiClient } from '@/services/api-client.js'

const logoLuizalabs = new URL('../../img/luizalabs-logo.png', import.meta.url).href

const API = '/api/v1'

const tela = ref('token_carregando')
const agenciaNome = ref('')
const token = ref('')

const modoToken = ref(true)
const tokenUUID = ref('')
const tokenErro = ref('')

const solicitacoes = ref([])
const carregandoLista = ref(false)
const filtroStatus = ref('')
const solDetalhe = ref(null)

const formCotacao = reactive({
  aereo_companhia: '',
  aereo_numero_voo: '',
  aereo_horario_ida: '',
  aereo_horario_volta: '',
  aereo_valor: null,
  hotel_nome: '',
  hotel_categoria: '',
  hotel_valor_diaria: null,
  rodov_empresa: '',
  rodov_horario_ida: '',
  rodov_horario_volta: '',
  rodov_valor: null,
  carro_locadora: '',
  carro_modelo: '',
  carro_valor_diaria: null,
  valor_total: null,
  observacoes: '',
})

const enviandoCotacao = ref(false)
const cotacaoSucesso = ref(false)
const cotacaoErro = ref('')

const arquivosVoucher = reactive({})
const enviandoVoucher = reactive({})
const voucherSucesso = ref('')
const voucherErro = ref('')

const formCancelamento = reactive({
  taxa_cancelamento_agencia: 0,
  valor_reembolsavel_agencia: 0,
  valor_credito_gerado: 0,
  companhia_credito: '',
})
const arquivoCancelamento = ref(null)
const enviandoCancelamento = ref(false)

const apiClient = createApiClient({
  baseUrl: API,
  getToken: () => token.value || '',
  onUnauthorized: () => {
    if (!modoToken.value) sair()
  },
})

const tiposInfo = {
  aereo: { label: 'Passagem Aérea', icone: '✈' },
  hospedagem: { label: 'Hospedagem', icone: '🏨' },
  carro: { label: 'Locação de Carro', icone: '🚗' },
  rodoviario: { label: 'Transporte Rodoviário', icone: '🚌' },
}

const mapServico = {
  Aereo: 'aereo',
  Hospedagem: 'hospedagem',
  Carro: 'carro',
  Rodoviario: 'rodoviario',
}

function temServico(sol, servico) {
  return (sol?.tipo_servico || '')
    .split(',')
    .map(s => s.trim())
    .includes(servico)
}

function formatarData(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('pt-BR')
}

function formatarMoeda(val) {
  if (val == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)
}

function badgeStatus(s) {
  const mapa = {
    AGUARDANDO_COTACAO: 'bg-yellow-100 text-yellow-800',
    COTACAO_ENVIADA: 'bg-blue-100 text-blue-800',
    APROVADA_AGUARDANDO_VOUCHER: 'bg-purple-100 text-purple-800',
    CONCLUIDA: 'bg-green-100 text-green-800',
    REPROVADA: 'bg-red-100 text-red-700',
  }
  return mapa[s] || 'bg-gray-100 text-gray-600'
}

function labelStatus(s) {
  const mapa = {
    AGUARDANDO_COTACAO: 'Aguardando Cotação',
    COTACAO_ENVIADA: 'Cotação Enviada',
    APROVADA_AGUARDANDO_VOUCHER: '🎫 Aguardando Vouchers',
    CONCLUIDA: 'Concluída',
    AGUARDANDO_N1: 'Aguardando N1',
    AGUARDANDO_N2: 'Aguardando N2',
    REPROVADA: 'Reprovada',
  }
  return mapa[s] || s
}

function badgeCasamento(tipo) {
  const mapa = {
    TOTAL: 'bg-green-100 text-green-800',
    PARCIAL_A: 'bg-blue-100 text-blue-800',
    PARCIAL_B: 'bg-yellow-100 text-yellow-800',
  }
  return mapa[tipo] || 'bg-gray-100 text-gray-600'
}

function popularFormCotacao(cotacao) {
  if (!cotacao) return
  Object.keys(formCotacao).forEach(k => {
    if (cotacao[k] !== undefined) formCotacao[k] = cotacao[k]
  })
}

async function carregarPorToken(uuid) {
  tela.value = 'token_carregando'
  try {
    const res = await apiClient.request(`/agencia/token/${uuid}`, { auth: false })
    const dados = res.data || {}
    if (!res.ok) {
      tokenErro.value = dados.detail || 'Link inválido ou expirado.'
      tela.value = 'token_erro'
      return
    }
    agenciaNome.value = dados.agencia_nome
    solDetalhe.value = dados.solicitacao
    tela.value = 'detalhe'
  } catch {
    tokenErro.value = 'Erro de conexão. Tente novamente mais tarde.'
    tela.value = 'token_erro'
  }
}

async function carregarSolicitacoes() {
  carregandoLista.value = true
  try {
    const qs = filtroStatus.value ? `?status_filtro=${filtroStatus.value}` : ''
    const res = await apiClient.request(`/agencia/solicitacoes${qs}`)
    if (!res.ok) return
    solicitacoes.value = res.data || []
  } finally {
    carregandoLista.value = false
  }
}

async function abrirDetalhe(id) {
  solDetalhe.value = null
  cotacaoSucesso.value = false
  cotacaoErro.value = ''
  tela.value = 'detalhe'
  const res = await apiClient.request(`/agencia/solicitacoes/${id}`)
  const dados = res.data || {}
  if (!res.ok) {
    cotacaoErro.value = dados.detail || 'Erro ao carregar detalhe.'
    voltarLista()
    return
  }
  solDetalhe.value = dados
  Object.keys(formCotacao).forEach(k => {
    formCotacao[k] = null
  })
  formCotacao.observacoes = ''
  if (dados.cotacao) {
    popularFormCotacao(dados.cotacao)
    return
  }
  if (dados.aereo_periodo_preferido) formCotacao.aereo_horario_ida = dados.aereo_periodo_preferido
  if (dados.preferencia_voo) formCotacao.aereo_numero_voo = dados.preferencia_voo
  if (dados.preferencia_hotel_nome) formCotacao.hotel_nome = dados.preferencia_hotel_nome
  if (dados.rodov_tipo_onibus) formCotacao.rodov_empresa = dados.rodov_tipo_onibus
}

function voltarLista() {
  tela.value = 'lista'
  solDetalhe.value = null
  void carregarSolicitacoes()
}

async function enviarCotacao() {
  if (!solDetalhe.value) return
  enviandoCotacao.value = true
  cotacaoSucesso.value = false
  cotacaoErro.value = ''
  try {
    const url = modoToken.value
      ? `/agencia/token/${tokenUUID.value}/cotacao`
      : `/agencia/solicitacoes/${solDetalhe.value.id}/cotacao`
    const res = await apiClient.request(url, {
      method: 'POST',
      auth: !modoToken.value,
      body: JSON.stringify(formCotacao),
    })
    const dados = res.data || {}
    if (!res.ok) {
      cotacaoErro.value = dados.detail || 'Erro ao registrar cotação.'
      return
    }
    cotacaoSucesso.value = true
    solDetalhe.value.cotacao = dados
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch {
    cotacaoErro.value = 'Erro de conexão com o servidor.'
  } finally {
    enviandoCotacao.value = false
  }
}

function tiposVoucherNecessarios(sol) {
  return (sol?.tipo_servico || '')
    .split(',')
    .map(s => s.trim())
    .filter(s => mapServico[s])
    .map(s => ({ valor: mapServico[s], ...tiposInfo[mapServico[s]] }))
}

function selecionarArquivoVoucher(event, tipo) {
  arquivosVoucher[tipo] = event.target.files?.[0] || null
}

async function uploadVoucher(tipo) {
  const arquivo = arquivosVoucher[tipo]
  if (!arquivo || !solDetalhe.value) return
  enviandoVoucher[tipo] = true
  voucherSucesso.value = ''
  voucherErro.value = ''
  try {
    const fd = new FormData()
    fd.append('tipo_voucher', tipo)
    fd.append('arquivo', arquivo)
    const url = modoToken.value
      ? `/agencia/token/${tokenUUID.value}/voucher`
      : `/vouchers/${solDetalhe.value.id}/upload`
    const res = await apiClient.request(url, {
      method: 'POST',
      auth: !modoToken.value,
      json: false,
      body: fd,
    })
    const dados = res.data || {}
    if (!res.ok) {
      voucherErro.value = dados.detail || 'Erro ao enviar voucher.'
      return
    }
    voucherSucesso.value = `Voucher "${tiposInfo[tipo]?.label}" enviado com sucesso!`
    arquivosVoucher[tipo] = null
    if (dados.status_solicitacao === 'CONCLUIDA') {
      solDetalhe.value.status = 'CONCLUIDA'
      voucherSucesso.value = '🎉 Todos os vouchers enviados! Solicitação CONCLUÍDA.'
    }
  } catch {
    voucherErro.value = 'Erro de conexão com o servidor.'
  } finally {
    enviandoVoucher[tipo] = false
  }
}

function selecionarArquivoCancelamento(event) {
  arquivoCancelamento.value = event.target.files?.[0] || null
}

async function submeterLiquidarCancelamento() {
  if (!solDetalhe.value) return
  enviandoCancelamento.value = true
  try {
    const fd = new FormData()
    fd.append('taxa_cancelamento_agencia', formCancelamento.taxa_cancelamento_agencia)
    fd.append('valor_reembolsavel_agencia', formCancelamento.valor_reembolsavel_agencia)
    fd.append('valor_credito_gerado', formCancelamento.valor_credito_gerado)
    fd.append('companhia_credito', formCancelamento.companhia_credito)
    if (arquivoCancelamento.value) fd.append('arquivo', arquivoCancelamento.value)
    const url = modoToken.value
      ? `/agencia/token/${tokenUUID.value}/liquidar-cancelamento`
      : `/agencia/solicitacoes/${solDetalhe.value.id}/liquidar-cancelamento`
    const res = await apiClient.request(url, {
      method: 'POST',
      auth: !modoToken.value,
      json: false,
      body: fd,
    })
    const dados = res.data || {}
    if (!res.ok) {
      voucherErro.value = dados.detail || 'Erro ao submeter liquidação.'
      return
    }
    voucherSucesso.value = 'Custos de cancelamento/remarcação liquidados com sucesso!'
    voltarLista()
  } catch {
    voucherErro.value = 'Erro de conexão com o servidor.'
  } finally {
    enviandoCancelamento.value = false
  }
}

function sair() {
  token.value = ''
  tela.value = 'token_erro'
  tokenErro.value = 'Sessão expirada ou link inválido.'
}

onMounted(() => {
  if (typeof window._vlReady === 'function') window._vlReady()
  const params = new URLSearchParams(window.location.search)
  const tokenParam = params.get('token')
  if (tokenParam) {
    modoToken.value = true
    tokenUUID.value = tokenParam
    void carregarPorToken(tokenParam)
    return
  }
  tokenErro.value = 'Este portal requer um link de cotação válido enviado por e-mail.'
  tela.value = 'token_erro'
})
</script>

<template>
  <div class="min-h-full vl-font-inter">
    <div v-if="tela === 'token_carregando'" class="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <div class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div class="vl-shell-dark-card text-center">
        <div class="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
        <div class="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-5" />
        <h2 class="text-lg font-bold text-white mb-1">Acessando Portal</h2>
        <p class="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">ViagensLabs</p>
        <p class="text-slate-300 text-sm">Carregando solicitação segura de cotação…</p>
      </div>
    </div>

    <div v-else-if="tela === 'token_erro'" class="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <div class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-red-600/5 rounded-full blur-[120px] pointer-events-none" />
      <div class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-orange-600/5 rounded-full blur-[120px] pointer-events-none" />
      <div class="vl-shell-dark-card text-center">
        <div class="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-red-500 to-orange-500" />
        <div class="text-4xl mb-4" aria-hidden="true">⚠️</div>
        <h2 class="text-xl font-bold text-white mb-2">Link de Cotação Expirado ou Inválido</h2>
        <p class="text-slate-300 text-sm mb-6 leading-relaxed">{{ tokenErro || 'Este portal requer um link de cotação válido enviado por e-mail.' }}</p>
        <p class="text-xs text-slate-500 border-t border-slate-800/80 pt-4">Entre em contato com o setor de viagens do Luizalabs para solicitar um novo link.</p>
      </div>
    </div>

    <div v-else class="bg-viagens min-h-screen">
      <nav class="bg-white/80 backdrop-blur-xl shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border-b border-slate-100 sticky top-0 z-50">
        <div class="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <img :src="logoLuizalabs" alt="Luizalabs" class="h-6 object-contain shrink-0">
            <div>
              <h1 class="text-sm font-extrabold text-slate-800 tracking-tight leading-tight">ViagensLabs</h1>
              <p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest">Portal da Agência</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="hidden sm:flex flex-col items-end">
              <span class="text-xs font-bold text-slate-700 leading-tight">{{ agenciaNome }}</span>
              <span class="text-[9px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100 uppercase tracking-wider mt-0.5">Parceiro</span>
            </div>
            <div class="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-blue-500 text-white flex items-center justify-center font-bold text-xs shadow-sm shadow-indigo-500/20">
              {{ agenciaNome ? agenciaNome.charAt(0).toUpperCase() : 'A' }}
            </div>
          </div>
        </div>
      </nav>

      <main class="max-w-5xl mx-auto px-4 py-8">
        <div class="bg-white/80 backdrop-blur-xl rounded-3xl border border-slate-100 shadow-[0_24px_50px_-12px_rgba(15,23,42,0.08)] p-8 min-h-[70vh]">
          <template v-if="tela === 'lista'">
            <div class="flex items-center justify-between mb-8">
              <div>
                <h1 class="text-2xl font-extrabold text-slate-800 tracking-tight">Solicitações de Viagem</h1>
                <p class="text-xs text-slate-400 mt-1 font-medium">Gerencie suas cotações e envie os vouchers operacionais.</p>
              </div>
              <div class="flex items-center gap-3">
                <select v-model="filtroStatus" class="border border-slate-200 bg-white rounded-xl px-4 py-2.5 text-xs font-bold text-slate-700">
                  <option value="">Todos os status</option>
                  <option value="AGUARDANDO_COTACAO">Aguardando Cotação</option>
                  <option value="COTACAO_ENVIADA">Cotação Enviada</option>
                  <option value="APROVADA_AGUARDANDO_VOUCHER">Aguardando Vouchers</option>
                  <option value="CONCLUIDA">Concluída</option>
                </select>
                <button class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-extrabold rounded-xl px-4 py-2.5" @click="carregarSolicitacoes">Atualizar</button>
              </div>
            </div>

            <div v-if="carregandoLista" class="text-center py-20">
              <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
              <p class="text-slate-400 text-xs font-medium">Buscando solicitações operacionais…</p>
            </div>
            <div v-else-if="solicitacoes.length === 0" class="text-center py-20 bg-slate-50/50 border border-dashed border-slate-200 rounded-2xl">
              <div class="text-4xl mb-3">📭</div>
              <h3 class="text-sm font-bold text-slate-700">Nenhuma solicitação encontrada</h3>
            </div>
            <div v-else class="space-y-4">
              <div
                v-for="sol in solicitacoes"
                :key="sol.id"
                class="bg-white/70 hover:bg-white border border-slate-100 rounded-2xl p-6 shadow-sm cursor-pointer"
                @click="abrirDetalhe(sol.id)"
              >
                <div class="flex items-start justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold text-blue-600 bg-blue-50 border border-blue-100/50 px-2.5 py-1 rounded-lg">{{ sol.protocolo }}</span>
                    <span :class="badgeStatus(sol.status)" class="text-xs font-bold rounded-lg border px-2.5 py-1">{{ labelStatus(sol.status) }}</span>
                  </div>
                  <div class="text-xs font-bold text-slate-400">{{ formatarData(sol.data_ida) }}</div>
                </div>
              </div>
            </div>
          </template>

          <template v-if="tela === 'detalhe'">
            <button v-if="!modoToken" class="bg-slate-50 border border-slate-200 text-slate-600 rounded-xl px-4 py-2 text-xs font-bold mb-6" @click="voltarLista">Voltar à lista</button>

            <div v-if="!solDetalhe" class="text-center py-20">
              <div class="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
              <p class="text-slate-400 text-xs font-medium">Carregando detalhes da viagem…</p>
            </div>

            <template v-else>
              <div class="bg-white/60 backdrop-blur-md rounded-2xl border border-slate-100 p-6 mb-6 shadow-sm">
                <div class="flex items-center justify-between flex-wrap gap-2 mb-6">
                  <div class="flex items-center gap-3">
                    <span class="text-lg font-bold font-mono text-blue-700 bg-blue-50 border border-blue-100/50 px-3 py-1 rounded-xl">{{ solDetalhe.protocolo }}</span>
                    <span :class="badgeStatus(solDetalhe.status)" class="text-xs font-bold rounded-lg border px-2.5 py-1">{{ labelStatus(solDetalhe.status) }}</span>
                  </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-sm">
                  <div><span class="text-slate-400 font-bold uppercase tracking-wider text-[10px] block mb-0.5">Solicitante</span><p class="font-bold text-slate-800">{{ solDetalhe.solicitante_username }}</p></div>
                  <div><span class="text-slate-400 font-bold uppercase tracking-wider text-[10px] block mb-0.5">Origem</span><p class="font-bold text-slate-800">{{ solDetalhe.origem_cidade || '—' }}</p></div>
                  <div><span class="text-slate-400 font-bold uppercase tracking-wider text-[10px] block mb-0.5">Destino</span><p class="font-bold text-slate-800">{{ solDetalhe.destino_cidade }}{{ solDetalhe.destino_estado ? '/' + solDetalhe.destino_estado : '' }}</p></div>
                </div>
              </div>

              <div class="bg-white/60 backdrop-blur-md rounded-2xl border border-slate-100 p-6 shadow-sm">
                <h2 class="text-lg font-extrabold text-slate-800 mb-1">💰 {{ solDetalhe.cotacao ? 'Atualizar Cotação Comercial' : 'Registrar Cotação Comercial' }}</h2>
                <p v-if="cotacaoSucesso" class="mb-5 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl px-4 py-3.5 text-xs font-bold">Cotação registrada com sucesso!</p>
                <p v-if="cotacaoErro" class="mb-5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl px-4 py-3.5 text-xs font-bold">{{ cotacaoErro }}</p>

                <form class="space-y-6" @submit.prevent="enviarCotacao">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gradient-to-br from-slate-50 to-slate-100/50 border border-slate-200 p-6 rounded-2xl">
                    <div>
                      <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Valor Total da Cotação (R$)</label>
                      <input v-model.number="formCotacao.valor_total" type="number" min="0" step="0.01" class="mt-2 w-full border border-slate-200 rounded-xl px-4 py-3 text-sm" />
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Observações da Agência</label>
                      <textarea v-model="formCotacao.observacoes" rows="2" class="mt-2 w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm resize-none" />
                    </div>
                  </div>
                  <div class="flex justify-end gap-3 pt-2">
                    <button type="button" class="px-5 py-2.5 text-xs font-bold border border-slate-200 rounded-xl text-slate-500" @click="voltarLista">Cancelar</button>
                    <button type="submit" :disabled="enviandoCotacao" class="px-6 py-2.5 text-xs font-extrabold bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-xl">
                      {{ enviandoCotacao ? 'Enviando…' : (solDetalhe.cotacao ? 'Atualizar Cotação' : 'Enviar Cotação') }}
                    </button>
                  </div>
                </form>
              </div>

              <div v-if="solDetalhe.status === 'APROVADA_AGUARDANDO_VOUCHER' && solDetalhe.agencia_vencedora === agenciaNome" class="bg-gradient-to-br from-purple-50/60 to-indigo-50/40 border border-purple-100/70 rounded-2xl p-6 mt-8 shadow-sm">
                <h2 class="text-lg font-extrabold text-purple-900 mb-1">🎫 Emitir Vouchers Operacionais</h2>
                <p v-if="voucherSucesso" class="mb-5 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl px-4 py-3.5 text-xs font-bold">✔ {{ voucherSucesso }}</p>
                <p v-if="voucherErro" class="mb-5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl px-4 py-3.5 text-xs font-bold">{{ voucherErro }}</p>

                <div class="space-y-4">
                  <div v-for="tipo in tiposVoucherNecessarios(solDetalhe)" :key="tipo.valor" class="flex flex-wrap sm:flex-nowrap items-center gap-4 border border-purple-100 bg-white/70 rounded-xl p-4 shadow-sm">
                    <span class="text-2xl bg-purple-100/60 w-11 h-11 rounded-lg flex items-center justify-center">{{ tipo.icone }}</span>
                    <div class="flex-1">
                      <p class="text-xs font-bold text-slate-700 uppercase tracking-wider">{{ tipo.label }}</p>
                      <p class="text-xs text-slate-450 mt-1 font-medium">{{ arquivosVoucher[tipo.valor] ? arquivosVoucher[tipo.valor].name : 'Nenhum arquivo selecionado' }}</p>
                    </div>
                    <div class="flex items-center gap-2">
                      <label class="cursor-pointer">
                        <span class="px-4 py-2 text-xs font-extrabold bg-purple-50 text-purple-700 border border-purple-200 rounded-xl">Selecionar</span>
                        <input type="file" class="hidden" accept=".pdf,.jpg,.jpeg,.png" @change="selecionarArquivoVoucher($event, tipo.valor)">
                      </label>
                      <button class="px-4 py-2 text-xs font-extrabold bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white rounded-xl" :disabled="!arquivosVoucher[tipo.valor] || enviandoVoucher[tipo.valor]" @click="uploadVoucher(tipo.valor)">
                        {{ enviandoVoucher[tipo.valor] ? 'Enviando…' : 'Enviar' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="solDetalhe.status === 'PENDENTE_CANCELAMENTO' || solDetalhe.status === 'PENDENTE_REMARCACAO' || solDetalhe.status === 'pendente_cancelamento' || solDetalhe.status === 'pendente_remarcacao'" class="bg-gradient-to-br from-red-50 to-orange-50 border border-orange-250 rounded-3xl p-6 mt-8 shadow-sm">
                <h2 class="text-base font-extrabold text-orange-950 mb-1">🛑 Liquidar Custos de Cancelamento / Remarcação</h2>
                <form class="space-y-5" @submit.prevent="submeterLiquidarCancelamento">
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                      <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Taxa / Multa (R$)</label>
                      <input v-model.number="formCancelamento.taxa_cancelamento_agencia" type="number" min="0" step="0.01" required class="mt-1.5 w-full border border-slate-250 rounded-xl px-4 py-2.5 text-xs" >
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Valor Reembolsável (R$)</label>
                      <input v-model.number="formCancelamento.valor_reembolsavel_agencia" type="number" min="0" step="0.01" required class="mt-1.5 w-full border border-slate-250 rounded-xl px-4 py-2.5 text-xs" >
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Valor de Crédito (R$)</label>
                      <input v-model.number="formCancelamento.valor_credito_gerado" type="number" min="0" step="0.01" required class="mt-1.5 w-full border border-slate-250 rounded-xl px-4 py-2.5 text-xs" >
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Companhia do Crédito</label>
                      <select v-model="formCancelamento.companhia_credito" class="mt-1.5 w-full border border-slate-250 rounded-xl px-4 py-2.5 text-xs">
                        <option value="">Nenhuma / Não se aplica</option>
                        <option value="LATAM">LATAM</option>
                        <option value="GOL">GOL</option>
                        <option value="AZUL">AZUL</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label class="text-[10px] text-slate-550 font-bold uppercase tracking-wider block mb-1.5">Anexar Comprovante (PDF)</label>
                    <input type="file" accept="application/pdf" required @change="selecionarArquivoCancelamento" class="block w-full text-xs text-slate-500">
                  </div>
                  <div class="flex justify-end gap-3 pt-2">
                    <button type="submit" :disabled="enviandoCancelamento" class="px-6 py-2.5 text-xs font-extrabold bg-orange-600 hover:bg-orange-700 disabled:opacity-60 text-white rounded-xl">Confirmar Liquidação de Custos</button>
                  </div>
                </form>
              </div>
            </template>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.bg-viagens {
  background-image: linear-gradient(135deg, rgba(10, 15, 30, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%), var(--vl-bg-aviao);
}

.glass-card {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
}
</style>
