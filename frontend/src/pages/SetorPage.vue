<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createApiClient } from '@/services/api-client.js'
import { createSetorApi } from '@/services/setor-api.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()
const logoLuizalabs = new URL('../../img/luizalabs-logo.png', import.meta.url).href

const storage = window.localStorage
const token = ref(authStore.getToken() || '')
const nomeUsuario = ref(authStore.nome || '')
const perfilUsuario = ref(authStore.perfil || 'setor')
const aba = ref('solicitacoes')
const carregando = ref(false)
const erroGeral = ref('')
const sucessoGeral = ref('')

const solicitacoes = ref([])
const ativosHoje = ref(0)
const alertasAcesso = ref([])
const alertasAcessoInterval = ref(null)
const menuRecolhido = ref(false)

const mostrandoModalLGPDGestor = ref(false)
const aceitouLGPDGestor = ref(false)
const registrandoConsentimentoGestor = ref(false)
const erroConsentimentoGestor = ref('')

const filtros = reactive({ status: '', periodo: '', agencia: '', busca: '' })
let buscarTimer = null

const modalAberto = ref(false)
const detalhe = ref({})
const acaoCarregando = ref(false)
const acaoErro = ref('')
const pdfErro = ref('')

const confirmacao = reactive({ aberto: false, sol: null, acao: '' })

const kpis = ref([])
const distribuicaoStatus = ref([])
const volumeMensal = ref([])
const centroCustoRanking = ref([])

const casamentos = ref([])
const casamentosCount = ref(0)
const casamentoMsgOk = ref('')
const casamentoMsgErr = ref('')

const ticketsTerceiros = ref([])
const ticketsTerceirosPendentesCount = ref(0)
const filtroTerceirosStatus = ref('PENDENTE')
const ticketObs = ref({})

const agencias = ref([])
const agenciaMsgOk = ref('')
const agenciaMsgErr = ref('')
const modalAgenciaAberto = ref(false)
const agenciaEditando = ref(null)
const agenciaFormLoading = ref(false)
const agenciaFormErr = ref('')
const cnpjBuscando = ref(false)
const cnpjErro = ref('')
const bancoBuscando = ref(false)

const maxMensal = computed(() => Math.max(1, ...volumeMensal.value.map(m => m.total || 0)))
const maxCC = computed(() => Math.max(1, ...centroCustoRanking.value.map(c => c.count || 0)))

const menuItens = computed(() => [
  { id: 'solicitacoes', label: 'Solicitações', icon: '📋' },
  { id: 'indicadores', label: 'Indicadores', icon: '📊' },
  { id: 'casamentos', label: 'Casamentos', icon: '🔗', count: casamentosCount.value },
  { id: 'agencias', label: 'Agências', icon: '🏢' },
  { id: 'terceiros', label: 'Acesso Terceiros', icon: '🛡️', count: ticketsTerceirosPendentesCount.value },
])

const menuLabel = computed(() => {
  const labels = {
    solicitacoes: 'Solicitações de Viagem',
    indicadores: 'Painel de Indicadores',
    casamentos: 'Otimização de Casamentos',
    agencias: 'Gestão de Agências',
    terceiros: 'Controle de Acesso de Terceiros',
  }
  return labels[aba.value] || 'Painel do Setor'
})

const menuDesc = computed(() => {
  const descs = {
    solicitacoes: 'Gerencie e pré-aprove solicitações de viagens corporativas.',
    indicadores: 'Monitore métricas, gastos e distribuição por status.',
    casamentos: 'Analise e gerencie pares de viagens para otimização.',
    agencias: 'Cadastre e gerencie agências parceiras para cotações.',
    terceiros: 'Aprove/reprove tickets de delegação para terceiros.',
  }
  return descs[aba.value] || ''
})

const slotsCotacao = computed(() => {
  if (!detalhe.value) return []
  const cotacoes = detalhe.value.todas_cotacoes || []
  const listaAgencias = agencias.value.map(a => a.agencia_nome)

  cotacoes.forEach(c => {
    if (!listaAgencias.some(name => name?.toLowerCase() === c.agencia_nome?.toLowerCase())) {
      listaAgencias.push(c.agencia_nome)
    }
  })

  return listaAgencias.map(agName => {
    const cot = cotacoes.find(c => c.agencia_nome?.toLowerCase() === agName?.toLowerCase())
    return { agencia: agName, cot: cot || null }
  })
})

const apiClient = createApiClient({
  baseUrl: '/api/v1',
  getToken: () => token.value || authStore.getToken() || '',
  onUnauthorized: () => {
    token.value = ''
    sair()
  },
})
const setorApi = createSetorApi(apiClient)

function hidratarSessaoLegada() {
  const legacyToken = storage.getItem('token')
  const legacyNome = storage.getItem('nome_usuario')
  const legacyPerfil = storage.getItem('perfil')
  const legacyUsername = storage.getItem('username_ad')

  if (legacyToken && !authStore.getToken()) authStore.setToken(legacyToken)
  if (legacyNome && !authStore.nome) authStore.setNome(legacyNome)
  if (legacyPerfil && !authStore.perfil) authStore.setPerfil(legacyPerfil)
  if (legacyUsername && !authStore.username) authStore.setUsername(legacyUsername)

  token.value = authStore.getToken() || ''
  nomeUsuario.value = authStore.nome || ''
  perfilUsuario.value = authStore.perfil || 'setor'
}

function vlNavigate(url) {
  const map = {
    '/index.html': '/',
    '/dev.html': '/dev',
    '/setor.html': '/setor',
    '/politica-privacidade.html': '/politica-privacidade',
  }
  const target = map[url]
  if (target) {
    router.push(target)
    return
  }
  window.location.href = url
}

function sair() {
  authStore.clearAll()
  storage.removeItem('token')
  storage.removeItem('nome_usuario')
  storage.removeItem('perfil')
  storage.removeItem('username_ad')
  vlNavigate('/index.html')
}

function fmtData(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return iso
  }
}

function fmtDataHora(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return `${d.toLocaleDateString('pt-BR')} ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
}

function fmtValor(v) {
  if (v === null || v === undefined) return '—'
  return Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const STATUS_LABELS = {
  AGUARDANDO_N1: 'Ag. Aprovação N1',
  AGUARDANDO_N2: 'Ag. Aprovação N2',
  PENDENTE_PRE_APROVACAO_SETOR: 'Pré-Aprovar',
  AGUARDANDO_COTACAO: 'Ag. Cotação',
  COTACAO_ENVIADA: 'Cot. Enviada',
  PENDENTE_APROVACAO_SETOR_COTACAO: 'Decidir Agência',
  CONCLUIDA: 'Concluída',
  REPROVADA: 'Reprovada',
  PENDENTE_CANCELAMENTO: 'Ag. Agência (Cancelamento)',
  PENDENTE_REMARCACAO: 'Ag. Agência (Remarcação)',
  PENDENTE_APROVACAO_CANCELAMENTO: 'Revisar Cancelamento',
  PENDENTE_APROVACAO_REMARCACAO: 'Revisar Remarcação',
  CANCELADA: 'Cancelada',
}
function statusLabel(s) {
  return STATUS_LABELS[s] || s
}

function statusCor(s) {
  const m = {
    PENDENTE_PRE_APROVACAO_SETOR: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    AGUARDANDO_COTACAO: 'bg-blue-50 text-blue-700 border-blue-200',
    COTACAO_ENVIADA: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    PENDENTE_APROVACAO_SETOR_COTACAO: 'bg-purple-50 text-purple-700 border-purple-200',
    CONCLUIDA: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    REPROVADA: 'bg-red-50 text-red-600 border-red-200',
    AGUARDANDO_N1: 'bg-gray-50 text-gray-600 border-gray-200',
    AGUARDANDO_N2: 'bg-orange-50 text-orange-600 border-orange-200',
    PENDENTE_CANCELAMENTO: 'bg-amber-50 text-amber-700 border-amber-200',
    PENDENTE_REMARCACAO: 'bg-amber-50 text-amber-700 border-amber-200',
    PENDENTE_APROVACAO_CANCELAMENTO: 'bg-rose-100 text-rose-700 border-rose-300',
    PENDENTE_APROVACAO_REMARCACAO: 'bg-violet-100 text-violet-700 border-violet-300',
    CANCELADA: 'bg-red-100 text-red-700 border-red-200',
  }
  return m[s] || 'bg-gray-50 text-gray-500 border-gray-200'
}

function statusBarCor(s) {
  const m = {
    CONCLUIDA: 'bg-emerald-500',
    REPROVADA: 'bg-red-400',
    PENDENTE_PRE_APROVACAO_SETOR: 'bg-yellow-400',
    AGUARDANDO_COTACAO: 'bg-blue-500',
    PENDENTE_APROVACAO_SETOR_COTACAO: 'bg-purple-500',
    COTACAO_ENVIADA: 'bg-indigo-500',
    AGUARDANDO_N1: 'bg-gray-400',
    AGUARDANDO_N2: 'bg-orange-400',
    PENDENTE_CANCELAMENTO: 'bg-amber-400',
    PENDENTE_REMARCACAO: 'bg-amber-400',
    PENDENTE_APROVACAO_CANCELAMENTO: 'bg-rose-400',
    PENDENTE_APROVACAO_REMARCACAO: 'bg-violet-400',
    CANCELADA: 'bg-red-500',
  }
  return m[s] || 'bg-gray-400'
}

const ACAO_LABELS = {
  PRE_APROVAR: 'Pré-Aprovar',
  PRE_REPROVAR: 'Reprovar (pré-aprovação)',
  REPROVAR: 'Reprovar',
  REENVIAR_AGENCIAS: 'Reenviar E-mails às Agências',
}
function acaoLabel(a) {
  return ACAO_LABELS[a] || a
}

function verificarConsentimentoLGPDGestor() {
  const aceitouEstavez = storage.getItem('lgpd_gestor_aceito')
  const dataAceito = storage.getItem('lgpd_gestor_data_aceito')
  const hoje = new Date().toISOString().split('T')[0]

  if (aceitouEstavez && dataAceito === hoje) {
    aceitouLGPDGestor.value = true
    mostrandoModalLGPDGestor.value = false
  } else {
    mostrandoModalLGPDGestor.value = true
    aceitouLGPDGestor.value = false
  }
}

async function aceitarConsentimentoLGPDGestor() {
  registrandoConsentimentoGestor.value = true
  erroConsentimentoGestor.value = ''
  try {
    const r = await setorApi.registrarConsentimentoLGPD({
      aceito: true,
      versao_politica: '1.0',
      tipo: 'gestor_operador',
    })
    if (r.ok) {
      aceitouLGPDGestor.value = true
      mostrandoModalLGPDGestor.value = false
      const hoje = new Date().toISOString().split('T')[0]
      storage.setItem('lgpd_gestor_aceito', 'true')
      storage.setItem('lgpd_gestor_data_aceito', hoje)
    } else {
      const err = r.data || {}
      erroConsentimentoGestor.value = err.detail || 'Erro ao registrar consentimento'
    }
  } catch {
    erroConsentimentoGestor.value = 'Erro de conexão ao registrar consentimento'
  } finally {
    registrandoConsentimentoGestor.value = false
  }
}

async function carregarSolicitacoes() {
  carregando.value = true
  erroGeral.value = ''
  try {
    const p = new URLSearchParams()
    if (filtros.status) p.set('status_filtro', filtros.status)
    if (filtros.periodo) p.set('periodo_dias', filtros.periodo)
    if (filtros.agencia) p.set('agencia', filtros.agencia)
    if (filtros.busca) p.set('busca', filtros.busca)
    const resp = await setorApi.listarSolicitacoes(p.toString())
    if (!resp.ok) {
      erroGeral.value = resp?.data?.detail || 'Falha ao carregar solicitações.'
      return
    }
    solicitacoes.value = resp.data || []
  } catch (e) {
    erroGeral.value = e?.message || 'Falha de conexão ao carregar solicitações.'
  } finally {
    carregando.value = false
  }
}

function debounceCarregar() {
  if (buscarTimer) clearTimeout(buscarTimer)
  buscarTimer = window.setTimeout(carregarSolicitacoes, 350)
}

async function abrirDetalhe(s) {
  acaoErro.value = ''
  try {
    const resp = await setorApi.obterDetalhesSolicitacao(s.id)
    if (!resp.ok) return
    detalhe.value = resp.data || {}
    modalAberto.value = true
  } catch {
    acaoErro.value = 'Erro ao carregar detalhe da solicitação.'
  }
}

function fecharModal() {
  modalAberto.value = false
  detalhe.value = {}
  acaoErro.value = ''
}

async function abrirPdfAssinado(ticket) {
  pdfErro.value = ''
  if (!ticket?.pdf_url && !ticket?.pdf_path) {
    pdfErro.value = 'PDF não disponível para esta autorização.'
    return
  }

  const url = ticket.pdf_url || `/${ticket.pdf_path}`
  const novaAba = window.open('about:blank', '_blank')
  if (!novaAba) {
    pdfErro.value = 'Permita pop-ups para abrir o PDF assinado.'
    return
  }

  try {
    const resp = await setorApi.baixarPdfAssinado(url)
    if (resp.status === 401 || resp.status === 403) {
      throw new Error('Não foi possível autenticar a visualização do PDF.')
    }
    if (!resp.ok) {
      const dados = await resp.json().catch(() => ({}))
      throw new Error(dados.detail || 'Falha ao carregar o PDF.')
    }
    const blob = await resp.blob()
    const blobUrl = URL.createObjectURL(blob)
    novaAba.location.href = blobUrl
    window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)
  } catch (e) {
    novaAba.close()
    pdfErro.value = e?.message || 'Falha ao abrir o PDF assinado.'
  }
}

function confirmarAcao(sol, acao) {
  acaoErro.value = ''
  confirmacao.sol = sol
  confirmacao.acao = acao
  confirmacao.aberto = true
}

async function executarAcao(sol, acao) {
  acaoCarregando.value = true
  acaoErro.value = ''
  try {
    const resp = await setorApi.decidirSolicitacao(sol.id, { acao, observacao: '' })
    const dados = resp.data || {}
    if (!resp.ok) throw new Error(dados.detail || 'Erro ao executar ação.')

    confirmacao.aberto = false
    sucessoGeral.value = 'Ação executada com sucesso.'
    await carregarSolicitacoes()
    if (modalAberto.value) await abrirDetalhe(sol)
  } catch (e) {
    acaoErro.value = e?.message || 'Falha ao executar ação.'
  } finally {
    acaoCarregando.value = false
  }
}

async function decidirCancelamento(sol, acao, observacao = '') {
  acaoCarregando.value = true
  acaoErro.value = ''
  try {
    const resp = await setorApi.cancelarSolicitacao(sol.id, { acao, observacao })
    const dados = resp.data || {}
    if (!resp.ok) throw new Error(dados.detail || 'Erro ao decidir cancelamento/remarcação.')

    confirmacao.aberto = false
    sucessoGeral.value = 'Decisão de cancelamento/remarcação registrada.'
    await carregarSolicitacoes()
    if (modalAberto.value) await abrirDetalhe(sol)
  } catch (e) {
    acaoErro.value = e?.message || 'Falha na decisão de cancelamento/remarcação.'
  } finally {
    acaoCarregando.value = false
  }
}

function calcularIndicadores() {
  const lista = solicitacoes.value
  const total = lista.length

  const grupos = {}
  lista.forEach(s => {
    grupos[s.status] = (grupos[s.status] || 0) + 1
  })

  distribuicaoStatus.value = Object.entries(grupos)
    .sort((a, b) => b[1] - a[1])
    .map(([status, count]) => ({
      label: statusLabel(status),
      count,
      pct: total > 0 ? Math.round((count / total) * 100) : 0,
      cor: statusBarCor(status),
    }))

  const meses = {}
  const agora = new Date()
  for (let i = 5; i >= 0; i -= 1) {
    const d = new Date(agora.getFullYear(), agora.getMonth() - i, 1)
    const key = `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getFullYear()).slice(2)}`
    meses[key] = 0
  }
  lista.forEach(s => {
    if (!s.data_ida) return
    const d = new Date(s.data_ida)
    const key = `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getFullYear()).slice(2)}`
    if (key in meses) meses[key] += 1
  })
  volumeMensal.value = Object.entries(meses).map(([mes, totalMes]) => ({ mes, total: totalMes }))

  const ccMap = {}
  lista.forEach(s => {
    const nome = s.viajante_centro_custo || ''
    const cod = s.viajante_cod_centro_custo || ''
    if (!nome && !cod) return
    const key = cod ? `${cod}__${nome}` : nome
    if (!ccMap[key]) ccMap[key] = { nome, cod, count: 0 }
    ccMap[key].count += 1
  })
  centroCustoRanking.value = Object.values(ccMap)
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  kpis.value = [
    { label: 'Total', valor: total },
    { label: 'Concluídas', valor: lista.filter(s => s.status === 'CONCLUIDA').length },
    { label: 'Reprovadas', valor: lista.filter(s => s.status === 'REPROVADA').length },
    { label: 'Pré-Aprovar', valor: lista.filter(s => s.status === 'PENDENTE_PRE_APROVACAO_SETOR').length },
    { label: 'Ativos Hoje', valor: ativosHoje.value },
  ]
}

const _csvEscape = v => {
  const s = v === null || v === undefined ? '' : String(v)
  return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s.replace(/"/g, '""')}"` : s
}

function baixarCSV(rows, filename) {
  const bom = '\uFEFF'
  const csv = bom + rows.map(r => r.map(_csvEscape).join(',')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function exportarSolicitacoes() {
  const cabecalho = ['Protocolo', 'Solicitante', 'Viajante', 'Destino', 'Data Ida', 'Status', 'Agência Vencedora']
  const linhas = solicitacoes.value.map(s => [
    s.protocolo,
    s.solicitante_username,
    s.viajante_nome,
    `${s.destino_cidade || ''}/${s.destino_estado || ''}`,
    fmtData(s.data_ida),
    statusLabel(s.status),
    s.agencia_vencedora || '',
  ])
  baixarCSV([cabecalho, ...linhas], `solicitacoes_${new Date().toISOString().slice(0, 10)}.csv`)
}

function exportarStatus() {
  const cabecalho = ['Status', 'Quantidade', 'Percentual (%)']
  const linhas = distribuicaoStatus.value.map(i => [i.label, i.count, i.pct])
  baixarCSV([cabecalho, ...linhas], `distribuicao_status_${new Date().toISOString().slice(0, 10)}.csv`)
}

async function carregarCasamentos() {
  casamentos.value = []
  try {
    const res = await setorApi.listarCasamentos()
    if (!res.ok) return
    casamentos.value = res.data || []
    casamentosCount.value = casamentos.value.length
  } catch {
    casamentoMsgErr.value = 'Erro ao carregar casamentos.'
  }
}

async function agirCasamento(id, acao) {
  casamentoMsgOk.value = ''
  casamentoMsgErr.value = ''
  try {
    const res = await setorApi.decidirCasamento(id, acao)
    if (!res.ok) {
      casamentoMsgErr.value = res?.data?.detail || 'Erro ao processar ação.'
      return
    }
    casamentoMsgOk.value = acao === 'vincular' ? '✔ Casamento vinculado.' : '✔ Match ignorado.'
    await carregarCasamentos()
  } catch {
    casamentoMsgErr.value = 'Erro de conexão.'
  }
}

function tipoCasamentoCor(tipo) {
  return {
    TOTAL: 'bg-green-100 text-green-800',
    PARCIAL_A: 'bg-blue-100 text-blue-800',
    PARCIAL_B: 'bg-yellow-100 text-yellow-800',
  }[tipo] || 'bg-gray-100 text-gray-600'
}

async function carregarTicketsTerceiros() {
  try {
    const statusFiltro = filtroTerceirosStatus.value
    const res = await setorApi.listarTerceiros(statusFiltro)
    if (res.ok) ticketsTerceiros.value = res.data || []

    const resP = await setorApi.listarTerceiros('PENDENTE')
    if (resP.ok) ticketsTerceirosPendentesCount.value = (resP.data || []).length
  } catch {
    erroGeral.value = 'Erro ao carregar tickets de terceiros.'
  }
}

async function decidirTicket(id, acao, obs = '') {
  try {
    const formData = new FormData()
    formData.append('acao', acao)
    formData.append('observacao', obs || '')

    const res = await setorApi.decidirTerceiro(id, formData)
    if (!res.ok) {
      erroGeral.value = res?.data?.detail || 'Erro ao processar decisão do ticket.'
      return
    }
    delete ticketObs.value[id]
    sucessoGeral.value = `Ticket ${acao === 'APROVADA' ? 'aprovado' : 'reprovado'} com sucesso.`
    await carregarTicketsTerceiros()
  } catch {
    erroGeral.value = 'Erro de conexão ao decidir ticket.'
  }
}

const emptyAgenciaForm = () => ({
  agencia_nome: '',
  razao_social: '',
  cnpj: '',
  inscricao_estadual: '',
  email: '',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  municipio: '',
  uf: '',
  banco_nome: '',
  banco_codigo: '',
  agencia_bancaria: '',
  conta_bancaria: '',
  tipo_conta: 'CC',
  titularidade_cnpj: '',
  titularidade_razao_social: '',
  ativo: true,
})
const agenciaForm = ref(emptyAgenciaForm())

function fmtCnpj(v) {
  const s = (v || '').replace(/\D/g, '').padStart(14, '0')
  return s.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')
}

function mascararCnpj() {
  let v = agenciaForm.value.cnpj.replace(/\D/g, '').slice(0, 14)
  if (v.length > 12) v = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{0,2})$/, '$1.$2.$3/$4-$5')
  else if (v.length > 8) v = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{0,4})$/, '$1.$2.$3/$4')
  else if (v.length > 5) v = v.replace(/^(\d{2})(\d{3})(\d{0,3})$/, '$1.$2.$3')
  else if (v.length > 2) v = v.replace(/^(\d{2})(\d{0,3})$/, '$1.$2')
  agenciaForm.value.cnpj = v
}

async function buscarCnpj() {
  const cnpj = agenciaForm.value.cnpj.replace(/\D/g, '')
  if (cnpj.length !== 14) {
    cnpjErro.value = 'CNPJ deve ter 14 dígitos.'
    return
  }
  cnpjErro.value = ''
  cnpjBuscando.value = true
  try {
    const res = await setorApi.buscarCnpj(cnpj)
    if (!res.ok) {
      cnpjErro.value = 'CNPJ não encontrado ou erro na consulta.'
      return
    }
    const d = res.data || {}
    agenciaForm.value.razao_social = d.razao_social || ''
    agenciaForm.value.agencia_nome = agenciaForm.value.agencia_nome || d.nome_fantasia || ''
    agenciaForm.value.logradouro = d.logradouro || ''
    agenciaForm.value.numero = d.numero || ''
    agenciaForm.value.complemento = d.complemento || ''
    agenciaForm.value.bairro = d.bairro || ''
    agenciaForm.value.municipio = d.municipio || ''
    agenciaForm.value.uf = d.uf || ''
    agenciaForm.value.cep = (d.cep || '').replace(/\D/g, '').replace(/^(\d{5})(\d{3})$/, '$1-$2')
    agenciaForm.value.titularidade_cnpj = agenciaForm.value.titularidade_cnpj || agenciaForm.value.cnpj
    agenciaForm.value.titularidade_razao_social = agenciaForm.value.titularidade_razao_social || d.razao_social || ''
  } catch {
    cnpjErro.value = 'Erro ao consultar CNPJ via proxy.'
  } finally {
    cnpjBuscando.value = false
  }
}

async function buscarCep() {
  const cep = agenciaForm.value.cep.replace(/\D/g, '')
  if (cep.length !== 8) return
  try {
    const res = await setorApi.buscarCep(cep)
    if (!res.ok) return
    const d = res.data || {}
    if (d.street) agenciaForm.value.logradouro = d.street
    if (d.neighborhood) agenciaForm.value.bairro = d.neighborhood
    if (d.city) agenciaForm.value.municipio = d.city
    if (d.state) agenciaForm.value.uf = d.state
  } catch {
    // noop
  }
}

async function buscarBanco() {
  const cod = (agenciaForm.value.banco_codigo || '').replace(/\D/g, '')
  if (!cod) return
  bancoBuscando.value = true
  try {
    const res = await setorApi.buscarBanco(cod)
    if (!res.ok) return
    const d = res.data || {}
    agenciaForm.value.banco_nome = d.name || d.fullName || agenciaForm.value.banco_nome
  } finally {
    bancoBuscando.value = false
  }
}

async function carregarAgencias() {
  try {
    const res = await setorApi.listarAgencias()
    if (!res.ok) {
      agenciaMsgErr.value = 'Erro ao carregar agências.'
      return
    }
    agencias.value = res.data || []
  } catch {
    agenciaMsgErr.value = 'Erro de conexão ao carregar agências.'
  }
}

function abrirModalAgencia(ag) {
  agenciaEditando.value = ag
  agenciaFormErr.value = ''
  cnpjErro.value = ''
  agenciaForm.value = ag ? { ...ag, cnpj: fmtCnpj(ag.cnpj) } : emptyAgenciaForm()
  modalAgenciaAberto.value = true
}

function fecharModalAgencia() {
  modalAgenciaAberto.value = false
  agenciaEditando.value = null
}

async function salvarAgencia() {
  agenciaFormErr.value = ''
  agenciaFormLoading.value = true
  try {
    const payload = {
      ...agenciaForm.value,
      cnpj: agenciaForm.value.cnpj.replace(/\D/g, ''),
      uf: (agenciaForm.value.uf || '').toUpperCase(),
    }
    const ed = agenciaEditando.value
    if (!payload.agencia_nome?.trim()) {
      agenciaFormErr.value = 'Informe o nome fantasia.'
      return
    }
    if (!ed && !payload.email?.trim()) {
      agenciaFormErr.value = 'Informe o e-mail de contato.'
      return
    }

    const url = ed ? `/setor/agencias/${ed.id}` : '/setor/agencias'
    const method = ed ? 'PUT' : 'POST'
    const res = await setorApi.salvarAgencia(url, method, payload)
    if (!res.ok) {
      agenciaFormErr.value = res?.data?.detail || 'Erro ao salvar agência.'
      return
    }
    agenciaMsgOk.value = ed ? '✔ Agência atualizada.' : '✔ Agência cadastrada com sucesso.'
    fecharModalAgencia()
    await carregarAgencias()
  } catch {
    agenciaFormErr.value = 'Erro de conexão ao salvar agência.'
  } finally {
    agenciaFormLoading.value = false
  }
}

async function toggleAgencia(ag) {
  agenciaMsgOk.value = ''
  agenciaMsgErr.value = ''
  try {
    const res = await setorApi.alternarStatusAgencia(ag.id, { ativo: !ag.ativo })
    if (!res.ok) {
      agenciaMsgErr.value = res?.data?.detail || 'Erro ao alterar status.'
      return
    }
    agenciaMsgOk.value = ag.ativo ? '✔ Agência desativada.' : '✔ Agência ativada.'
    await carregarAgencias()
  } catch {
    agenciaMsgErr.value = 'Erro de conexão ao alterar status.'
  }
}

async function confirmarExcluirAgencia(ag) {
  if (!window.confirm(`Excluir permanentemente a agência "${ag.agencia_nome}"?`)) return
  try {
    const res = await setorApi.excluirAgencia(ag.id)
    if (res.status === 204 || res.ok) {
      agenciaMsgOk.value = `✔ Agência "${ag.agencia_nome}" excluída.`
      await carregarAgencias()
      return
    }
    agenciaMsgErr.value = res?.data?.detail || 'Erro ao excluir agência.'
  } catch {
    agenciaMsgErr.value = 'Erro de conexão ao excluir agência.'
  }
}

async function carregarStatsAdicionais() {
  try {
    const resp = await setorApi.obterStats()
    if (resp.ok) {
      ativosHoje.value = resp?.data?.ativos_hoje || 0
    }
  } catch {
    // noop
  }
}

async function carregarAlertasAcesso() {
  try {
    const resp = await setorApi.obterAlertasAcesso()
    if (resp.ok) alertasAcesso.value = resp.data || []
  } catch {
    // noop
  }
}

function isWithin24h(dataCriacao, dataAtualizacao) {
  if (!dataCriacao) return false
  const criacao = new Date(dataCriacao)
  const atualizacao = dataAtualizacao ? new Date(dataAtualizacao) : new Date()
  const diffTime = Math.abs(atualizacao - criacao)
  const diffHours = diffTime / (1000 * 60 * 60)
  return diffHours <= 24
}

watch(aba, async novaAba => {
  if (novaAba === 'terceiros') {
    await carregarAlertasAcesso()
    if (alertasAcessoInterval.value) clearInterval(alertasAcessoInterval.value)
    alertasAcessoInterval.value = window.setInterval(() => {
      void carregarAlertasAcesso()
    }, 8000)
  } else if (alertasAcessoInterval.value) {
    clearInterval(alertasAcessoInterval.value)
    alertasAcessoInterval.value = null
  }

  if (novaAba === 'indicadores') {
    await carregarStatsAdicionais()
    calcularIndicadores()
  }
  if (novaAba === 'casamentos') {
    await carregarCasamentos()
  }
  if (novaAba === 'agencias') {
    await carregarAgencias()
  }
  if (novaAba === 'terceiros') {
    await carregarTicketsTerceiros()
  }
})

onMounted(async () => {
  hidratarSessaoLegada()
  const perfil = perfilUsuario.value || authStore.perfil || ''
  if (!token.value || (perfil !== 'setor' && perfil !== 'dev')) {
    vlNavigate('/index.html')
    return
  }

  verificarConsentimentoLGPDGestor()
  await carregarSolicitacoes()
  await carregarTicketsTerceiros()
  await carregarAgencias()
  await carregarStatsAdicionais()
  calcularIndicadores()
})

onBeforeUnmount(() => {
  if (buscarTimer) clearTimeout(buscarTimer)
  if (alertasAcessoInterval.value) clearInterval(alertasAcessoInterval.value)
})
</script>

<template>
  <div class="min-h-screen flex bg-[#f8fafc] text-gray-800">
    <aside
      :class="menuRecolhido ? 'w-20' : 'w-64'"
      class="bg-[#0a0f1e] text-slate-300 flex flex-col shrink-0 border-r border-slate-800/40 min-h-screen transition-all duration-300"
    >
      <div class="p-5 flex flex-col items-center border-b border-slate-800/40 gap-2 select-none">
        <img
          :src="logoLuizalabs"
          alt="Luizalabs"
          :class="menuRecolhido ? 'h-6' : 'h-8'"
          class="object-contain shrink-0"
        >
        <div v-if="!menuRecolhido" class="text-center">
          <span class="text-[10px] font-mono text-blue-400 block tracking-widest leading-none uppercase font-bold mt-1">Viagens</span>
        </div>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <button
          v-for="item in menuItens"
          :key="item.id"
          type="button"
          @click="aba = item.id"
          :class="aba === item.id ? 'bg-blue-600/15 text-blue-400 border-l-4 border-blue-500 font-bold rounded-lg' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/20 border-l-4 border-transparent rounded-lg'"
          class="w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-all duration-200 text-left"
        >
          <span class="text-base shrink-0">{{ item.icon }}</span>
          <span v-if="!menuRecolhido" class="truncate flex-1">{{ item.label }}</span>
          <span
            v-if="!menuRecolhido && item.count"
            class="bg-blue-600/20 text-blue-300 text-[9px] font-bold px-1.5 py-0.5 rounded-full"
          >{{ item.count }}</span>
        </button>
      </nav>

      <div class="p-4 border-t border-slate-800/40 flex flex-col gap-2 shrink-0">
        <button
          type="button"
          @click="menuRecolhido = !menuRecolhido"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800/20 border border-slate-800/40 hover:bg-slate-800/30 text-slate-400 hover:text-slate-200 rounded-lg text-[10px] font-mono transition"
        >
          <span>{{ menuRecolhido ? '▶' : '◀ Recolher menu' }}</span>
        </button>
        <button
          type="button"
          class="text-xs text-slate-300 hover:text-white text-left"
          @click="vlNavigate('/index.html')"
        >
          ✈️ Portal do Viajante
        </button>
      </div>
    </aside>

    <div class="flex-grow flex flex-col min-w-0 min-h-screen">
      <header class="bg-white border-b border-gray-200/80 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
        <div class="min-w-0">
          <span class="text-sm font-bold text-gray-800 tracking-tight">{{ menuLabel }}</span>
          <p class="text-xs text-gray-400 truncate">{{ menuDesc }}</p>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <span class="text-xs font-semibold text-gray-700 leading-tight">{{ nomeUsuario || 'Operador' }}</span>
          <button type="button" @click="sair" class="vl-btn-logout">Sair</button>
        </div>
      </header>

      <main class="w-full p-6 flex-grow space-y-4">
        <div v-if="erroGeral" class="vl-red-error-surface p-3 text-sm">{{ erroGeral }}</div>
        <div v-if="sucessoGeral" class="bg-green-50 border border-green-200 text-green-700 rounded-lg p-3 text-sm">{{ sucessoGeral }}</div>

        <template v-if="aba === 'solicitacoes'">
          <section class="glass-panel card-accent-blue p-5">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Filtros</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label for="setor-status" class="block text-xs font-semibold text-gray-600 mb-1.5">Status</label>
                <select id="setor-status" v-model="filtros.status" @change="carregarSolicitacoes" class="w-full text-sm border border-labs-border rounded-lg px-3 py-2.5">
                  <option value="">Todos os status</option>
                  <option value="AGUARDANDO_N1">Ag. Aprovação N1</option>
                  <option value="AGUARDANDO_N2">Ag. Aprovação N2</option>
                  <option value="PENDENTE_PRE_APROVACAO_SETOR">Pré-Aprovar</option>
                  <option value="AGUARDANDO_COTACAO">Ag. Cotação</option>
                  <option value="COTACAO_ENVIADA">Cot. Enviada</option>
                  <option value="PENDENTE_APROVACAO_SETOR_COTACAO">Decidir Agência</option>
                  <option value="CONCLUIDA">Concluída</option>
                  <option value="REPROVADA">Reprovada</option>
                </select>
              </div>
              <div>
                <label for="setor-periodo" class="block text-xs font-semibold text-gray-600 mb-1.5">Período</label>
                <select id="setor-periodo" v-model="filtros.periodo" @change="carregarSolicitacoes" class="w-full text-sm border border-labs-border rounded-lg px-3 py-2.5">
                  <option value="">Todos os períodos</option>
                  <option value="7">Últimos 7 dias</option>
                  <option value="30">Últimos 30 dias</option>
                  <option value="90">Últimos 90 dias</option>
                </select>
              </div>
              <div>
                <label for="setor-agencia" class="block text-xs font-semibold text-gray-600 mb-1.5">Agência Vencedora</label>
                <select id="setor-agencia" v-model="filtros.agencia" @change="carregarSolicitacoes" class="w-full text-sm border border-labs-border rounded-lg px-3 py-2.5">
                  <option value="">Todas as agências</option>
                  <option v-for="ag in agencias" :key="ag.id" :value="ag.agencia_nome">{{ ag.agencia_nome }}</option>
                </select>
              </div>
              <div>
                <label for="setor-busca" class="block text-xs font-semibold text-gray-600 mb-1.5">Busca</label>
                <input id="setor-busca" v-model="filtros.busca" type="text" @input="debounceCarregar" placeholder="Protocolo, viajante..." class="w-full text-sm border border-labs-border rounded-lg px-3 py-2.5">
              </div>
            </div>
          </section>

          <section v-if="carregando" class="glass-panel flex items-center justify-center py-16">
            <span class="text-sm font-medium text-gray-500">Carregando solicitações…</span>
          </section>

          <section v-else-if="solicitacoes.length" class="glass-panel card-accent-blue overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-sm" aria-label="Tabela de solicitações do setor">
                <thead>
                  <tr class="bg-labs-gray border-b border-labs-border">
                    <th scope="col" class="text-left px-4 py-3">Protocolo</th>
                    <th scope="col" class="text-left px-4 py-3">Viajante</th>
                    <th scope="col" class="text-left px-4 py-3 hidden md:table-cell">Destino</th>
                    <th scope="col" class="text-left px-4 py-3">Status</th>
                    <th scope="col" class="text-right px-4 py-3">Ações</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="s in solicitacoes" :key="s.id" class="row-hover">
                    <td class="px-4 py-3"><button type="button" class="font-mono font-bold text-labs-blue hover:underline" @click="abrirDetalhe(s)">{{ s.protocolo }}</button></td>
                    <td class="px-4 py-3">{{ s.solicitante_username }}</td>
                    <td class="px-4 py-3 hidden md:table-cell">{{ s.destino_cidade }}/{{ s.destino_estado }}</td>
                    <td class="px-4 py-3"><span :class="['text-[10px] font-semibold rounded-full px-2 py-0.5 border', statusCor(s.status)]">{{ statusLabel(s.status) }}</span></td>
                    <td class="px-4 py-3 text-right">
                      <div class="flex items-center justify-end gap-1 flex-wrap">
                        <button v-if="s.status === 'PENDENTE_PRE_APROVACAO_SETOR'" type="button" class="inline-flex text-[11px] bg-emerald-600 text-white rounded px-2 py-1" @click="confirmarAcao(s, 'PRE_APROVAR')">Aprovar</button>
                        <button v-if="s.status === 'PENDENTE_PRE_APROVACAO_SETOR'" type="button" class="inline-flex text-[11px] bg-red-50 text-red-700 border border-red-200 rounded px-2 py-1" @click="confirmarAcao(s, 'PRE_REPROVAR')">Negar</button>
                        <button v-if="s.status === 'AGUARDANDO_COTACAO' || s.status === 'COTACAO_ENVIADA'" type="button" class="inline-flex text-[11px] bg-blue-50 text-blue-700 border border-blue-200 rounded px-2 py-1" @click="confirmarAcao(s, 'REENVIAR_AGENCIAS')">Reenviar</button>
                        <button type="button" class="inline-flex text-[11px] bg-labs-gray text-gray-700 border border-labs-border rounded px-2 py-1" @click="abrirDetalhe(s)">Detalhes</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section v-else class="glass-panel flex flex-col items-center justify-center py-16 text-gray-400">
            <p class="text-sm font-medium">Nenhuma solicitação encontrada.</p>
          </section>
        </template>

        <template v-if="aba === 'indicadores'">
          <section class="glass-panel card-accent-blue p-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-bold text-gray-800">Exportações e Relatórios BI</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button type="button" @click="exportarSolicitacoes" class="px-3 py-2 text-xs font-semibold bg-blue-50 text-blue-700 rounded-lg border border-blue-200">Solicitações</button>
              <button type="button" @click="exportarStatus" class="px-3 py-2 text-xs font-semibold bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200">Por Status</button>
            </div>
          </section>
          <section class="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div v-for="kpi in kpis" :key="kpi.label" class="glass-panel p-4 border border-gray-100">
              <p class="text-xs text-gray-500">{{ kpi.label }}</p>
              <p class="text-2xl font-extrabold">{{ kpi.valor }}</p>
            </div>
          </section>
          <section class="glass-panel p-4">
            <h3 class="text-sm font-bold mb-3">Distribuição por Status</h3>
            <div v-if="distribuicaoStatus.length" class="space-y-3">
              <div v-for="item in distribuicaoStatus" :key="item.label">
                <div class="flex justify-between text-xs mb-1">
                  <span>{{ item.label }}</span>
                  <span>{{ item.count }} ({{ item.pct }}%)</span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div class="bar-fill h-2 rounded-full" :class="item.cor" :style="`width:${item.pct}%`" />
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-gray-500">Sem dados disponíveis.</p>
          </section>
          <section class="glass-panel p-4">
            <h3 class="text-sm font-bold mb-3">Volume Mensal</h3>
            <div class="flex items-end gap-2 h-32">
              <div v-for="m in volumeMensal" :key="m.mes" class="flex-1 flex flex-col items-center justify-end">
                <div class="w-full bg-blue-500 rounded-t" :style="`height:${Math.max(4, (m.total / maxMensal) * 100)}%`" />
                <span class="text-[10px] text-gray-500 mt-1">{{ m.mes }}</span>
              </div>
            </div>
          </section>
          <section class="glass-panel p-4">
            <h3 class="text-sm font-bold mb-3">Solicitações por Centro de Custo</h3>
            <div v-if="centroCustoRanking.length" class="space-y-2">
              <div v-for="(item, idx) in centroCustoRanking" :key="`${item.cod}-${idx}`" class="text-xs">
                <div class="flex justify-between mb-1">
                  <span>{{ item.cod }} {{ item.nome }}</span>
                  <span class="font-bold">{{ item.count }}</span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div class="bar-fill h-2 rounded-full bg-labs-blue" :style="`width:${Math.max(4, (item.count / maxCC) * 100)}%`" />
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-gray-500">Sem dados para consolidação.</p>
          </section>
        </template>

        <template v-if="aba === 'casamentos'">
          <section class="glass-panel card-accent-purple p-6">
            <h2 class="text-base font-bold text-gray-800 mb-1">🔗 Casamentos Detectados</h2>
            <p class="text-xs text-gray-400 mb-4">Pares de viagem que podem ser otimizados juntos.</p>
            <div v-if="casamentoMsgOk" class="mb-3 bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm">{{ casamentoMsgOk }}</div>
            <div v-if="casamentoMsgErr" class="mb-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{{ casamentoMsgErr }}</div>
            <div v-if="!casamentos.length" class="text-sm text-gray-400">Nenhum casamento pendente.</div>
            <div v-else class="space-y-3">
              <article v-for="c in casamentos" :key="c.id" class="border border-gray-200 rounded-xl p-4 bg-white">
                <div class="flex justify-between flex-wrap gap-2">
                  <span :class="[tipoCasamentoCor(c.tipo_match), 'text-xs font-bold rounded-full px-3 py-0.5']">{{ c.tipo_match }}</span>
                  <div class="flex gap-2">
                    <button type="button" class="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg" @click="agirCasamento(c.id, 'vincular')">Vincular</button>
                    <button type="button" class="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-lg" @click="agirCasamento(c.id, 'ignorar')">Ignorar</button>
                  </div>
                </div>
                <p class="mt-2 text-xs text-gray-600">{{ c.protocolo_a }} ↔ {{ c.protocolo_b }}</p>
              </article>
            </div>
          </section>
        </template>

        <template v-if="aba === 'agencias'">
          <section class="glass-panel p-6 card-accent-blue">
            <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
              <h2 class="text-base font-bold text-gray-800">Agências de Viagens</h2>
              <button type="button" @click="abrirModalAgencia(null)" class="px-4 py-2 bg-labs-blue text-white text-sm font-semibold rounded-lg">Nova Agência</button>
            </div>
            <div v-if="agenciaMsgOk" class="mb-3 bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm">{{ agenciaMsgOk }}</div>
            <div v-if="agenciaMsgErr" class="mb-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{{ agenciaMsgErr }}</div>
            <div v-if="!agencias.length" class="text-sm text-gray-400">Nenhuma agência cadastrada.</div>
            <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <article v-for="ag in agencias" :key="ag.id" class="border rounded-xl p-4 bg-white">
                <div class="flex justify-between items-start gap-2">
                  <div>
                    <p class="font-bold text-sm">{{ ag.agencia_nome }}</p>
                    <p class="text-xs text-gray-500">{{ ag.razao_social || '—' }}</p>
                    <p class="text-xs text-gray-500 font-mono">{{ ag.cnpj ? fmtCnpj(ag.cnpj) : 'CNPJ não informado' }}</p>
                  </div>
                  <span :class="ag.ativo ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-600 border-red-200'" class="text-[10px] font-bold px-2 py-0.5 rounded-full border">{{ ag.ativo ? 'Ativa' : 'Inativa' }}</span>
                </div>
                <div class="mt-3 flex gap-2">
                  <button type="button" class="px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded-lg border border-blue-200" @click="abrirModalAgencia(ag)">Editar</button>
                  <button type="button" class="px-3 py-1.5 text-xs bg-amber-50 text-amber-700 rounded-lg border border-amber-200" @click="toggleAgencia(ag)">{{ ag.ativo ? 'Desativar' : 'Ativar' }}</button>
                  <button type="button" class="px-3 py-1.5 text-xs bg-red-50 text-red-700 rounded-lg border border-red-200" @click="confirmarExcluirAgencia(ag)">Excluir</button>
                </div>
              </article>
            </div>
          </section>
        </template>

        <template v-if="aba === 'terceiros'">
          <section class="glass-panel card-accent-blue p-6">
            <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
              <h2 class="text-base font-bold text-gray-800">Tickets de Autorização para Terceiros</h2>
              <select v-model="filtroTerceirosStatus" class="text-xs border border-labs-border rounded-lg px-3 py-2" @change="carregarTicketsTerceiros">
                <option value="">Todos os status</option>
                <option value="PENDENTE">Apenas Pendentes</option>
                <option value="APROVADA">Aprovados</option>
                <option value="REPROVADA">Reprovados</option>
              </select>
            </div>
            <div v-if="!ticketsTerceiros.length" class="text-sm text-gray-400">Nenhum ticket encontrado.</div>
            <div v-else class="overflow-x-auto">
              <table class="w-full text-sm" aria-label="Tabela de tickets de terceiros">
                <thead>
                  <tr class="bg-labs-gray border-b border-labs-border text-gray-500 text-xs uppercase font-semibold">
                    <th scope="col" class="text-left px-4 py-3">Data</th>
                    <th scope="col" class="text-left px-4 py-3">Solicitante</th>
                    <th scope="col" class="text-left px-4 py-3">Terceiro</th>
                    <th scope="col" class="text-left px-4 py-3">Status</th>
                    <th scope="col" class="text-right px-4 py-3">Decisão</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="t in ticketsTerceiros" :key="t.id" class="row-hover text-xs">
                    <td class="px-4 py-3">{{ fmtData(t.data_criacao) }}</td>
                    <td class="px-4 py-3">{{ t.solicitante_username }}</td>
                    <td class="px-4 py-3">{{ t.terceiro_nome || t.terceiro_username }}</td>
                    <td class="px-4 py-3">{{ t.status }}</td>
                    <td class="px-4 py-3 text-right">
                      <div v-if="t.status === 'PENDENTE'" class="flex items-center justify-end gap-2">
                        <input v-model="ticketObs[t.id]" type="text" placeholder="Observações" class="px-2 py-1 text-xs border border-labs-border rounded-lg">
                        <button type="button" class="text-[11px] bg-emerald-600 text-white rounded px-2.5 py-1" @click="decidirTicket(t.id, 'APROVADA', ticketObs[t.id])">Aprovar</button>
                        <button type="button" class="text-[11px] bg-red-50 text-red-700 border border-red-200 rounded px-2.5 py-1" @click="decidirTicket(t.id, 'REPROVADA', ticketObs[t.id])">Negar</button>
                      </div>
                      <span v-else class="text-gray-500">Decidido por {{ t.operador_setor || '—' }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section v-if="alertasAcesso.length" class="glass-panel card-accent-purple p-6">
            <h2 class="text-base font-bold text-gray-800 mb-2">🛡️ Alertas de Onboarding (Acesso AD)</h2>
            <div class="overflow-x-auto">
              <table class="w-full text-sm" aria-label="Tabela de alertas de acesso">
                <thead>
                  <tr class="bg-labs-gray border-b border-labs-border text-gray-500 text-xs uppercase font-semibold">
                    <th scope="col" class="text-left px-4 py-3">Data/Hora</th>
                    <th scope="col" class="text-left px-4 py-3">Colaborador</th>
                    <th scope="col" class="text-left px-4 py-3">IP</th>
                    <th scope="col" class="text-left px-4 py-3">Detalhe</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="al in alertasAcesso" :key="al.id" class="row-hover text-xs">
                    <td class="px-4 py-3">{{ fmtDataHora(al.data_criacao) }}</td>
                    <td class="px-4 py-3">{{ al.username }}</td>
                    <td class="px-4 py-3">{{ al.ip_origem }}</td>
                    <td class="px-4 py-3 whitespace-pre-wrap">{{ al.observacao }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>

        <div class="text-center text-xs text-gray-600 mt-4">
          <button type="button" class="hover:text-labs-blue transition underline" @click="vlNavigate('/politica-privacidade.html')">
            Política de Privacidade
          </button>
        </div>
      </main>
    </div>

    <div v-if="modalAgenciaAberto" class="fixed inset-0 z-50 overflow-y-auto bg-labs-dark/70 backdrop-blur-sm flex items-start justify-center p-4 pt-6" @click.self="fecharModalAgencia">
      <div class="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-white/20 mb-8">
        <div class="bg-labs-blue px-6 py-4 flex items-center justify-between">
          <h3 class="text-white font-bold text-sm">{{ agenciaEditando ? 'Editar Agência' : 'Cadastrar Agência de Viagens' }}</h3>
          <button type="button" class="text-white/70 hover:text-white" @click="fecharModalAgencia">✕</button>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="sm:col-span-2">
              <label for="ag-cnpj" class="block text-xs font-semibold text-gray-600 mb-1">CNPJ *</label>
              <div class="flex gap-2">
                <input id="ag-cnpj" v-model="agenciaForm.cnpj" type="text" maxlength="18" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm" @input="mascararCnpj">
                <button type="button" class="px-4 py-2 text-xs font-semibold bg-labs-blue text-white rounded-lg disabled:opacity-50" :disabled="cnpjBuscando" @click="buscarCnpj">{{ cnpjBuscando ? 'Buscando…' : 'Consultar' }}</button>
              </div>
              <p v-if="cnpjErro" class="text-red-500 text-xs mt-1">{{ cnpjErro }}</p>
            </div>
            <div>
              <label for="ag-nome" class="block text-xs font-semibold text-gray-600 mb-1">Nome Fantasia *</label>
              <input id="ag-nome" v-model="agenciaForm.agencia_nome" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
            </div>
            <div>
              <label for="ag-email" class="block text-xs font-semibold text-gray-600 mb-1">E-mail de Contato *</label>
              <input id="ag-email" v-model="agenciaForm.email" type="email" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
            </div>
            <div>
              <label for="ag-cep" class="block text-xs font-semibold text-gray-600 mb-1">CEP</label>
              <input id="ag-cep" v-model="agenciaForm.cep" type="text" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" @blur="buscarCep">
            </div>
            <div>
              <label for="ag-banco" class="block text-xs font-semibold text-gray-600 mb-1">Código do Banco</label>
              <div class="flex gap-2">
                <input id="ag-banco" v-model="agenciaForm.banco_codigo" type="text" maxlength="3" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm" @input="agenciaForm.banco_codigo = agenciaForm.banco_codigo.replace(/\D/g, '').slice(0, 3)">
                <button type="button" class="px-3 py-2 text-xs bg-gray-100 rounded-lg" :disabled="bancoBuscando" @click="buscarBanco">{{ bancoBuscando ? '…' : 'Buscar' }}</button>
              </div>
            </div>
          </div>
          <div v-if="agenciaFormErr" class="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{{ agenciaFormErr }}</div>
        </div>
        <div class="px-6 pb-6 flex gap-3 justify-end border-t border-gray-100 pt-4">
          <button type="button" class="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg" @click="fecharModalAgencia">Cancelar</button>
          <button type="button" :disabled="agenciaFormLoading" class="px-6 py-2 text-sm font-semibold bg-labs-blue text-white rounded-lg disabled:opacity-50" @click="salvarAgencia">{{ agenciaFormLoading ? 'Salvando…' : (agenciaEditando ? 'Salvar Alterações' : 'Cadastrar Agência') }}</button>
        </div>
      </div>
    </div>

    <div v-if="modalAberto" class="fixed inset-0 z-50 flex items-start justify-center p-4 pt-8 bg-labs-dark/70 backdrop-blur-sm overflow-y-auto" @click.self="fecharModal">
      <div class="bg-white w-full max-w-2xl rounded-2xl shadow-2xl mb-10 overflow-hidden border border-white/20">
        <div class="h-1.5 w-full bg-labs-blue" />
        <div class="flex items-start justify-between px-6 py-5 border-b border-labs-border">
          <div>
            <h2 class="text-base font-bold text-labs-dark font-mono tracking-tight">{{ detalhe.protocolo }}</h2>
            <span :class="['text-xs font-semibold rounded-full px-3 py-0.5 border', statusCor(detalhe.status)]">{{ statusLabel(detalhe.status) }}</span>
          </div>
          <button type="button" class="text-gray-400 hover:text-gray-700" @click="fecharModal">✕</button>
        </div>
        <div class="px-6 py-5 space-y-4 max-h-[62vh] overflow-y-auto">
          <div v-if="detalhe.status === 'PENDENTE_APROVACAO_CANCELAMENTO' || detalhe.status === 'PENDENTE_APROVACAO_REMARCACAO'" class="border rounded-2xl p-4 bg-rose-50/20 border-rose-200">
            <p class="text-xs font-bold text-rose-800">Revisão de cancelamento/remarcação</p>
            <p class="text-xs text-gray-600 mt-1">Tipo: {{ detalhe.tipo_solicitacao_cancelamento || 'CANCELAR' }}</p>
            <p class="text-xs text-gray-600">Taxa: R$ {{ fmtValor(detalhe.taxa_cancelamento_agencia) }}</p>
            <p class="text-xs text-gray-600">Reembolso: R$ {{ fmtValor(detalhe.valor_reembolsavel_agencia) }}</p>
            <p class="text-xs mt-1" :class="isWithin24h(detalhe.data_criacao, detalhe.data_atualizacao) ? 'text-emerald-700' : 'text-rose-700'">
              {{ isWithin24h(detalhe.data_criacao, detalhe.data_atualizacao) ? 'Dentro das 24h' : 'Fora das 24h' }}
            </p>
          </div>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-xs text-gray-400 block">Solicitante</span>
              <strong>{{ detalhe.solicitante_username }}</strong>
            </div>
            <div>
              <span class="text-xs text-gray-400 block">Serviços</span>
              <span>{{ (detalhe.tipo_servico || '').replace(/,/g, ' · ') }}</span>
            </div>
            <div>
              <span class="text-xs text-gray-400 block">Ida</span>
              <span>{{ fmtData(detalhe.data_ida) }}</span>
            </div>
            <div>
              <span class="text-xs text-gray-400 block">Volta</span>
              <span>{{ detalhe.data_volta ? fmtData(detalhe.data_volta) : '—' }}</span>
            </div>
          </div>

          <div v-if="slotsCotacao.length" class="space-y-2">
            <h3 class="text-xs font-bold text-labs-dark uppercase tracking-wider">Cotações das Agências</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div v-for="slot in slotsCotacao" :key="slot.agencia" class="rounded-xl border p-3 bg-labs-gray">
                <p class="font-bold text-sm">{{ slot.agencia }}</p>
                <p v-if="slot.cot" class="text-xs text-gray-600">Total: R$ {{ fmtValor(slot.cot.valor_total) }}</p>
                <p v-else class="text-xs text-gray-400">Aguardando cotação...</p>
              </div>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-labs-border bg-labs-gray">
          <div v-if="acaoErro" class="mb-3 text-sm text-red-700 vl-red-error-surface px-4 py-2.5">{{ acaoErro }}</div>
          <div class="flex flex-wrap gap-2 justify-end">
            <button v-if="detalhe.status === 'PENDENTE_PRE_APROVACAO_SETOR'" type="button" :disabled="acaoCarregando" class="text-sm bg-emerald-600 text-white rounded-lg px-4 py-2.5 font-bold disabled:opacity-50" @click="executarAcao(detalhe, 'PRE_APROVAR')">✓ Pré-Aprovar</button>
            <button v-if="detalhe.status === 'PENDENTE_PRE_APROVACAO_SETOR'" type="button" :disabled="acaoCarregando" class="text-sm bg-red-50 text-red-700 border border-red-200 rounded-lg px-4 py-2.5 font-bold disabled:opacity-50" @click="executarAcao(detalhe, 'PRE_REPROVAR')">✕ Reprovar</button>

            <button v-if="detalhe.status === 'PENDENTE_APROVACAO_CANCELAMENTO' || detalhe.status === 'PENDENTE_APROVACAO_REMARCACAO'" type="button" :disabled="acaoCarregando" class="text-sm bg-emerald-600 text-white rounded-lg px-4 py-2.5 font-bold disabled:opacity-50" @click="decidirCancelamento(detalhe, 'APROVAR')">✓ Aprovar Cancelamento</button>
            <button v-if="detalhe.status === 'PENDENTE_APROVACAO_CANCELAMENTO' || detalhe.status === 'PENDENTE_APROVACAO_REMARCACAO'" type="button" :disabled="acaoCarregando" class="text-sm bg-rose-50 text-rose-700 border border-rose-200 rounded-lg px-4 py-2.5 font-bold disabled:opacity-50" @click="decidirCancelamento(detalhe, 'REPROVAR')">✕ Negar Cancelamento</button>

            <button v-if="detalhe.status === 'AGUARDANDO_COTACAO' || detalhe.status === 'COTACAO_ENVIADA'" type="button" :disabled="acaoCarregando" class="text-sm bg-blue-50 text-blue-700 border border-blue-200 rounded-lg px-4 py-2.5 font-bold disabled:opacity-50" @click="executarAcao(detalhe, 'REENVIAR_AGENCIAS')">↺ Reenviar E-mails</button>

            <button v-for="slot in slotsCotacao" :key="`acao-${slot.agencia}`" type="button" :disabled="acaoCarregando" class="text-sm bg-labs-blue text-white rounded-lg px-4 py-2.5 font-bold disabled:opacity-50" @click="executarAcao(detalhe, 'APROVAR_' + slot.agencia.toUpperCase())">🏆 Escolher {{ slot.agencia }}</button>

            <button type="button" class="text-sm bg-white border border-labs-border text-gray-600 rounded-lg px-4 py-2.5" @click="fecharModal">Fechar</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="confirmacao.aberto" class="fixed inset-0 z-50 flex items-center justify-center bg-labs-dark/70 backdrop-blur-sm p-4" @click.self="confirmacao.aberto = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
        <div class="h-1 w-full bg-labs-blue" />
        <div class="p-6">
          <h3 class="font-extrabold text-labs-dark mb-2">Confirmar Ação</h3>
          <p class="text-sm text-gray-600 mb-1"><strong>{{ acaoLabel(confirmacao.acao) }}</strong></p>
          <p class="text-sm text-gray-500 mb-4">Solicitação: <strong class="font-mono font-bold text-labs-blue">{{ confirmacao.sol?.protocolo }}</strong></p>
          <div class="flex gap-2 justify-end">
            <button type="button" class="text-sm border border-labs-border rounded-lg px-4 py-2" @click="confirmacao.aberto = false">Cancelar</button>
            <button type="button" :disabled="acaoCarregando" class="text-sm bg-labs-blue text-white rounded-lg px-5 py-2 font-bold disabled:opacity-50" @click="executarAcao(confirmacao.sol, confirmacao.acao)">{{ acaoCarregando ? 'Aguarde…' : 'Confirmar' }}</button>
          </div>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div v-show="mostrandoModalLGPDGestor && !aceitouLGPDGestor" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/80 backdrop-blur-sm">
        <div class="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
          <div class="bg-gradient-to-r from-indigo-600 to-purple-700 px-6 py-5">
            <h2 class="text-lg font-bold text-white">Termo de Responsabilidade - Acesso a Dados Pessoais</h2>
          </div>
          <div class="p-6 space-y-3 max-h-[70vh] overflow-y-auto text-sm text-gray-700">
            <p>Como <strong>operador de dados</strong> no sistema Viagens Labs, você terá acesso a dados pessoais protegidos pela LGPD.</p>
            <div class="vl-amber-alert-surface p-4 text-xs">
              <p><strong>⚠️ Responsabilidades:</strong></p>
              <ul class="list-disc list-inside space-y-1 mt-1">
                <li>Confidencialidade e uso estritamente operacional</li>
                <li>Não exportar dados para fora do sistema oficial</li>
                <li>Aceitar monitoramento e auditoria de acessos</li>
              </ul>
            </div>
            <div v-if="erroConsentimentoGestor" class="vl-red-error-surface p-3 text-xs text-red-700">{{ erroConsentimentoGestor }}</div>
          </div>
          <div class="px-6 py-4 border-t border-gray-100 flex justify-between items-center gap-3 shrink-0">
            <button type="button" class="px-3 py-2 border border-gray-300 text-gray-600 rounded-lg text-xs font-semibold" @click="sair">Rejeitar e Sair</button>
            <button type="button" :disabled="registrandoConsentimentoGestor" class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold disabled:opacity-50" @click="aceitarConsentimentoLGPDGestor">
              <span v-if="!registrandoConsentimentoGestor">✓ Aceitar Termos e Continuar</span>
              <span v-else>Processando...</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.glass-panel {
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.2);
}

.card-accent-blue {
  border-top: 3px solid #0055ff;
}

.card-accent-purple {
  border-top: 3px solid #7c3aed;
}

.row-hover {
  transition: background 0.15s;
}

.row-hover:hover {
  background: #f0f7ff;
}

.bar-fill {
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 3px;
}
</style>
