<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createApiClient } from '@/services/api-client.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()
const API = '/api/v1'
const logoLuizalabs = new URL('../../img/luizalabs-logo.png', import.meta.url).href

const tela = ref('login')
const token = ref('')
const nomeUsuario = ref('')
const loginForm = reactive({ username: '', password: '' })
const loginErro = ref('')
const loginCarregando = ref(false)
const abaAtiva = ref('dashboard')
const menuRecolhido = ref(false)

const tabs = [
  { id: 'dashboard', icon: '◈', label: 'Dashboard' },
  { id: 'solicitacoes', icon: '⊞', label: 'Solicitações' },
  { id: 'agencias', icon: '🏢', label: 'Agências' },
  { id: 'qa_suite', icon: '✅', label: 'Suite QA' },
  { id: 'qa_testers', icon: '🧪', label: 'Testadores QA' },
  { id: 'delegacoes_ad', icon: '👤', label: 'Delegações AD' },
  { id: 'logs', icon: '⌨', label: 'Logs do Sistema' },
  { id: 'logs_acesso', icon: '🛡', label: 'Histórico de Acessos' },
  { id: 'config', icon: '⚙', label: 'Configuração' },
  { id: 'plataforma', icon: '⬡', label: 'Plataforma' },
  { id: 'consultas_sql', icon: '⚡', label: 'Grandes Resultados' },
]

const portais = [
  { icon: '✈', nome: 'Portal do Viajante', desc: 'Solicitação de viagens', grupo: 'G_ACCESS_VIAGENSLABS_USERS', url: '/' },
  { icon: '🏢', nome: 'Portal do Setor', desc: 'Pré-aprovação e gestão', grupo: 'G_ACCESS_VIAGENSLABS_ADMINS', url: '/setor' },
  { icon: '🧳', nome: 'Portal da Agência', desc: 'Cotação e vouchers (token)', grupo: 'Link por e-mail', url: '/agencia' },
  { icon: '💻', nome: 'Portal Dev', desc: 'Gestão irrestrita', grupo: 'G_ACCESS_VIAGENSLABS_DEV', url: '/dev' },
]

const endpoints = [
  { method: 'POST', path: '/auth/login', perfil: 'todos', desc: 'Autenticação via AD' },
  { method: 'POST', path: '/viagens/solicitar', perfil: 'viajante', desc: 'Criar solicitação' },
  { method: 'GET', path: '/viagens/minhas', perfil: 'viajante', desc: 'Histórico do viajante' },
  { method: 'GET', path: '/setor/solicitacoes', perfil: 'setor', desc: 'Listar solicitações pendentes' },
  { method: 'POST', path: '/setor/solicitacoes/{id}/pre-aprovar', perfil: 'setor', desc: 'Pré-aprovar solicitação' },
  { method: 'POST', path: '/setor/solicitacoes/{id}/negar', perfil: 'setor', desc: 'Negar solicitação' },
  { method: 'GET', path: '/agencia/solicitacoes', perfil: 'agencia', desc: 'Listar para cotação' },
  { method: 'POST', path: '/agencia/solicitacoes/{id}/cotacao', perfil: 'agencia', desc: 'Enviar cotação' },
  { method: 'GET', path: '/aprovacao/{uuid}', perfil: 'token', desc: 'Consultar token de aprovação' },
  { method: 'POST', path: '/aprovacao/{uuid}/decidir', perfil: 'token', desc: 'Aprovar/Reprovar via e-mail' },
  { method: 'GET', path: '/dev/stats', perfil: 'dev', desc: 'Métricas globais' },
  { method: 'GET', path: '/dev/solicitacoes', perfil: 'dev', desc: 'Todas as solicitações' },
  { method: 'GET', path: '/dev/agencias', perfil: 'dev', desc: 'Listar agências' },
  { method: 'GET', path: '/dev/config', perfil: 'dev', desc: 'Configuração ativa' },
  { method: 'GET', path: '/dev/atividade', perfil: 'dev', desc: 'Feed de atividade recente' },
  { method: 'GET', path: '/dev/qa/suites', perfil: 'dev', desc: 'Lista suites QA disponíveis' },
  { method: 'POST', path: '/dev/qa/executar?mode={padrao|integration|completa}', perfil: 'dev', desc: 'Executa suite pytest no servidor' },
  { method: 'GET', path: '/dev/qa/jobs/{job_id}', perfil: 'dev', desc: 'Consulta status/logs de uma execução QA' },
  { method: 'POST', path: '/dev/qa/jobs/{job_id}/cancelar', perfil: 'dev', desc: 'Solicita cancelamento da execução QA' },
]

const qaSuites = ref([
  {
    mode: 'padrao',
    nome: 'Suite Padrão',
    desc: 'Testes rápidos de QA sem dependências externas.',
    cmd: '.\\venv\\Scripts\\python.exe -m pytest tests -m "not integration"',
  },
  {
    mode: 'integration',
    nome: 'Suite Integração (PostgreSQL)',
    desc: 'Valida schema e conectividade real com banco PostgreSQL.',
    cmd: '.\\venv\\Scripts\\python.exe -m pytest tests -m integration',
  },
  {
    mode: 'completa',
    nome: 'Suite Completa',
    desc: 'Executa todos os testes da pasta tests em uma única rodada.',
    cmd: '.\\venv\\Scripts\\python.exe -m pytest tests',
  },
])
const qaExecCarregando = ref(false)
const qaExecResultado = ref(null)
const qaExecErro = ref('')
const qaExecJob = ref(null)
const qaPollTimer = ref(null)
const qaCancelando = ref(false)
const qaSuitesCarregando = ref(false)

const statusOpcoes = [
  'AGUARDANDO_N1',
  'AGUARDANDO_N2',
  'PENDENTE_PRE_APROVACAO_SETOR',
  'AGUARDANDO_COTACAO',
  'EM_COTACAO',
  'COTACAO_RECEBIDA',
  'APROVADO',
  'REPROVADO',
  'CANCELADO',
]

const stats = ref(null)
const statsCarregando = ref(false)
const atividade = ref([])
const atividadeCarregando = ref(false)

const solicitacoes = ref([])
const solCarregando = ref(false)
const solTotal = ref(0)
const solOffset = ref(0)
const solFiltro = reactive({ busca: '', status: '' })

const agencias = ref([])
const agenciasCarregando = ref(false)

const config = ref(null)
const configCarregando = ref(false)
const configGrupos = [
  {
    titulo: 'URLs & Domínios',
    campos: [{ key: 'base_url' }, { key: 'base_url_agencia' }, { key: 'base_url_aprovacao' }],
  },
  {
    titulo: 'SMTP',
    campos: [{ key: 'smtp_host' }, { key: 'smtp_port' }, { key: 'smtp_from' }],
  },
  {
    titulo: 'Integrações',
    campos: [{ key: 'gas_relay_url' }, { key: 'gas_secret_ok' }, { key: 'google_places_key_ok' }],
  },
  {
    titulo: 'Active Directory',
    campos: [{ key: 'ad_base_dn' }, { key: 'ad_group_admins' }, { key: 'ad_group_dev' }, { key: 'ad_group_agencias' }],
  },
  {
    titulo: 'E-mails Operacionais',
    campos: [{ key: 'setor_email' }, { key: 'agencia_tastur_email' }, { key: 'agencia_kontrip_email' }, { key: 'qa_aprovador_email' }],
  },
  {
    titulo: 'Banco de Dados',
    campos: [{ key: 'database_url' }],
  },
]

const consultasPredefinidas = ref([
  {
    id: 'custos_cc',
    nome: 'Custos por Centro de Custo',
    desc: 'Extrai o volume de solicitações, custos totais reembolsados e total de multas agrupados por centro de custo.',
    sql: `SELECT 
    cod_centro_custo AS "Código CC", 
    centro_custo AS "Nome Centro de Custo", 
    COUNT(id) AS "Total Viagens", 
    COALESCE(SUM(valor_reembolsavel_agencia), 0) AS "Total Reembolsado (R$)",
    COALESCE(SUM(taxa_cancelamento_agencia), 0) AS "Total Multas (R$)"
FROM solicitacoes 
GROUP BY cod_centro_custo, centro_custo 
ORDER BY COUNT(id) DESC;`,
  },
  {
    id: 'market_share',
    nome: 'Market Share de Agências',
    desc: 'Determina a taxa de conversão e cotações vencidas de cada agência de viagem credenciada.',
    sql: `SELECT 
    agencia_nome AS "Agência de Viagem", 
    COUNT(id) AS "Total Cotações Recebidas",
    SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) AS "Cotações Vencidas (Aprovadas)",
    ROUND(100.0 * SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) / NULLIF(COUNT(id), 0), 2) || '%' AS "Taxa de Conversão"
FROM cotacoes 
GROUP BY agencia_nome 
ORDER BY SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) DESC;`,
  },
  {
    id: 'auditoria_delegacoes',
    nome: 'Auditoria de Delegações Dev',
    desc: 'Histórico auditado de inserções e exclusões manuais de assessores/terceiros executados pelo time de Dev.',
    sql: `SELECT 
    username AS "Usuário Dev", 
    nome AS "Nome do Dev", 
    perfil AS "Perfil", 
    observacao AS "Ação Auditada", 
    data_criacao AS "Data e Hora"
FROM log_acessos 
WHERE observacao LIKE '%Delegação manual%' 
ORDER BY data_criacao DESC;`,
  },
  {
    id: 'creditos_cia',
    nome: 'Créditos Acumulados por Cia',
    desc: 'Montante total de reembolsos gerados e créditos ativos que podem ser utilizados em novas solicitações.',
    sql: `SELECT 
    companhia_credito AS "Companhia Aérea", 
    COUNT(id) AS "Quantidade de Créditos",
    COALESCE(SUM(valor_credito_gerado), 0) AS "Total Créditos Acumulados (R$)"
FROM solicitacoes 
WHERE tipo_solicitacao_cancelamento = 'CANCELAR' 
  AND credito_utilizado = FALSE 
GROUP BY companhia_credito 
ORDER BY COALESCE(SUM(valor_credito_gerado), 0) DESC;`,
  },
])
const consultaAtivaId = ref('custos_cc')
const consultaResultados = ref(null)
const consultaCarregando = ref(false)
const consultaErro = ref('')

const qaTesters = ref([])
const qaTestersCarregando = ref(false)
const qaForm = reactive({ username: '', email: '' })
const qaFormErro = ref('')
const qaFormOk = ref(false)
const qaFormLoading = ref(false)

const delegacoes = ref([])
const delegacoesCarregando = ref(false)
const delForm = reactive({ solicitante: '', viajante: '' })
const delFormErro = ref('')
const delFormOk = ref('')
const delFormLoading = ref(false)
const solicitanteInfo = ref(null)
const solicitanteBuscando = ref(false)
const viajanteInfo = ref(null)
const viajanteBuscando = ref(false)

const reiniciandoBackend = ref(false)
const contadorRegressivo = ref(12)
const recarregandoNginx = ref(false)

const logServico = ref('app_out')
const logLinhas = ref(100)
const logPausado = ref(false)
const logConteudo = ref('')
const logCaminho = ref('')
const logCarregando = ref(false)

const logsAcesso = ref([])
const logsAcessoCarregando = ref(false)
const logsAcessoInterval = ref(null)

const excluirModal = reactive({ aberto: false, solicitacao: null, erro: '', carregando: false })

const apiClient = createApiClient({
  baseUrl: API,
  getToken: () => token.value,
  onUnauthorized: () => logout(),
})

const logsFormatados = computed(() => {
  if (!logConteudo.value) return []
  const linhas = logConteudo.value.split('\n')
  return linhas
    .map(linha => {
      const lTrim = linha.trim()
      if (!lTrim) return ''

      const mNginxErr = lTrim.match(/^(\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}) \[([a-z]+)\] (.*)$/)
      if (mNginxErr) {
        const [, timestamp, nivel, msg] = mNginxErr
        let badgeClass = 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
        let textClass = 'text-slate-300'
        if (nivel === 'crit' || nivel === 'alert' || nivel === 'emerg' || nivel === 'error' || nivel === 'err') {
          badgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20 font-bold'
          textClass = 'text-red-400/90 font-medium'
        } else if (nivel === 'warn' || nivel === 'warning') {
          badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold'
          textClass = 'text-amber-400/90'
        } else if (nivel === 'info' || nivel === 'notice') {
          badgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          textClass = 'text-blue-300/90'
        } else if (nivel === 'debug') {
          badgeClass = 'bg-slate-600/10 text-slate-500 border border-slate-500/10'
          textClass = 'text-slate-400/80'
        }
        return `<span class="text-slate-500 select-none shrink-0 font-semibold font-mono">${timestamp}</span><span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider shrink-0 select-none ${badgeClass}">${nivel}</span><span class="font-mono text-xs break-all ${textClass}">${msg}</span>`
      }

      const mFastApi = lTrim.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([A-Z]+)\] (.*)$/)
      if (mFastApi) {
        const [, timestamp, nivel, msg] = mFastApi
        let badgeClass = 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
        let textClass = 'text-slate-300'
        const n = nivel.toUpperCase()
        if (n === 'ERROR' || n === 'CRITICAL' || n === 'FATAL') {
          badgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20 font-bold'
          textClass = 'text-red-400/90 font-medium'
        } else if (n === 'WARNING' || n === 'WARN') {
          badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold'
          textClass = 'text-amber-400/90'
        } else if (n === 'INFO') {
          badgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          textClass = 'text-emerald-300/90'
        } else if (n === 'DEBUG') {
          badgeClass = 'bg-slate-600/10 text-slate-500 border border-slate-500/10'
          textClass = 'text-slate-400/80'
        }

        let msgFormatted = msg
        if (
          logServico.value === 'db_queries' ||
          msg.trim().startsWith('SELECT') ||
          msg.trim().startsWith('INSERT') ||
          msg.trim().startsWith('UPDATE') ||
          msg.trim().startsWith('DELETE') ||
          msg.trim().startsWith('COMMIT') ||
          msg.trim().startsWith('ROLLBACK') ||
          msg.trim().startsWith('BEGIN')
        ) {
          msgFormatted = msgFormatted
            .replace(/\b(FROM|WHERE|LEFT JOIN|INNER JOIN|RIGHT JOIN|JOIN|GROUP BY|ORDER BY|LIMIT|OFFSET|HAVING|UNION|INSERT INTO|VALUES|UPDATE|SET)\b/g, '<br>&nbsp;&nbsp;$1')
            .replace(/\b(AND|OR)\b/g, '<br>&nbsp;&nbsp;&nbsp;&nbsp;$1')
            .replace(/\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|LEFT|RIGHT|ON|GROUP BY|ORDER BY|LIMIT|OFFSET|HAVING|AND|OR|IN|AS|COMMIT|ROLLBACK|BEGIN|IMPLICIT|SET|VALUES|INSERT INTO|UNION)\b/g, '<span class="text-cyan-400 font-bold">$1</span>')
            .replace(/\b(NULL|TRUE|FALSE)\b/g, '<span class="text-amber-400 font-bold">$1</span>')
        }
        return `<span class="text-slate-500 select-none shrink-0 font-semibold font-mono">${timestamp}</span><span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider shrink-0 select-none ${badgeClass}">${n}</span><span class="font-mono text-xs break-all ${textClass}">${msgFormatted}</span>`
      }

      const mWinSW = lTrim.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+([A-Z]+)\s+-\s+(.*)$/)
      if (mWinSW) {
        const [, timestamp, nivel, msg] = mWinSW
        let badgeClass = 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
        let textClass = 'text-slate-300'
        const n = nivel.toUpperCase()
        if (n === 'ERROR' || n === 'CRITICAL' || n === 'FATAL') {
          badgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20 font-bold'
          textClass = 'text-red-400/90 font-medium'
        } else if (n === 'WARNING' || n === 'WARN') {
          badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold'
          textClass = 'text-amber-400/90'
        } else if (n === 'INFO') {
          badgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          textClass = 'text-blue-300/90'
        } else if (n === 'DEBUG') {
          badgeClass = 'bg-slate-600/10 text-slate-500 border border-slate-500/10'
          textClass = 'text-slate-400/80'
        }
        return `<span class="text-slate-500 select-none shrink-0 font-semibold font-mono">${timestamp.split(',')[0]}</span><span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider shrink-0 select-none ${badgeClass}">${n}</span><span class="font-mono text-xs break-all ${textClass}">${msg}</span>`
      }

      const mNginxAcc = lTrim.match(/^([\d.]+) - - \[(.*?)\] "(.*?)" (\d+) (\d+)(?: "(.*?)" "(.*?)")?$/)
      if (mNginxAcc) {
        const [, ip, rawTime, req, status] = mNginxAcc
        let displayTime = rawTime
        try {
          const parts = rawTime.split(':')
          const datePart = parts[0]
          const h = parts[1]
          const min = parts[2]
          const s = parts[3].split(' ')[0]
          const dParts = datePart.split('/')
          const meses = { Jan: '01', Feb: '02', Mar: '03', Apr: '04', May: '05', Jun: '06', Jul: '07', Aug: '08', Sep: '09', Oct: '10', Nov: '11', Dec: '12' }
          displayTime = `${dParts[2]}-${meses[dParts[1]] || '05'}-${dParts[0].padStart(2, '0')} ${h}:${min}:${s}`
        } catch {
          // noop
        }

        const st = Number.parseInt(status, 10)
        let badgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
        let textClass = 'text-slate-300'
        if (st >= 500) {
          badgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20 font-bold'
          textClass = 'text-red-400/90 font-medium'
        } else if (st >= 400) {
          badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold'
          textClass = 'text-amber-400/80'
        } else if (st >= 300) {
          badgeClass = 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
          textClass = 'text-slate-400'
        } else if (st >= 200) {
          badgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          textClass = 'text-emerald-300/90'
        }
        return `<span class="text-slate-500 select-none shrink-0 font-semibold font-mono">${displayTime}</span><span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider shrink-0 select-none ${badgeClass}">HTTP ${status}</span><span class="text-indigo-400 select-none font-mono text-xs shrink-0">${ip}</span><span class="font-mono text-xs break-all ${textClass}">${req}</span>`
      }

      const mLegacyUvicorn = lTrim.match(/^([A-Z]+):\s+(.*)$/)
      if (mLegacyUvicorn) {
        const [, nivel, msg] = mLegacyUvicorn
        let badgeClass = 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
        let textClass = 'text-slate-300'
        const n = nivel.toUpperCase()
        if (n === 'ERROR' || n === 'CRITICAL' || n === 'FATAL') {
          badgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20 font-bold'
          textClass = 'text-red-400/90'
        } else if (n === 'WARNING' || n === 'WARN') {
          badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold'
          textClass = 'text-amber-400/90'
        } else if (n === 'INFO') {
          badgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          textClass = 'text-emerald-400'
        }
        return `<span class="text-slate-500 select-none shrink-0 font-semibold font-mono">—</span><span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider shrink-0 select-none ${badgeClass}">${n}</span><span class="font-mono text-xs break-all ${textClass}">${msg}</span>`
      }

      let badgeClass = 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
      let textClass = 'text-[#34d399]/90'
      let n = 'LOG'
      const uLine = lTrim.toUpperCase()
      if (uLine.includes('ERROR') || uLine.includes('ERR:') || uLine.includes('CRIT') || uLine.includes('FAIL') || uLine.includes('EXCEPTION')) {
        badgeClass = 'bg-red-500/10 text-red-400 border border-red-500/20 font-bold'
        textClass = 'text-red-400/90'
        n = 'ERR'
      } else if (uLine.includes('WARN') || uLine.includes('WARNING')) {
        badgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold'
        textClass = 'text-amber-400/90'
        n = 'WRN'
      } else if (uLine.includes('DEBUG') || uLine.includes('TRAC')) {
        badgeClass = 'bg-slate-600/10 text-slate-500 border border-slate-500/10'
        textClass = 'text-slate-400/80'
        n = 'DBG'
      } else if (uLine.includes('INFO') || uLine.includes('SUCCESS') || uLine.includes('STARTING') || uLine.includes('STOPPING')) {
        badgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
        textClass = 'text-slate-300'
        n = 'INF'
      }

      return `<span class="text-slate-500 select-none shrink-0 font-semibold font-mono">—</span><span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider shrink-0 select-none ${badgeClass}">${n}</span><span class="font-mono text-xs break-all ${textClass}">${lTrim}</span>`
    })
    .filter(Boolean)
})

function hidratarSessao() {
  const authToken = authStore.getToken()
  const authNome = authStore.nome

  const legacyDevToken = window.localStorage.getItem('vl:dev:token')
  const legacyDevNome = window.localStorage.getItem('vl:dev:nome')
  const legacyToken = window.localStorage.getItem('token')
  const legacyNome = window.localStorage.getItem('nome_usuario')

  token.value = authToken || legacyDevToken || legacyToken || ''
  nomeUsuario.value = authNome || legacyDevNome || legacyNome || ''

  if (token.value) authStore.setToken(token.value)
  if (nomeUsuario.value) authStore.setNome(nomeUsuario.value)
}

function persistirSessao(dados, usernameFallback = '') {
  token.value = dados.access_token || ''
  nomeUsuario.value = dados.nome_usuario || usernameFallback

  authStore.setToken(token.value)
  authStore.setNome(nomeUsuario.value)
  authStore.setPerfil(dados.perfil || 'dev')
  authStore.setUsername(usernameFallback)

  window.localStorage.setItem('vl:dev:token', token.value)
  window.localStorage.setItem('vl:dev:nome', nomeUsuario.value)
}

function limparTimers() {
  if (qaPollTimer.value) {
    clearInterval(qaPollTimer.value)
    qaPollTimer.value = null
  }
  if (logInterval.value) {
    clearInterval(logInterval.value)
    logInterval.value = null
  }
  if (logsAcessoInterval.value) {
    clearInterval(logsAcessoInterval.value)
    logsAcessoInterval.value = null
  }
  if (reinicioInterval.value) {
    clearInterval(reinicioInterval.value)
    reinicioInterval.value = null
  }
  if (qaSearchTimer) clearTimeout(qaSearchTimer)
  if (solSearchTimer) clearTimeout(solSearchTimer)
  if (viajSearchTimer) clearTimeout(viajSearchTimer)
}

function logout() {
  authStore.clearAll()
  token.value = ''
  nomeUsuario.value = ''
  tela.value = 'login'
  window.localStorage.removeItem('vl:dev:token')
  window.localStorage.removeItem('vl:dev:nome')
  window.localStorage.removeItem('token')
  window.localStorage.removeItem('nome_usuario')
  window.localStorage.removeItem('perfil')
  limparTimers()
}

async function realizarLogin() {
  if (!loginForm.username || !loginForm.password) {
    loginErro.value = 'Preencha usuário e senha.'
    return
  }

  loginCarregando.value = true
  loginErro.value = ''
  try {
    const res = await apiClient.request('/auth/login', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ username: loginForm.username, password: loginForm.password }),
    })
    const dados = res.data
    if (!res.ok) {
      loginErro.value = dados?.detail || 'Erro ao autenticar.'
      return
    }
    if (dados.perfil !== 'dev') {
      loginErro.value = `Acesso negado. Seu perfil é "${dados.perfil}". Necessário: G_ACCESS_VIAGENSLABS_DEV.`
      return
    }

    persistirSessao(dados, loginForm.username)
    tela.value = 'portal'
    await Promise.all([carregarStats(), carregarAtividade()])
  } catch {
    loginErro.value = 'Falha de comunicação com a API.'
  } finally {
    loginCarregando.value = false
  }
}

function qaStatusClass(status) {
  if (status === 'success') return 'text-green-400 border-green-500/40 bg-green-500/10'
  if (status === 'failed') return 'text-red-400 border-red-500/40 bg-red-500/10'
  if (status === 'running') return 'text-amber-300 border-amber-500/40 bg-amber-500/10'
  if (status === 'canceling') return 'text-amber-300 border-amber-500/40 bg-amber-500/10'
  if (status === 'canceled') return 'text-slate-300 border-slate-500/40 bg-slate-500/10'
  return 'text-slate-300 border-slate-500/40 bg-slate-500/10'
}

function qaStatusLabel(status) {
  if (status === 'success') return 'Sucesso'
  if (status === 'failed') return 'Falha'
  if (status === 'running') return 'Em execução'
  if (status === 'canceling') return 'Cancelando'
  if (status === 'canceled') return 'Cancelado'
  return 'Em fila'
}

function podeCancelarQa(status) {
  return status === 'queued' || status === 'running' || status === 'canceling'
}

async function carregarQASuites() {
  qaSuitesCarregando.value = true
  try {
    const res = await apiClient.request('/dev/qa/suites')
    const d = res.data
    if (res.ok && Array.isArray(d?.suites) && d.suites.length) qaSuites.value = d.suites
  } catch {
    // fallback para lista local
  } finally {
    qaSuitesCarregando.value = false
  }
}

function pararPollingQa() {
  if (qaPollTimer.value) {
    clearInterval(qaPollTimer.value)
    qaPollTimer.value = null
  }
}

async function buscarStatusQaJobSilencioso() {
  if (!qaExecJob.value?.job_id) return
  try {
    const res = await apiClient.request(`/dev/qa/jobs/${encodeURIComponent(qaExecJob.value.job_id)}`)
    const d = res.data
    if (!res.ok) return

    qaExecResultado.value = d
    qaExecJob.value = d

    if (d.status === 'success' || d.status === 'failed' || d.status === 'canceled') {
      qaExecCarregando.value = false
      qaCancelando.value = false
      pararPollingQa()
    }
  } catch {
    // polling silencioso
  }
}

async function cancelarQASuite() {
  if (!qaExecJob.value?.job_id || !podeCancelarQa(qaExecJob.value.status)) return
  qaCancelando.value = true
  qaExecErro.value = ''
  try {
    const res = await apiClient.request(`/dev/qa/jobs/${encodeURIComponent(qaExecJob.value.job_id)}/cancelar`, {
      method: 'POST',
    })
    const d = res.data
    if (!res.ok) {
      qaExecErro.value = d?.detail || 'Erro ao cancelar execução QA.'
      qaCancelando.value = false
      return
    }
    await buscarStatusQaJobSilencioso()
  } catch {
    qaExecErro.value = 'Falha de comunicação ao cancelar execução QA.'
    qaCancelando.value = false
  }
}

async function executarQASuite(mode) {
  pararPollingQa()
  qaExecCarregando.value = true
  qaCancelando.value = false
  qaExecErro.value = ''
  qaExecResultado.value = null
  qaExecJob.value = null

  try {
    const res = await apiClient.request(`/dev/qa/executar?mode=${encodeURIComponent(mode)}`, {
      method: 'POST',
    })
    const d = res.data
    if (!res.ok) {
      qaExecErro.value = d?.detail || 'Erro ao executar suite QA.'
      qaExecCarregando.value = false
      return
    }

    qaExecJob.value = d
    qaExecResultado.value = {
      command: `pytest (${mode})`,
      status: 'queued',
      success: null,
      exit_code: '-',
      duration_seconds: '-',
      output: '[QA] Aguardando início da execução...\n',
    }

    await buscarStatusQaJobSilencioso()
    qaPollTimer.value = setInterval(buscarStatusQaJobSilencioso, 1000)
  } catch {
    qaExecErro.value = 'Falha de comunicação ao executar suite QA.'
    qaExecCarregando.value = false
  }
}

async function carregarStats() {
  statsCarregando.value = true
  try {
    const res = await apiClient.request('/dev/stats')
    if (res.ok) stats.value = res.data
  } finally {
    statsCarregando.value = false
  }
}

async function carregarAtividade() {
  atividadeCarregando.value = true
  try {
    const res = await apiClient.request('/dev/atividade?limit=20')
    if (res.ok) atividade.value = res.data
  } finally {
    atividadeCarregando.value = false
  }
}

async function carregarSolicitacoes(reset = false) {
  if (reset) solOffset.value = 0
  solCarregando.value = true
  try {
    const params = new URLSearchParams({ limit: '50', offset: String(solOffset.value) })
    if (solFiltro.status) params.append('status', solFiltro.status)
    if (solFiltro.busca) params.append('busca', solFiltro.busca)
    const res = await apiClient.request(`/dev/solicitacoes?${params.toString()}`)
    if (!res.ok) return
    const dados = res.data || {}
    solicitacoes.value = dados.itens || []
    solTotal.value = dados.total || 0
  } finally {
    solCarregando.value = false
  }
}

async function carregarAgencias() {
  agenciasCarregando.value = true
  try {
    const res = await apiClient.request('/dev/agencias')
    if (res.ok) agencias.value = res.data
  } finally {
    agenciasCarregando.value = false
  }
}

async function toggleAgencia(ag) {
  const res = await apiClient.request(`/dev/agencias/${ag.id}/toggle-ativa`, { method: 'PATCH' })
  if (res.ok) ag.ativo = res.data?.ativo
}

async function carregarConfig() {
  configCarregando.value = true
  try {
    const res = await apiClient.request('/dev/config')
    if (res.ok) config.value = res.data
  } finally {
    configCarregando.value = false
  }
}

function corStatus(status) {
  const mapa = {
    AGUARDANDO_N1: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30',
    AGUARDANDO_N2: 'bg-orange-500/10 text-orange-400 border border-orange-500/30',
    PENDENTE_PRE_APROVACAO_SETOR: 'bg-purple-500/10 text-purple-400 border border-purple-500/30',
    AGUARDANDO_COTACAO: 'bg-blue-500/10 text-blue-400 border border-blue-500/30',
    EM_COTACAO: 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30',
    COTACAO_RECEBIDA: 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30',
    APROVADO: 'bg-green-500/10 text-green-400 border border-green-500/30',
    REPROVADO: 'bg-red-500/10 text-red-400 border border-red-500/30',
    CANCELADO: 'bg-slate-500/10 text-slate-400 border border-slate-500/30',
  }
  return mapa[status] || 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
}

function corBarraStatus(status) {
  const mapa = {
    AGUARDANDO_N1: 'bg-yellow-400',
    AGUARDANDO_N2: 'bg-orange-400',
    PENDENTE_PRE_APROVACAO_SETOR: 'bg-purple-400',
    AGUARDANDO_COTACAO: 'bg-blue-400',
    EM_COTACAO: 'bg-cyan-400',
    COTACAO_RECEBIDA: 'bg-indigo-400',
    APROVADO: 'bg-green-400',
    REPROVADO: 'bg-red-400',
    CANCELADO: 'bg-slate-500',
  }
  return mapa[status] || 'bg-slate-500'
}

function formatarCnpj(cnpj) {
  if (!cnpj) return '—'
  const limpo = cnpj.replace(/\D/g, '')
  if (limpo.length !== 14) return cnpj
  return limpo.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')
}

function formatarData(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('pt-BR')
}

function formatarTempo(dt) {
  if (!dt) return '—'
  const diff = Date.now() - new Date(dt).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 60) return `${min}m atrás`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h}h atrás`
  return `${Math.floor(h / 24)}d atrás`
}

function selecionarConsulta(id) {
  consultaAtivaId.value = id
  consultaResultados.value = null
  consultaErro.value = ''
}

function getConsultaAtiva() {
  return consultasPredefinidas.value.find(q => q.id === consultaAtivaId.value) || consultasPredefinidas.value[0]
}

async function copiarSql(text) {
  if (!text) return
  await navigator.clipboard.writeText(text)
  window.alert('SQL copiado para a área de transferência!')
}

async function executarConsulta() {
  consultaCarregando.value = true
  consultaErro.value = ''
  consultaResultados.value = null
  try {
    const res = await apiClient.request('/dev/consultas/executar', {
      method: 'POST',
      body: JSON.stringify({ query_id: consultaAtivaId.value }),
    })
    const dados = res.data
    if (!res.ok) {
      consultaErro.value = dados?.detail || 'Erro ao executar consulta.'
      return
    }
    consultaResultados.value = dados
  } catch {
    consultaErro.value = 'Falha de conexão ao executar consulta.'
  } finally {
    consultaCarregando.value = false
  }
}

async function carregarQATesters() {
  qaTestersCarregando.value = true
  try {
    const res = await apiClient.request('/dev/usuarios-qa')
    if (res.ok) qaTesters.value = res.data
  } finally {
    qaTestersCarregando.value = false
  }
}

async function salvarQATester() {
  if (!qaForm.username || !qaForm.email) {
    qaFormErro.value = 'Preencha o username e o e-mail.'
    return
  }

  qaFormLoading.value = true
  qaFormErro.value = ''
  qaFormOk.value = false
  try {
    const res = await apiClient.request('/dev/usuarios-qa', {
      method: 'POST',
      body: JSON.stringify({ username: qaForm.username, email: qaForm.email }),
    })
    const d = res.data
    if (!res.ok) {
      qaFormErro.value = d?.detail || 'Erro ao cadastrar.'
      return
    }
    qaFormOk.value = true
    qaForm.username = ''
    qaForm.email = ''
    await carregarQATesters()
  } finally {
    qaFormLoading.value = false
  }
}

async function removerQATester(t) {
  if (!window.confirm(`Remover testador QA "${t.username}"?`)) return
  const res = await apiClient.request(`/dev/usuarios-qa/${t.id}`, { method: 'DELETE' })
  if (res.ok) await carregarQATesters()
}

let qaSearchTimer = null
watch(
  () => qaForm.username,
  newVal => {
    if (qaSearchTimer) clearTimeout(qaSearchTimer)
    const username = newVal.trim()
    if (!username) return

    qaSearchTimer = setTimeout(async () => {
      try {
        const res = await apiClient.request(`/viagens/colaborador/${username}`)
        if (res.ok && res.data?.sucesso && res.data?.dados?.email) qaForm.email = res.data.dados.email
      } catch {
        // noop
      }
    }, 400)
  },
)

async function carregarDelegacoes() {
  delegacoesCarregando.value = true
  try {
    const res = await apiClient.request('/dev/delegacoes')
    if (res.ok) delegacoes.value = res.data
  } finally {
    delegacoesCarregando.value = false
  }
}

async function salvarDelegacao() {
  if (!delForm.solicitante || !delForm.viajante) {
    delFormErro.value = 'Preencha ambos os campos.'
    return
  }

  delFormLoading.value = true
  delFormErro.value = ''
  delFormOk.value = ''
  try {
    const res = await apiClient.request('/dev/delegacoes', {
      method: 'POST',
      body: JSON.stringify({ solicitante: delForm.solicitante, viajante: delForm.viajante }),
    })
    const d = res.data
    if (!res.ok) {
      delFormErro.value = d?.detail || 'Erro ao cadastrar.'
      return
    }
    delFormOk.value = '✓ Delegação cadastrada e aprovada com sucesso!'
    delForm.solicitante = ''
    delForm.viajante = ''
    solicitanteInfo.value = null
    viajanteInfo.value = null
    await carregarDelegacoes()
  } finally {
    delFormLoading.value = false
  }
}

async function removerDelegacao(d) {
  if (!window.confirm(`Excluir delegação manual de "${d.solicitante}" para "${d.terceiro_username}"?`)) return
  const res = await apiClient.request(`/dev/delegacoes/${d.id}`, { method: 'DELETE' })
  if (res.ok) await carregarDelegacoes()
}

let solSearchTimer = null
watch(
  () => delForm.solicitante,
  newVal => {
    if (solSearchTimer) clearTimeout(solSearchTimer)
    solicitanteInfo.value = null
    const username = newVal.trim()
    if (!username) return
    solicitanteBuscando.value = true

    solSearchTimer = setTimeout(async () => {
      try {
        const res = await apiClient.request(`/viagens/colaborador/${username}`)
        if (res.ok && res.data?.sucesso) solicitanteInfo.value = res.data.dados
      } catch {
        // noop
      } finally {
        solicitanteBuscando.value = false
      }
    }, 400)
  },
)

let viajSearchTimer = null
watch(
  () => delForm.viajante,
  newVal => {
    if (viajSearchTimer) clearTimeout(viajSearchTimer)
    viajanteInfo.value = null
    const username = newVal.trim()
    if (!username) return
    viajanteBuscando.value = true

    viajSearchTimer = setTimeout(async () => {
      try {
        const res = await apiClient.request(`/viagens/colaborador/${username}`)
        if (res.ok && res.data?.sucesso) viajanteInfo.value = res.data.dados
      } catch {
        // noop
      } finally {
        viajanteBuscando.value = false
      }
    }, 400)
  },
)

async function recarregarServicoNginx() {
  recarregandoNginx.value = true
  try {
    const res = await apiClient.request('/dev/servicos/recarregar-nginx', { method: 'POST' })
    const d = res.data
    if (res.ok && d?.sucesso) {
      window.alert('✓ Nginx recarregado com sucesso!')
    } else {
      window.alert(`⚠ Erro ao recarregar Nginx: ${d?.detail || d?.mensagem || 'Erro desconhecido'}`)
    }
  } catch {
    window.alert('⚠ Falha de comunicação ao recarregar o Nginx.')
  } finally {
    recarregandoNginx.value = false
  }
}

const reinicioInterval = ref(null)

function iniciarContadorReinicio() {
  reiniciandoBackend.value = true
  contadorRegressivo.value = 12
  reinicioInterval.value = setInterval(() => {
    contadorRegressivo.value -= 1
    if (contadorRegressivo.value <= 0) {
      clearInterval(reinicioInterval.value)
      reinicioInterval.value = null
      window.location.reload()
    }
  }, 1000)
}

async function reiniciarServicoBackend() {
  if (!window.confirm('Deseja realmente reiniciar o serviço do backend (ViagensLabs)? O portal ficará temporariamente indisponível por 12 segundos.')) return

  try {
    const res = await apiClient.request('/dev/servicos/reiniciar-backend', { method: 'POST' })
    if (res.ok) {
      iniciarContadorReinicio()
    } else {
      const d = res.data
      window.alert(`⚠ Erro ao iniciar reinicialização: ${d?.detail || d?.mensagem || 'Erro desconhecido'}`)
    }
  } catch {
    iniciarContadorReinicio()
  }
}

async function carregarLogs(showLoading = true) {
  if (showLoading) logCarregando.value = true
  try {
    const params = new URLSearchParams({ servico: logServico.value, linhas: String(logLinhas.value) })
    const res = await apiClient.request(`/dev/logs?${params.toString()}`)
    if (!res.ok) return
    logConteudo.value = res.data?.conteudo || ''
    logCaminho.value = res.data?.caminho || ''
  } finally {
    logCarregando.value = false
  }
}

function limparLogsConsole() {
  logConteudo.value = ''
}

async function carregarLogsAcesso(showLoading = true) {
  if (showLoading) logsAcessoCarregando.value = true
  try {
    const res = await apiClient.request('/dev/logs-acesso')
    if (res.ok) logsAcesso.value = res.data
  } finally {
    logsAcessoCarregando.value = false
  }
}

function formatarDataHora(dt) {
  if (!dt) return '—'
  const d = new Date(dt)
  return `${d.toLocaleDateString('pt-BR')} ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
}

function solicitarExcluir(s) {
  Object.assign(excluirModal, { aberto: true, solicitacao: s, erro: '', carregando: false })
}

async function confirmarExclusaoCascade() {
  excluirModal.carregando = true
  excluirModal.erro = ''
  try {
    const res = await apiClient.request(`/dev/solicitacoes/${excluirModal.solicitacao.id}`, {
      method: 'DELETE',
    })
    if (!res.ok) {
      excluirModal.erro = res.data?.detail || 'Erro ao excluir solicitação.'
      return
    }
    excluirModal.aberto = false
    await carregarSolicitacoes()
    await carregarStats()
  } finally {
    excluirModal.carregando = false
  }
}

function irPara(url) {
  if (url === '/') {
    router.push('/')
    return
  }
  if (url.startsWith('/')) {
    router.push(url)
    return
  }
  window.location.href = url
}

const logInterval = ref(null)
watch(abaAtiva, aba => {
  if (aba === 'solicitacoes' && !solicitacoes.value.length) void carregarSolicitacoes()
  if (aba === 'agencias' && !agencias.value.length) void carregarAgencias()
  if (aba === 'config' && !config.value) void carregarConfig()
  if (aba === 'qa_testers') void carregarQATesters()
  if (aba === 'qa_suite') void carregarQASuites()
  if (aba === 'delegacoes_ad') void carregarDelegacoes()

  if (aba === 'logs') {
    void carregarLogs()
    if (logInterval.value) clearInterval(logInterval.value)
    logInterval.value = setInterval(() => {
      if (!logPausado.value) void carregarLogs(false)
    }, 3000)
  } else if (logInterval.value) {
    clearInterval(logInterval.value)
    logInterval.value = null
  }

  if (aba === 'logs_acesso') {
    void carregarLogsAcesso()
    if (logsAcessoInterval.value) clearInterval(logsAcessoInterval.value)
    logsAcessoInterval.value = setInterval(() => {
      void carregarLogsAcesso(false)
    }, 5000)
  } else if (logsAcessoInterval.value) {
    clearInterval(logsAcessoInterval.value)
    logsAcessoInterval.value = null
  }
})

onMounted(async () => {
  if (typeof window._vlReady === 'function') window._vlReady()
  hidratarSessao()

  if (token.value) {
    try {
      const res = await apiClient.request('/dev/stats')
      if (res.ok) {
        tela.value = 'portal'
        stats.value = res.data
        await carregarAtividade()
      } else {
        logout()
      }
    } catch {
      logout()
    }
  }
})

onBeforeUnmount(() => {
  limparTimers()
})
</script>

<template>
  <div class="dev-page min-h-screen font-sans antialiased text-slate-300 vl-font-inter">
    <div v-if="tela === 'login'" class="min-h-screen flex items-center justify-center p-4" style="background: radial-gradient(ellipse at 60% 20%, rgba(99,102,241,0.15) 0%, transparent 60%), #0a0f1e;">
      <div class="w-full max-w-sm">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 mb-4 glow">
            <svg class="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-white tracking-tight">Portal do Desenvolvedor</h1>
          <p class="text-slate-500 text-xs mt-1 font-mono">G_ACCESS_VIAGENSLABS_DEV</p>
        </div>

        <div class="bg-dev-card border border-dev-border rounded-2xl p-6">
          <div v-if="loginErro" class="mb-4 p-3 bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg" role="status" aria-live="polite">
            {{ loginErro }}
          </div>
          <div class="space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide" for="dev-login-username">Usuário AD</label>
              <input id="dev-login-username" v-model="loginForm.username" type="text" autocomplete="username" placeholder="username" class="w-full bg-dev-panel border border-dev-border text-slate-200 rounded-lg px-3 py-2.5 text-sm font-mono focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 placeholder-slate-600" @keyup.enter="realizarLogin">
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide" for="dev-login-password">Senha</label>
              <input id="dev-login-password" v-model="loginForm.password" type="password" autocomplete="current-password" placeholder="••••••••" class="w-full bg-dev-panel border border-dev-border text-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 placeholder-slate-600" @keyup.enter="realizarLogin">
            </div>
            <button type="button" :disabled="loginCarregando" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg text-sm transition disabled:opacity-60 flex items-center justify-center gap-2" @click="realizarLogin">
              <svg v-if="loginCarregando" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ loginCarregando ? 'Autenticando…' : 'Entrar' }}
            </button>
          </div>
          <p class="text-center text-slate-600 text-xs mt-4">Acesso restrito — grupo AD obrigatório</p>
        </div>
      </div>
    </div>

    <div v-else-if="tela === 'portal'" class="min-h-screen flex bg-dev-bg text-slate-300 w-full relative">
      <aside :class="menuRecolhido ? 'w-20' : 'w-64'" class="bg-dev-panel text-slate-300 flex flex-col shrink-0 border-r border-dev-border min-h-screen transition-all duration-300 z-30 relative shadow-2xl">
        <div class="p-5 flex flex-col items-center border-b border-dev-border gap-2 select-none">
          <img :src="logoLuizalabs" alt="Luizalabs" :class="menuRecolhido ? 'h-6' : 'h-8'" class="object-contain shrink-0" loading="lazy" @error="event => { event.target.style.display = 'none' }">
          <div v-if="!menuRecolhido" class="text-center">
            <span class="text-[10px] font-mono text-indigo-400 block tracking-widest leading-none uppercase font-bold mt-1">Viagens</span>
          </div>
        </div>

        <nav class="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto" aria-label="Navegação do Portal Dev">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            :class="abaAtiva === tab.id ? 'bg-indigo-600/15 text-indigo-400 border-l-4 border-indigo-500 font-bold rounded-lg' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/20 border-l-4 border-transparent rounded-lg'"
            class="w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-all duration-200 text-left"
            @click="abaAtiva = tab.id"
          >
            <span class="text-base shrink-0">{{ tab.icon }}</span>
            <span v-if="!menuRecolhido" class="truncate flex-1">{{ tab.label }}</span>
          </button>

          <div class="pt-4 border-t border-dev-border mt-4 space-y-1.5">
            <p v-if="!menuRecolhido" class="text-[10px] text-slate-500 font-bold uppercase tracking-wider px-3">Portais</p>
            <button type="button" class="w-full flex items-center gap-3 px-3 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/20 rounded-lg transition-all" @click="irPara('/')">
              <span class="text-base shrink-0">✈️</span>
              <span v-if="!menuRecolhido">Portal do Viajante</span>
            </button>
            <button type="button" class="w-full flex items-center gap-3 px-3 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/20 rounded-lg transition-all" @click="irPara('/setor')">
              <span class="text-base shrink-0">🏢</span>
              <span v-if="!menuRecolhido">Painel do Setor</span>
            </button>
          </div>
        </nav>

        <div class="p-4 border-t border-dev-border flex flex-col gap-3 shrink-0">
          <button type="button" class="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800/20 border border-slate-700/30 hover:bg-slate-800/30 text-slate-400 hover:text-slate-200 rounded-lg text-[10px] font-mono transition" @click="menuRecolhido = !menuRecolhido">
            <span>{{ menuRecolhido ? '▶' : '◀ Recolher' }}</span>
          </button>
        </div>
      </aside>

      <div class="flex-grow flex flex-col min-w-0 min-h-screen">
        <header class="bg-dev-panel border-b border-dev-border px-6 py-3 flex items-center justify-between sticky top-0 z-20 shadow-lg">
          <div class="flex items-center gap-3 min-w-0">
            <span class="text-sm font-bold text-white tracking-tight uppercase">
              {{ tabs.find(t => t.id === abaAtiva)?.label }}
            </span>
            <span class="h-4 w-px bg-dev-border hidden sm:block" />
            <p class="text-xs text-slate-500 truncate hidden sm:block font-mono">Console de Gerenciamento & Auditoria da Plataforma</p>
          </div>

          <div class="flex items-center gap-3 shrink-0">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span class="text-xs font-mono text-slate-400">{{ nomeUsuario }}</span>
            </div>
            <button type="button" class="ml-2 text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-red-500/10 px-2.5 py-1.5 rounded-lg border border-red-500/20 hover:border-red-500/50 transition" @click="logout">
              Sair
            </button>
          </div>
        </header>

        <main class="flex-grow p-6 overflow-auto w-full">
          <div v-if="abaAtiva === 'dashboard'">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h2 class="text-xl font-bold text-white">Dashboard</h2>
                <p class="text-slate-500 text-xs mt-0.5">Visão geral da plataforma em tempo real</p>
              </div>
              <button type="button" :disabled="statsCarregando" class="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-dev-card border border-dev-border rounded-lg text-slate-400 hover:text-slate-200 transition" @click="carregarStats">
                <svg :class="statsCarregando ? 'animate-spin' : ''" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Atualizar
              </button>
            </div>

            <div v-if="stats" class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div class="bg-indigo-950/25 border border-indigo-500/30 rounded-2xl p-5 relative overflow-hidden transition duration-300 hover:shadow-indigo-500/10 hover:shadow-lg hover:-translate-y-0.5">
                <div class="absolute -right-6 -bottom-6 w-16 h-16 bg-indigo-500/15 rounded-full blur-xl" />
                <p class="text-xs text-indigo-300 uppercase tracking-wider font-bold">Total Solicitações</p>
                <p class="text-3xl font-extrabold text-white mt-2 leading-none font-mono">{{ stats.total_solicitacoes }}</p>
              </div>
              <div class="bg-cyan-950/25 border border-cyan-500/30 rounded-2xl p-5 relative overflow-hidden transition duration-300 hover:shadow-cyan-500/10 hover:shadow-lg hover:-translate-y-0.5">
                <div class="absolute -right-6 -bottom-6 w-16 h-16 bg-cyan-500/15 rounded-full blur-xl" />
                <p class="text-xs text-cyan-300 uppercase tracking-wider font-bold">Agências Ativas</p>
                <p class="text-3xl font-extrabold text-dev-cyan mt-2 leading-none font-mono">{{ stats.total_agencias }}</p>
              </div>
              <div class="bg-amber-950/25 border border-amber-500/30 rounded-2xl p-5 relative overflow-hidden transition duration-300 hover:shadow-amber-500/10 hover:shadow-lg hover:-translate-y-0.5">
                <div class="absolute -right-6 -bottom-6 w-16 h-16 bg-amber-500/15 rounded-full blur-xl" />
                <p class="text-xs text-amber-300 uppercase tracking-wider font-bold">Cotações</p>
                <p class="text-3xl font-extrabold text-dev-yellow mt-2 leading-none font-mono">{{ stats.total_cotacoes }}</p>
              </div>
              <div class="bg-emerald-950/25 border border-emerald-500/30 rounded-2xl p-5 relative overflow-hidden transition duration-300 hover:shadow-emerald-500/10 hover:shadow-lg hover:-translate-y-0.5">
                <div class="absolute -right-6 -bottom-6 w-16 h-16 bg-emerald-500/15 rounded-full blur-xl" />
                <p class="text-xs text-emerald-300 uppercase tracking-wider font-bold">Vouchers</p>
                <p class="text-3xl font-extrabold text-dev-green mt-2 leading-none font-mono">{{ stats.total_vouchers }}</p>
              </div>
            </div>

            <div v-if="stats" class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              <div class="bg-dev-card border border-dev-border rounded-xl p-4">
                <h3 class="text-sm font-semibold text-slate-300 mb-3">Distribuição por Status</h3>
                <div class="space-y-2">
                  <div v-for="(count, status) in stats.por_status" :key="status" class="flex items-center gap-3">
                    <span :class="corStatus(status)" class="badge-status w-44 text-center">{{ status.replace(/_/g, ' ') }}</span>
                    <div class="flex-1 bg-dev-panel rounded-full h-1.5 overflow-hidden">
                      <div class="h-full rounded-full transition-all duration-500" :class="corBarraStatus(status)" :style="{ width: Math.round((count / stats.total_solicitacoes) * 100) + '%' }" />
                    </div>
                    <span class="text-xs font-mono text-slate-400 w-8 text-right">{{ count }}</span>
                  </div>
                </div>
              </div>

              <div class="bg-dev-card border border-dev-border rounded-xl p-4">
                <h3 class="text-sm font-semibold text-slate-300 mb-3">Atividade Recente</h3>
                <div v-if="atividadeCarregando" class="flex justify-center py-4">
                  <div class="animate-spin w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full" />
                </div>
                <div v-else class="space-y-2 max-h-64 overflow-y-auto pr-1">
                  <div v-for="a in atividade" :key="a.protocolo + a.atualizado_em" class="flex items-start justify-between gap-2 py-1.5 border-b border-dev-border/50 last:border-0">
                    <div class="min-w-0">
                      <p class="text-xs font-mono text-indigo-300">{{ a.protocolo }}</p>
                      <p class="text-[10px] text-slate-500 truncate">{{ a.viajante }} → {{ a.destino }}</p>
                    </div>
                    <div class="shrink-0 text-right">
                      <span :class="corStatus(a.status)" class="badge-status">{{ a.status.replace(/_/g, ' ').slice(0, 12) }}</span>
                      <p class="text-[10px] text-slate-600 mt-0.5">{{ formatarTempo(a.atualizado_em) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 class="text-sm font-semibold text-slate-300 mb-3">Portais da Plataforma</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <button v-for="p in portais" :key="p.url" type="button" class="text-left bg-dev-card border border-dev-border hover:border-indigo-500/50 rounded-xl p-4 transition group cursor-pointer block" @click="irPara(p.url)">
                  <div class="text-3xl mb-2">{{ p.icon }}</div>
                  <p class="text-sm font-semibold text-slate-200 group-hover:text-white transition">{{ p.nome }}</p>
                  <p class="text-xs text-slate-500 mt-0.5">{{ p.desc }}</p>
                  <p class="text-[10px] font-mono text-indigo-400/60 mt-2">{{ p.grupo }}</p>
                </button>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'solicitacoes'">
            <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
              <h2 class="text-xl font-bold text-white">Solicitações</h2>
              <div class="flex gap-2 flex-wrap">
                <input v-model="solFiltro.busca" placeholder="Protocolo, usuário, destino…" class="bg-dev-card border border-dev-border text-sm text-slate-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500 placeholder-slate-600 w-56 font-mono" @input="carregarSolicitacoes(true)">
                <select v-model="solFiltro.status" class="bg-dev-card border border-dev-border text-sm text-slate-300 px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500" @change="carregarSolicitacoes(true)">
                  <option value="">Todos os status</option>
                  <option v-for="s in statusOpcoes" :key="s" :value="s">{{ s }}</option>
                </select>
                <button type="button" class="px-3 py-1.5 bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 rounded-lg text-sm hover:bg-indigo-600/30 transition" @click="carregarSolicitacoes(true)">
                  Filtrar
                </button>
              </div>
            </div>
            <div class="bg-dev-card border border-dev-border rounded-xl overflow-hidden">
              <div v-if="solCarregando" class="flex justify-center py-10">
                <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
              </div>
              <div v-else-if="!solicitacoes.length" class="text-center py-10 text-slate-500 text-sm">Nenhuma solicitação encontrada.</div>
              <div v-else class="overflow-x-auto">
                <table class="w-full text-xs" aria-label="Tabela de solicitações">
                  <thead class="border-b border-dev-border">
                    <tr class="text-slate-500 uppercase tracking-wide text-[10px]">
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Protocolo</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Viajante</th>
                      <th class="px-4 py-3 text-left font-semibold hidden md:table-cell" scope="col">Destino</th>
                      <th class="px-4 py-3 text-left font-semibold hidden lg:table-cell" scope="col">Serviço</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Status</th>
                      <th class="px-4 py-3 text-left font-semibold hidden lg:table-cell" scope="col">Criado</th>
                      <th class="px-4 py-3 text-right font-semibold" scope="col">Ações</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dev-border/50">
                    <tr v-for="s in solicitacoes" :key="s.id" class="hover:bg-dev-panel/50 transition">
                      <td class="px-4 py-3 font-mono text-indigo-300">{{ s.protocolo }}</td>
                      <td class="px-4 py-3">
                        <p class="text-slate-200 font-semibold">{{ s.viajante_nome || s.solicitante }}</p>
                        <p class="text-slate-500 font-mono text-[10px]">{{ s.solicitante }}</p>
                      </td>
                      <td class="px-4 py-3 text-slate-400 hidden md:table-cell">{{ s.destino }}</td>
                      <td class="px-4 py-3 text-slate-400 hidden lg:table-cell">{{ s.tipo_servico }}</td>
                      <td class="px-4 py-3"><span :class="corStatus(s.status)" class="badge-status">{{ s.status.replace(/_/g, ' ') }}</span></td>
                      <td class="px-4 py-3 text-slate-500 font-mono hidden lg:table-cell">{{ formatarData(s.data_criacao) }}</td>
                      <td class="px-4 py-3 text-right">
                        <button type="button" class="text-red-400 hover:text-red-300 hover:bg-red-500/10 px-2 py-1 rounded-lg border border-transparent hover:border-red-500/30 transition shrink-0 inline-flex items-center gap-1" @click="solicitarExcluir(s)">
                          🗑 Excluir
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div class="flex items-center justify-between px-4 py-3 border-t border-dev-border">
                  <span class="text-xs text-slate-500">{{ solTotal }} solicitações no total</span>
                  <div class="flex gap-2">
                    <button type="button" :disabled="solOffset === 0" class="px-3 py-1 text-xs bg-dev-panel border border-dev-border text-slate-400 rounded-lg disabled:opacity-40" @click="solOffset = Math.max(0, solOffset - 50); carregarSolicitacoes()">← Anterior</button>
                    <button type="button" :disabled="solOffset + 50 >= solTotal" class="px-3 py-1 text-xs bg-dev-panel border border-dev-border text-slate-400 rounded-lg disabled:opacity-40" @click="solOffset += 50; carregarSolicitacoes()">Próxima →</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'agencias'">
            <div class="flex items-center justify-between mb-5">
              <h2 class="text-xl font-bold text-white">Agências de Viagens</h2>
              <button type="button" class="text-xs px-3 py-1.5 bg-dev-card border border-dev-border text-slate-300 hover:text-slate-100 rounded-lg transition" @click="carregarAgencias">Recarregar</button>
            </div>
            <div v-if="agenciasCarregando" class="flex justify-center py-10">
              <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <div v-for="ag in agencias" :key="ag.id" class="bg-dev-card border border-dev-border rounded-xl p-5 flex flex-col justify-between hover:border-indigo-500/40 transition-all duration-300">
                <div>
                  <div class="flex items-start justify-between mb-3 gap-3">
                    <div class="min-w-0">
                      <p class="font-bold text-slate-100 truncate text-sm" :title="ag.agencia_nome">{{ ag.agencia_nome || 'Sem Nome' }}</p>
                      <p class="text-[10px] text-slate-300 italic truncate mt-0.5" :title="ag.razao_social">{{ ag.razao_social || 'Sem Razão Social' }}</p>
                    </div>
                    <span :class="ag.ativo ? 'bg-green-500/10 text-green-400 border-green-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30'" class="text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase shrink-0">
                      {{ ag.ativo ? 'ATIVA' : 'INATIVA' }}
                    </span>
                  </div>
                  <div class="space-y-2 mb-4 text-xs">
                    <div class="flex items-center gap-1.5">
                      <span class="text-slate-400 font-medium w-16">CNPJ:</span>
                      <span class="font-mono text-slate-200">{{ formatarCnpj(ag.cnpj) }}</span>
                    </div>
                    <div class="flex items-center gap-1.5 truncate">
                      <span class="text-slate-400 font-medium w-16">E-mail:</span>
                      <span class="truncate font-mono text-slate-200" :title="ag.email">{{ ag.email || '—' }}</span>
                    </div>
                    <div v-if="ag.municipio" class="flex items-center gap-1.5">
                      <span class="text-slate-400 font-medium w-16">Município:</span>
                      <span class="text-slate-200 font-medium">{{ ag.municipio }}/{{ ag.uf }}</span>
                    </div>
                    <div v-if="ag.banco_nome" class="flex items-start gap-1.5">
                      <span class="text-slate-400 font-medium w-16 shrink-0">Banco:</span>
                      <span class="text-slate-200 leading-tight">
                        {{ ag.banco_nome }}
                        <span class="text-[10px] text-slate-300 font-mono block mt-0.5">(Ag {{ ag.agencia_bancaria }} · CC {{ ag.conta_bancaria }})</span>
                      </span>
                    </div>
                  </div>
                </div>
                <div class="flex mt-auto pt-3 border-t border-dev-border/40">
                  <button type="button" class="w-full py-1.5 text-xs font-semibold rounded-lg border transition" :class="ag.ativo ? 'border-red-500/40 text-red-400 hover:bg-red-500/10' : 'border-green-500/40 text-green-400 hover:bg-green-500/10'" @click="toggleAgencia(ag)">
                    {{ ag.ativo ? 'Desativar Agência' : 'Ativar Agência' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'config'">
            <div class="flex items-center justify-between mb-5">
              <h2 class="text-xl font-bold text-white">Configuração do Sistema</h2>
              <button type="button" class="text-xs px-3 py-1.5 bg-dev-card border border-dev-border text-slate-400 hover:text-slate-200 rounded-lg transition" @click="carregarConfig">Recarregar</button>
            </div>
            <div v-if="configCarregando" class="flex justify-center py-10">
              <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
            </div>
            <div v-else-if="config" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div v-for="grupo in configGrupos" :key="grupo.titulo" class="bg-dev-card border border-dev-border rounded-xl p-4">
                <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">{{ grupo.titulo }}</h3>
                <div class="space-y-2">
                  <div v-for="campo in grupo.campos" :key="campo.key" class="flex items-center justify-between gap-2 py-1.5 border-b border-dev-border/40 last:border-0">
                    <span class="text-xs text-slate-500 font-mono flex-1">{{ campo.key }}</span>
                    <span class="text-xs font-mono" :class="config[campo.key] === '(não configurado)' || config[campo.key] === '(desativado)' ? 'text-slate-600' : config[campo.key] === true ? 'text-green-400' : config[campo.key] === false ? 'text-red-400' : 'text-slate-200'">
                      {{ config[campo.key] === true ? '✓ OK' : config[campo.key] === false ? '✗ NÃO' : config[campo.key] }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'plataforma'">
            <h2 class="text-xl font-bold text-white mb-6">Plataforma & Portais</h2>

            <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Portais de Acesso</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div v-for="p in portais" :key="p.url" class="bg-dev-card border border-dev-border rounded-xl p-5 hover:border-indigo-500/50 transition">
                <div class="text-4xl mb-3">{{ p.icon }}</div>
                <p class="font-bold text-white text-sm mb-1">{{ p.nome }}</p>
                <p class="text-xs text-slate-500 mb-3">{{ p.desc }}</p>
                <div class="text-[10px] font-mono text-slate-600 mb-3">Grupo: {{ p.grupo }}</div>
                <button type="button" class="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition" @click="irPara(p.url)">
                  Abrir portal →
                </button>
              </div>
            </div>

            <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Endpoints Principais da API</h3>
            <div class="bg-dev-card border border-dev-border rounded-xl overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full text-xs" aria-label="Tabela de endpoints da API">
                  <thead class="border-b border-dev-border bg-dev-panel">
                    <tr class="text-slate-500 uppercase text-[10px] tracking-wide">
                      <th class="px-4 py-3 text-left" scope="col">Método</th>
                      <th class="px-4 py-3 text-left" scope="col">Endpoint</th>
                      <th class="px-4 py-3 text-left" scope="col">Perfil</th>
                      <th class="px-4 py-3 text-left" scope="col">Descrição</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dev-border/40">
                    <tr v-for="ep in endpoints" :key="ep.path" class="hover:bg-dev-panel/30">
                      <td class="px-4 py-2.5"><span :class="ep.method === 'GET' ? 'text-green-400' : ep.method === 'POST' ? 'text-yellow-400' : ep.method === 'PATCH' ? 'text-blue-400' : 'text-red-400'" class="font-mono font-bold text-[11px]">{{ ep.method }}</span></td>
                      <td class="px-4 py-2.5 font-mono text-indigo-300 text-[11px]">{{ ep.path }}</td>
                      <td class="px-4 py-2.5"><span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 border border-dev-border">{{ ep.perfil }}</span></td>
                      <td class="px-4 py-2.5 text-slate-400">{{ ep.desc }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'qa_suite'">
            <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
              <div>
                <h2 class="text-xl font-bold text-white">Suite QA (Pytest)</h2>
                <p class="text-slate-500 text-xs mt-0.5">Execução oficial de QA diretamente do Portal Dev.</p>
              </div>
              <button type="button" class="text-xs px-3 py-1.5 bg-dev-card border border-dev-border text-slate-400 hover:text-slate-200 rounded-lg transition" @click="qaExecResultado = null; qaExecErro = ''">
                Limpar Resultado
              </button>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
              <div v-for="suite in qaSuites" :key="suite.mode" class="bg-dev-card border border-dev-border rounded-xl p-4 hover:border-indigo-500/40 transition">
                <div class="flex items-start justify-between gap-2 mb-2">
                  <h3 class="text-sm font-bold text-white">{{ suite.nome }}</h3>
                  <span class="text-[10px] px-2 py-0.5 rounded-full border border-dev-border text-slate-400 uppercase font-bold">{{ suite.mode }}</span>
                </div>
                <p class="text-xs text-slate-500 mb-3 leading-relaxed">{{ suite.desc }}</p>
                <p class="text-[10px] text-indigo-300 font-mono bg-dev-panel border border-dev-border rounded-lg px-2 py-1 mb-3 break-all">{{ suite.cmd }}</p>
                <button type="button" :disabled="qaExecCarregando" class="w-full bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-600/30 rounded-lg py-2 text-xs font-semibold transition disabled:opacity-60" @click="executarQASuite(suite.mode)">
                  {{ qaExecCarregando ? 'Executando...' : 'Executar' }}
                </button>
              </div>
            </div>

            <div v-if="qaSuitesCarregando" class="mb-4 text-xs text-slate-500">Carregando catálogo de suites...</div>

            <div v-if="qaExecErro" class="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-300" role="status" aria-live="polite">
              {{ qaExecErro }}
            </div>

            <div v-if="qaExecJob" class="mb-4 p-3 bg-dev-card border border-dev-border rounded-lg text-xs text-slate-300 flex items-center justify-between gap-3 flex-wrap">
              <div class="font-mono">Job: {{ qaExecJob.job_id }}</div>
              <div class="flex items-center gap-2">
                <span :class="qaStatusClass(qaExecJob.status)" class="text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase">{{ qaExecJob.status }}</span>
                <span v-if="qaExecJob.pid" class="text-[10px] text-slate-500 font-mono">pid={{ qaExecJob.pid }}</span>
                <button type="button" :disabled="qaCancelando || !podeCancelarQa(qaExecJob.status)" class="text-[10px] px-2 py-1 rounded border border-red-500/30 text-red-300 bg-red-500/10 hover:bg-red-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition" @click="cancelarQASuite">
                  {{ qaCancelando ? 'Cancelando...' : 'Cancelar' }}
                </button>
              </div>
            </div>

            <div v-if="qaExecResultado" class="bg-dev-card border border-dev-border rounded-xl overflow-hidden">
              <div class="px-4 py-3 border-b border-dev-border flex items-center justify-between gap-2 flex-wrap">
                <div class="text-xs text-slate-300 font-mono">{{ qaExecResultado.command }}</div>
                <div class="flex items-center gap-2">
                  <span :class="qaStatusClass(qaExecResultado.status || (qaExecResultado.success ? 'success' : 'failed'))" class="text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase">
                    {{ qaStatusLabel(qaExecResultado.status || (qaExecResultado.success ? 'success' : 'failed')) }}
                  </span>
                  <span class="text-[10px] text-slate-500 font-mono">exit={{ qaExecResultado.exit_code }} | {{ qaExecResultado.duration_seconds }}s</span>
                </div>
              </div>
              <pre class="p-4 text-[11px] font-mono text-slate-300 bg-dev-panel overflow-auto max-h-[420px] whitespace-pre-wrap">{{ qaExecResultado.output }}</pre>
            </div>
          </div>

          <div v-if="abaAtiva === 'qa_testers'">
            <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
              <div>
                <h2 class="text-xl font-bold text-white">Testadores QA</h2>
                <p class="text-slate-500 text-xs mt-0.5">Cadastre usuários QA cujos e-mails de solicitação serão desviados para testes.</p>
              </div>
              <button type="button" class="text-xs px-3 py-1.5 bg-dev-card border border-dev-border text-slate-400 hover:text-slate-200 rounded-lg transition" @click="carregarQATesters">Recarregar</button>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div class="bg-dev-card border border-dev-border rounded-xl p-5 h-fit glow">
                <h3 class="text-sm font-bold text-white mb-3">Novo Testador QA</h3>
                <div class="space-y-4">
                  <div>
                    <label class="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide" for="qa-username">Username AD (Luizalabs)</label>
                    <input id="qa-username" v-model="qaForm.username" type="text" placeholder="ex: fulano.silva" class="w-full bg-dev-panel border border-dev-border text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600 font-mono">
                  </div>
                  <div>
                    <label class="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide" for="qa-email">E-mail de Redirecionamento</label>
                    <input id="qa-email" v-model="qaForm.email" type="email" placeholder="ex: qa.teste@magazineluiza.com.br" class="w-full bg-dev-panel border border-dev-border text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600">
                  </div>
                  <div v-if="qaFormErro" class="text-xs text-red-400">{{ qaFormErro }}</div>
                  <div v-if="qaFormOk" class="text-xs text-green-400">✓ Testador cadastrado com sucesso!</div>
                  <button type="button" :disabled="qaFormLoading" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 rounded-lg text-xs transition disabled:opacity-60" @click="salvarQATester">
                    {{ qaFormLoading ? 'Cadastrando…' : 'Cadastrar' }}
                  </button>
                </div>
              </div>

              <div class="lg:col-span-2 bg-dev-card border border-dev-border rounded-xl p-5">
                <h3 class="text-sm font-bold text-white mb-3">Testadores Ativos</h3>
                <div v-if="qaTestersCarregando" class="flex justify-center py-6">
                  <div class="animate-spin w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full" />
                </div>
                <div v-else-if="!qaTesters.length" class="text-center py-6 text-slate-500 text-xs">Nenhum testador QA ativo cadastrado.</div>
                <div v-else class="space-y-3">
                  <div v-for="t in qaTesters" :key="t.id" class="flex items-center justify-between p-3 bg-dev-panel border border-dev-border/60 rounded-xl">
                    <div>
                      <span class="text-sm font-bold text-white font-mono">{{ t.username }}</span>
                      <span class="text-xs text-slate-500 block mt-0.5">{{ t.email }}</span>
                    </div>
                    <button type="button" class="text-red-400 hover:text-red-300 text-xs font-semibold px-2.5 py-1.5 rounded border border-red-500/20 hover:border-red-500/50 transition bg-red-500/5" @click="removerQATester(t)">
                      Excluir
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'logs_acesso'">
            <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
              <div>
                <h2 class="text-xl font-bold text-white">Histórico de Acessos</h2>
                <p class="text-slate-500 text-xs mt-0.5">Trilha de auditoria em tempo real de logins e conexões na ferramenta</p>
              </div>
              <div class="flex items-center gap-2">
                <button type="button" :disabled="logsAcessoCarregando" class="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-dev-card border border-dev-border rounded-lg text-slate-400 hover:text-slate-200 transition" @click="carregarLogsAcesso">
                  <svg :class="logsAcessoCarregando ? 'animate-spin' : ''" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Atualizar
                </button>
              </div>
            </div>
            <div class="bg-dev-card border border-dev-border rounded-xl overflow-hidden glow">
              <div v-if="logsAcessoCarregando" class="flex justify-center py-10">
                <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
              </div>
              <div v-else-if="!logsAcesso.length" class="text-center py-10 text-slate-500 text-sm">Nenhum registro de acesso encontrado.</div>
              <div v-else class="overflow-x-auto">
                <table class="w-full text-xs" aria-label="Tabela de logs de acesso">
                  <thead class="border-b border-dev-border">
                    <tr class="text-slate-500 uppercase tracking-wide text-[10px]">
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Data/Hora</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Usuário AD</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Nome Completo</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Perfil</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">IP de Origem</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Status</th>
                      <th class="px-4 py-3 text-left font-semibold" scope="col">Detalhes</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dev-border/50">
                    <tr v-for="l in logsAcesso" :key="l.id" class="hover:bg-dev-panel/50 transition">
                      <td class="px-4 py-3 text-slate-400 font-mono">{{ formatarDataHora(l.data_criacao) }}</td>
                      <td class="px-4 py-3 font-mono font-bold text-indigo-300">{{ l.username }}</td>
                      <td class="px-4 py-3 text-slate-200">{{ l.nome || '—' }}</td>
                      <td class="px-4 py-3">
                        <span v-if="l.perfil === 'dev'" class="bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">Developer</span>
                        <span v-else-if="l.perfil === 'setor'" class="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">Setor Viagens</span>
                        <span v-else-if="l.perfil === 'viajante'" class="bg-slate-500/10 text-slate-400 border border-slate-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">Viajante</span>
                        <span v-else-if="l.perfil === 'agencia'" class="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">Agência</span>
                        <span v-else class="text-slate-500">—</span>
                      </td>
                      <td class="px-4 py-3 text-slate-400 font-mono">{{ l.ip_origem }}</td>
                      <td class="px-4 py-3">
                        <span v-if="l.status_acesso === 'SUCESSO'" class="bg-green-500/10 text-green-400 border border-green-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">Sucesso</span>
                        <span v-else class="bg-red-500/10 text-red-400 border border-red-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">Bloqueado</span>
                      </td>
                      <td class="px-4 py-3 text-slate-400 truncate max-w-xs" :title="l.observacao">{{ l.observacao || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'logs'">
            <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
              <div>
                <h2 class="text-xl font-bold text-white">Logs do Sistema</h2>
                <p class="text-slate-500 text-xs mt-0.5">Acompanhamento em tempo real de logs do FastAPI e do Nginx</p>
              </div>
              <div class="flex items-center gap-2 flex-wrap">
                <label class="sr-only" for="log-servico">Serviço de log</label>
                <select id="log-servico" v-model="logServico" class="bg-dev-card border border-dev-border text-xs text-slate-300 px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500 bg-dev-panel" @change="carregarLogs">
                  <option value="app_out">FastAPI (viagenslabs_service.out.log)</option>
                  <option value="app_err">FastAPI Errors (viagenslabs_service.err.log)</option>
                  <option value="db_queries">Banco de Dados (viagenslabs_db.log)</option>
                  <option value="nginx_access">Nginx Access (access.log)</option>
                  <option value="nginx_error">Nginx Error (error.log)</option>
                  <option value="nginx_service_err">Nginx Service Wrapper (viagenslabs_service.wrapper.log)</option>
                </select>

                <label class="sr-only" for="log-linhas">Quantidade de linhas</label>
                <select id="log-linhas" v-model="logLinhas" class="bg-dev-card border border-dev-border text-xs text-slate-300 px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500 w-28 bg-dev-panel" @change="carregarLogs">
                  <option :value="50">50 linhas</option>
                  <option :value="100">100 linhas</option>
                  <option :value="200">200 linhas</option>
                  <option :value="500">500 linhas</option>
                </select>

                <button type="button" :class="logPausado ? 'bg-amber-600/20 border-amber-500/40 text-amber-300' : 'bg-green-600/20 border-green-500/40 text-green-300'" class="px-3 py-1.5 border rounded-lg text-xs font-semibold transition" @click="logPausado = !logPausado">
                  {{ logPausado ? '⏸ Pausado' : '⚡ Auto-Refresh' }}
                </button>
                <button type="button" class="px-3 py-1.5 bg-dev-card border border-dev-border text-slate-400 hover:text-slate-200 rounded-lg text-xs transition" @click="limparLogsConsole">
                  Limpar Tela
                </button>
              </div>
            </div>

            <div class="bg-dev-card border border-dev-border rounded-xl p-4 mb-5 glow flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                  <span class="flex h-2 w-2 relative">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                  </span>
                  Gerenciamento de Serviços Nginx &amp; ViagensLabs
                </h3>
                <p class="text-xs text-slate-400 mt-1 font-sans">Controle de reinicialização e recarga rápida dos serviços em um único clique.</p>
              </div>
              <div class="flex items-center gap-3">
                <button type="button" :disabled="recarregandoNginx" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-dev-border hover:border-slate-500 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-md" @click="recarregarServicoNginx">
                  <span v-if="recarregandoNginx" class="animate-spin w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full mr-1" />
                  <span v-else>⚙️</span>
                  Recarregar Nginx
                </button>
                <button type="button" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-indigo-600/10 border border-indigo-500/30" @click="reiniciarServicoBackend">
                  🚀 Reiniciar Backend (ViagensLabs)
                </button>
              </div>
            </div>

            <div class="bg-[#030712] border border-dev-border rounded-2xl overflow-hidden shadow-2xl relative">
              <div class="bg-[#0f172a] px-4 py-3 border-b border-dev-border flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <div class="flex items-center gap-2">
                  <span class="w-3.5 h-3.5 rounded-full bg-[#ff5f56]" />
                  <span class="w-3.5 h-3.5 rounded-full bg-[#ffbd2e]" />
                  <span class="w-3.5 h-3.5 rounded-full bg-[#27c93f]" />
                  <span class="ml-2 font-semibold text-slate-400">Terminal Shell // {{ logCaminho || 'system.log' }}</span>
                </div>
                <div class="flex items-center gap-1.5 font-semibold text-[10px]">
                  <span v-if="!logPausado && logCarregando" class="animate-pulse flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                    Syncing...
                  </span>
                  <span v-else-if="logPausado">⏸ PAUSED</span>
                  <span v-else class="text-slate-500">AUTO-REFRESH (3s)</span>
                </div>
              </div>
              <div class="p-5 font-mono text-[11px] leading-relaxed overflow-y-auto h-[55vh] bg-[#020617] select-text selection:bg-indigo-500/30 selection:text-white space-y-1.5 scrollbar-thin" aria-live="polite">
                <template v-if="logsFormatados.length">
                  <div v-for="(line, idx) in logsFormatados" :key="idx" v-html="line" class="border-b border-dev-border/5 pb-1 flex items-start gap-2.5 hover:bg-slate-800/10 px-1 py-0.5 rounded transition" />
                </template>
                <div v-else class="text-slate-500 italic select-none">Initializing debug session... No log streams recorded.</div>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'consultas_sql'">
            <div class="mb-5">
              <h2 class="text-xl font-bold text-white font-sans tracking-tight">Grandes Resultados</h2>
              <p class="text-slate-500 text-xs mt-0.5 font-sans">Principais consultas SQL estruturadas para extração ágil de relatórios analíticos de alto impacto no banco de dados.</p>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div class="space-y-3">
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest px-1">Relatórios Disponíveis</h3>
                <button v-for="q in consultasPredefinidas" :key="q.id" type="button" :class="consultaAtivaId === q.id ? 'bg-indigo-600/15 border-indigo-500/60 shadow-lg text-white' : 'bg-dev-card border-dev-border text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'" class="w-full text-left p-4 border rounded-xl transition cursor-pointer flex flex-col gap-1.5 group select-none" @click="selecionarConsulta(q.id)">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-bold transition group-hover:text-white">{{ q.nome }}</span>
                    <span class="text-xs text-indigo-400/80 font-mono">#{{ q.id }}</span>
                  </div>
                  <p class="text-xs text-slate-500 leading-normal">{{ q.desc }}</p>
                </button>
              </div>

              <div class="lg:col-span-2 space-y-4">
                <div class="bg-dev-card border border-dev-border rounded-xl p-5 space-y-4 glow">
                  <div class="flex justify-between items-center flex-wrap gap-2">
                    <div>
                      <h3 class="text-sm font-bold text-white font-mono">{{ getConsultaAtiva().nome }}</h3>
                      <p class="text-xs text-slate-400 mt-1 leading-normal">{{ getConsultaAtiva().desc }}</p>
                    </div>
                    <button type="button" class="text-xs font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-500/5 hover:bg-indigo-500/10 border border-indigo-500/20 hover:border-indigo-500/40 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5" @click="copiarSql(getConsultaAtiva().sql)">
                      📋 Copiar SQL
                    </button>
                  </div>

                  <div class="bg-[#020617] border border-dev-border rounded-lg overflow-hidden font-mono text-[11px] leading-relaxed">
                    <div class="bg-[#0f172a] px-3 py-1.5 border-b border-dev-border text-[9px] text-slate-500 flex justify-between font-mono select-none">
                      <span>SQL QUERY STRUCTURE</span>
                      <span class="text-indigo-400/70 font-semibold">SQLite / Postgres</span>
                    </div>
                    <pre class="p-4 text-cyan-400 overflow-x-auto whitespace-pre select-text">{{ getConsultaAtiva().sql }}</pre>
                  </div>

                  <div class="flex justify-end pt-2">
                    <button type="button" :disabled="consultaCarregando" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-xs transition disabled:opacity-60 flex items-center gap-2 glow" @click="executarConsulta">
                      <svg v-if="consultaCarregando" class="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      ⚡ Executar Consulta no Banco de Dados
                    </button>
                  </div>
                </div>

                <div class="bg-dev-card border border-dev-border rounded-xl p-5 relative min-h-[200px]">
                  <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Resultado da Extração</h3>

                  <div v-if="consultaCarregando" class="absolute inset-0 bg-dev-card/65 flex items-center justify-center rounded-xl">
                    <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
                  </div>

                  <div v-if="consultaErro" class="p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-xs rounded-lg" role="status" aria-live="polite">{{ consultaErro }}</div>

                  <div v-else-if="!consultaResultados" class="text-center py-16 text-slate-500 text-xs leading-normal select-none">Clique no botão acima para rodar a query estruturada e ver os grandes resultados analíticos.</div>

                  <div v-else-if="consultaResultados.rows.length === 0" class="text-center py-16 text-slate-500 text-xs font-medium">A consulta executou com sucesso, mas retornou 0 registros.</div>

                  <div v-else class="overflow-x-auto border border-dev-border rounded-lg bg-dev-panel">
                    <table class="w-full text-[11px] text-left" aria-label="Tabela de resultados SQL">
                      <thead>
                        <tr class="bg-[#0f172a] border-b border-dev-border text-slate-400 font-bold uppercase tracking-wider text-[9px] select-none">
                          <th v-for="header in consultaResultados.headers" :key="header" class="px-4 py-3 font-mono" scope="col">{{ header }}</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-dev-border/50 text-slate-300 font-mono">
                        <tr v-for="(row, rIdx) in consultaResultados.rows" :key="rIdx" class="hover:bg-slate-800/15 transition">
                          <td v-for="header in consultaResultados.headers" :key="header" class="px-4 py-3.5 text-slate-200">{{ row[header] }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="abaAtiva === 'delegacoes_ad'">
            <div class="mb-5 flex items-center justify-between flex-wrap gap-3">
              <div>
                <h2 class="text-xl font-bold text-white">Delegações AD (Automação Manual)</h2>
                <p class="text-slate-500 text-xs mt-0.5">Cadastre ou remova delegações diretas no banco de dados com auditoria automática.</p>
              </div>
              <button type="button" class="text-xs px-3 py-1.5 bg-dev-card border border-dev-border text-slate-400 hover:text-slate-200 rounded-lg transition" @click="carregarDelegacoes">Recarregar</button>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div class="bg-dev-card border border-dev-border rounded-xl p-5 h-fit glow">
                <h3 class="text-sm font-bold text-white mb-4">Nova Delegação Imediata</h3>
                <div class="space-y-4">
                  <div>
                    <label class="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide" for="deleg-solicitante">Username Terceiro / Solicitante (AD)</label>
                    <input id="deleg-solicitante" v-model="delForm.solicitante" type="text" placeholder="ex: fulana.silva" class="w-full bg-dev-panel border border-dev-border text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600 font-mono">
                    <div v-if="solicitanteBuscando" class="mt-2 text-[10px] text-indigo-400 font-mono animate-pulse">Buscando no BigQuery...</div>
                    <div v-else-if="solicitanteInfo" class="mt-2 p-2 bg-indigo-950/20 border border-indigo-500/20 rounded-lg text-[10px] text-slate-400 space-y-1">
                      <p class="font-bold text-slate-200">{{ solicitanteInfo.nome }}</p>
                      <p>{{ solicitanteInfo.cargo }}</p>
                      <p class="font-mono text-indigo-300">{{ solicitanteInfo.email }}</p>
                    </div>
                  </div>

                  <div>
                    <label class="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide" for="deleg-viajante">Username Viajante / Titular (AD)</label>
                    <input id="deleg-viajante" v-model="delForm.viajante" type="text" placeholder="ex: diretor.andre" class="w-full bg-dev-panel border border-dev-border text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 placeholder-slate-600 font-mono">
                    <div v-if="viajanteBuscando" class="mt-2 text-[10px] text-indigo-400 font-mono animate-pulse">Buscando no BigQuery...</div>
                    <div v-else-if="viajanteInfo" class="mt-2 p-2 bg-indigo-950/20 border border-indigo-500/20 rounded-lg text-[10px] text-slate-400 space-y-1">
                      <p class="font-bold text-slate-200">{{ viajanteInfo.nome }}</p>
                      <p>{{ viajanteInfo.cargo }}</p>
                      <p class="font-mono text-indigo-300">{{ viajanteInfo.email }}</p>
                    </div>
                  </div>

                  <div v-if="delFormErro" class="text-xs text-red-400">{{ delFormErro }}</div>
                  <div v-if="delFormOk" class="text-xs text-green-400">{{ delFormOk }}</div>

                  <button type="button" :disabled="delFormLoading || solicitanteBuscando || viajanteBuscando" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 rounded-lg text-xs transition disabled:opacity-60" @click="salvarDelegacao">
                    {{ delFormLoading ? 'Cadastrando…' : 'Cadastrar Delegação' }}
                  </button>
                </div>
              </div>

              <div class="lg:col-span-2 bg-dev-card border border-dev-border rounded-xl p-5">
                <h3 class="text-sm font-bold text-white mb-4">Delegações Ativas no Banco</h3>

                <div v-if="delegacoesCarregando" class="flex justify-center py-10">
                  <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
                </div>

                <div v-else-if="!delegacoes.length" class="text-center py-16 text-slate-500 text-xs font-mono select-none">Nenhuma delegação manual cadastrada no momento.</div>

                <div v-else class="overflow-x-auto border border-dev-border rounded-lg bg-dev-panel">
                  <table class="w-full text-[11px] text-left" aria-label="Tabela de delegações AD">
                    <thead>
                      <tr class="bg-[#0f172a] border-b border-dev-border text-slate-400 font-bold uppercase tracking-wider text-[9px] select-none">
                        <th class="px-4 py-3" scope="col">Terceiro (Secretária)</th>
                        <th class="px-4 py-3" scope="col">Viajante (Titular)</th>
                        <th class="px-4 py-3" scope="col">Status</th>
                        <th class="px-4 py-3" scope="col">Operador Dev</th>
                        <th class="px-4 py-3 text-right" scope="col">Ações</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-dev-border/50 text-slate-300 font-mono">
                      <tr v-for="d in delegacoes" :key="d.id" class="hover:bg-slate-800/15 transition">
                        <td class="px-4 py-3 font-bold text-indigo-300">{{ d.solicitante }}</td>
                        <td class="px-4 py-3 text-slate-200">
                          <p class="font-bold">{{ d.terceiro_nome }}</p>
                          <p class="text-[10px] text-slate-500">{{ d.terceiro_username }} ({{ d.terceiro_email }})</p>
                        </td>
                        <td class="px-4 py-3"><span class="bg-green-500/10 text-green-400 border border-green-500/30 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">APROVADA</span></td>
                        <td class="px-4 py-3 text-slate-400">{{ d.operador }}</td>
                        <td class="px-4 py-3 text-right">
                          <button type="button" class="text-red-400 hover:text-red-300 hover:bg-red-500/10 px-2 py-1 rounded-lg border border-transparent hover:border-red-500/30 transition shrink-0 inline-flex items-center gap-1" @click="removerDelegacao(d)">
                            🗑 Remover
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>

    <div v-if="excluirModal.aberto" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div class="bg-dev-card border border-dev-border rounded-2xl p-6 w-full max-w-sm glow" role="dialog" aria-modal="true" aria-label="Confirmação de exclusão">
        <div class="flex items-center gap-2.5 text-red-400 mb-3">
          <span class="text-2xl">⚠</span>
          <h3 class="text-sm font-bold text-white">Excluir Solicitação</h3>
        </div>
        <p class="text-xs text-slate-400 mb-4 leading-relaxed">
          Tem certeza que deseja excluir a solicitação <strong class="font-mono text-indigo-300">{{ excluirModal.solicitacao?.protocolo }}</strong> de forma definitiva?
          <span class="block mt-2 text-red-400 font-semibold">Esta ação removerá logs, cotações, tokens, vouchers e casamentos em cascata.</span>
        </p>
        <div v-if="excluirModal.erro" class="text-xs text-red-400 mb-3" role="status" aria-live="polite">{{ excluirModal.erro }}</div>
        <div class="flex gap-2">
          <button type="button" :disabled="excluirModal.carregando" class="flex-1 py-2 text-xs font-semibold bg-red-600 hover:bg-red-500 text-white rounded-lg transition disabled:opacity-60" @click="confirmarExclusaoCascade">
            {{ excluirModal.carregando ? 'Excluindo…' : 'Excluir Definitivamente' }}
          </button>
          <button type="button" class="flex-1 py-2 text-xs font-semibold border border-dev-border text-slate-400 rounded-lg hover:border-slate-500 transition" @click="excluirModal.aberto = false">
            Cancelar
          </button>
        </div>
      </div>
    </div>

    <div v-if="reiniciandoBackend" class="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center z-50 p-4">
      <div class="bg-dev-card border border-dev-border rounded-2xl p-8 w-full max-w-md text-center glow space-y-6" role="status" aria-live="polite">
        <div class="relative flex justify-center">
          <div class="animate-spin rounded-full h-20 w-20 border-4 border-indigo-500/20 border-t-indigo-500" />
          <div class="absolute inset-0 flex items-center justify-center">
            <span class="text-2xl font-bold font-mono text-indigo-400 animate-pulse">{{ contadorRegressivo }}</span>
          </div>
        </div>
        <div>
          <h3 class="text-lg font-bold text-white tracking-tight">Reiniciando Serviços</h3>
          <p class="text-xs text-slate-400 mt-2 leading-relaxed">
            O serviço do backend do <strong class="text-indigo-300 font-semibold font-mono">ViagensLabs</strong> está sendo reiniciado graciosamente. O WinSW irá reconectar a aplicação em alguns instantes.
          </p>
        </div>
        <div class="bg-indigo-950/20 border border-indigo-500/10 rounded-xl p-3 text-[10px] text-indigo-300 font-mono">
          Aguarde, redirecionando em {{ contadorRegressivo }} segundos...
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dev-page {
  background: #0a0f1e;
}

.dev-page :deep(::-webkit-scrollbar) {
  width: 5px;
  height: 5px;
}

.dev-page :deep(::-webkit-scrollbar-track) {
  background: #0f172a;
}

.dev-page :deep(::-webkit-scrollbar-thumb) {
  background: #334155;
  border-radius: 3px;
}

.bg-dev-bg {
  background-color: #0a0f1e;
}

.bg-dev-panel {
  background-color: #0f172a;
}

.bg-dev-card {
  background-color: #1e293b;
}

.border-dev-border {
  border-color: #334155;
}

.text-dev-cyan {
  color: #06b6d4;
}

.text-dev-yellow {
  color: #f59e0b;
}

.text-dev-green {
  color: #22c55e;
}

.glow {
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.badge-status {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: .03em;
}
</style>
