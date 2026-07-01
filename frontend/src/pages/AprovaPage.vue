<script setup>
import { onMounted, ref } from 'vue'
import { createApiClient } from '@/services/api-client.js'

const estado = ref('carregando')
const detalhes = ref(null)
const observacao = ref('')
const processando = ref(false)
const acaoAtual = ref('')
const erroMsg = ref('')
const erroAcao = ref('')
const resultado = ref(null)

const tokenUuid = new URLSearchParams(window.location.search).get('token')
const apiClient = createApiClient({
  baseUrl: '/api/v1',
  getToken: () => '',
})

function formatarDataExpiracao(dataExpiracao) {
  if (!dataExpiracao) return '—'
  return new Date(dataExpiracao).toLocaleString('pt-BR')
}

async function carregarDetalhes() {
  if (!tokenUuid) {
    erroMsg.value = 'Token não informado na URL.'
    estado.value = 'erro'
    return
  }

  try {
    const res = await apiClient.request(`/aprovacao/${tokenUuid}`, { auth: false })
    if (!res.ok) {
      erroMsg.value = res.data?.detail || 'Token inválido.'
      estado.value = 'erro'
      return
    }

    detalhes.value = res.data
    if (detalhes.value?.expirado) {
      estado.value = 'expirado'
      return
    }
    if (detalhes.value?.status_token !== 'PENDENTE') {
      estado.value = 'ja_respondido'
      return
    }
    estado.value = 'aguardando'
  } catch {
    erroMsg.value = 'Erro de conexão. Tente novamente.'
    estado.value = 'erro'
  }
}

async function processar(acao) {
  erroAcao.value = ''
  processando.value = true
  acaoAtual.value = acao
  try {
    const res = await apiClient.request(`/aprovacao/${tokenUuid}`, {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ acao, observacao: observacao.value }),
    })

    if (!res.ok) {
      erroAcao.value = res.data?.detail || 'Erro ao processar.'
      return
    }

    resultado.value = res.data || {}
    estado.value = 'concluido'
  } catch {
    erroAcao.value = 'Erro de conexão. Tente novamente.'
  } finally {
    processando.value = false
    acaoAtual.value = ''
  }
}

onMounted(async () => {
  await carregarDetalhes()
})
</script>

<template>
  <main class="bg-aprovacao min-h-screen flex items-center justify-center p-4 vl-font-inter">
    <div class="w-full">
      <div v-if="estado === 'carregando'" class="text-center text-slate-200 space-y-3">
        <div class="w-10 h-10 border-4 border-blue-300 border-t-transparent rounded-full animate-spin mx-auto" />
        <p>Carregando solicitação…</p>
      </div>

      <div v-else-if="estado === 'erro'" class="vl-approval-state-card fade-in">
        <div class="text-5xl mb-4" aria-hidden="true">⚠️</div>
        <h2 class="text-xl font-bold text-red-600 mb-2">{{ erroMsg }}</h2>
        <p class="text-slate-500 text-sm">Se precisar de ajuda, entre em contato com o setor de viagens.</p>
      </div>

      <div v-else-if="estado === 'ja_respondido'" class="vl-approval-state-card fade-in">
        <div class="text-5xl mb-4" aria-hidden="true">{{ detalhes?.status_token === 'APROVADO' ? '✅' : '❌' }}</div>
        <h2 class="text-xl font-bold mb-2">
          {{ detalhes?.status_token === 'APROVADO' ? 'Solicitação já aprovada' : 'Solicitação já reprovada' }}
        </h2>
        <p class="text-slate-500 text-sm">Protocolo: <strong>{{ detalhes?.solicitacao?.protocolo }}</strong></p>
        <p class="text-slate-400 text-xs mt-2">Este link já foi utilizado e não pode ser reaproveitado.</p>
      </div>

      <div v-else-if="estado === 'expirado'" class="vl-approval-state-card fade-in">
        <div class="text-5xl mb-4" aria-hidden="true">⏱️</div>
        <h2 class="text-xl font-bold text-orange-600 mb-2">Link Expirado</h2>
        <p class="text-slate-500 text-sm">
          O prazo de aprovação para <strong>{{ detalhes?.solicitacao?.protocolo }}</strong> foi encerrado.
        </p>
        <p class="text-slate-400 text-xs mt-2">Entre em contato com o setor de viagens para uma nova avaliação.</p>
      </div>

      <div v-else-if="estado === 'aguardando'" class="max-w-lg w-full mx-auto space-y-4 fade-in">
        <header class="bg-blue-800 text-white rounded-2xl px-6 py-5 shadow-lg">
          <p class="text-xs uppercase tracking-widest opacity-75 mb-1">Viagens Corporativas · Magalu</p>
          <h1 class="text-xl font-bold">
            {{ detalhes?.nivel === 'N1' ? '👤 Aprovação N1 — Gestor Direto' : '🏢 Aprovação N2 — Diretoria' }}
          </h1>
          <p class="text-sm mt-1 opacity-90">Olá, <strong>{{ detalhes?.nome_aprovador || detalhes?.email_aprovador }}</strong></p>
        </header>

        <section class="vl-approval-panel space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="font-bold text-slate-700">Solicitação de Viagem</h2>
            <span
              class="text-xs font-bold px-3 py-1 rounded-full"
              :class="detalhes?.solicitacao?.classificacao === 'Emergencial'
                ? 'bg-red-100 text-red-700 border border-red-300'
                : 'bg-green-100 text-green-700 border border-green-300'"
            >
              {{ detalhes?.solicitacao?.classificacao === 'Emergencial' ? '⚠️ EMERGENCIAL' : '✔ COMUM' }}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div><p class="text-xs text-slate-400 uppercase tracking-wide">Protocolo</p><p class="font-bold text-blue-700">{{ detalhes?.solicitacao?.protocolo }}</p></div>
            <div><p class="text-xs text-slate-400 uppercase tracking-wide">Solicitante</p><p class="font-semibold">{{ detalhes?.solicitacao?.solicitante_username }}</p></div>
            <div><p class="text-xs text-slate-400 uppercase tracking-wide">Destino</p><p class="font-semibold">{{ detalhes?.solicitacao?.destino_cidade }} / {{ detalhes?.solicitacao?.destino_estado }}</p></div>
            <div><p class="text-xs text-slate-400 uppercase tracking-wide">Antecedência</p><p class="font-semibold">{{ detalhes?.solicitacao?.antecedencia_dias }} dias</p></div>
            <div><p class="text-xs text-slate-400 uppercase tracking-wide">Ida</p><p class="font-semibold">{{ detalhes?.solicitacao?.data_ida }}</p></div>
            <div><p class="text-xs text-slate-400 uppercase tracking-wide">Retorno</p><p class="font-semibold">{{ detalhes?.solicitacao?.data_volta || '—' }}</p></div>
            <div class="col-span-2"><p class="text-xs text-slate-400 uppercase tracking-wide">Serviços Solicitados</p><p class="font-semibold">{{ detalhes?.solicitacao?.tipo_servico?.join(' · ') }}</p></div>
            <div class="col-span-2"><p class="text-xs text-slate-400 uppercase tracking-wide">Motivo</p><p class="text-slate-700">{{ detalhes?.solicitacao?.motivo_viagem }}</p></div>
            <div v-if="detalhes?.solicitacao?.observacoes_viajante" class="col-span-2"><p class="text-xs text-slate-400 uppercase tracking-wide">Observações do Viajante</p><p class="text-slate-600 italic">{{ detalhes?.solicitacao?.observacoes_viajante }}</p></div>
          </div>

          <p class="vl-amber-alert-surface px-3 py-2 text-xs text-amber-700">
            ⏳ Link válido até <strong>{{ formatarDataExpiracao(detalhes?.data_expiracao) }}</strong>
          </p>
        </section>

        <section class="vl-approval-panel">
          <label class="block text-sm font-semibold text-slate-700 mb-1" for="obs-aprovacao">
            Observação <span class="text-slate-400 font-normal">(opcional)</span>
          </label>
          <textarea
            id="obs-aprovacao"
            v-model="observacao"
            rows="3"
            class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Ex.: Solicitar comprovante de reunião antes de aprovar…"
          />
        </section>

        <div class="grid grid-cols-2 gap-3">
          <button
            class="vl-approval-action-btn bg-red-600 hover:bg-red-700"
            :disabled="processando"
            @click="processar('reprovar')"
          >
            <span
              v-if="processando && acaoAtual === 'reprovar'"
              class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
            />
            ❌ Reprovar
          </button>
          <button
            class="vl-approval-action-btn bg-green-600 hover:bg-green-700"
            :disabled="processando"
            @click="processar('aprovar')"
          >
            <span
              v-if="processando && acaoAtual === 'aprovar'"
              class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
            />
            ✅ Aprovar
          </button>
        </div>

        <p v-if="erroAcao" class="text-center text-red-600 text-sm bg-red-50 rounded-lg p-2">{{ erroAcao }}</p>
      </div>

      <div v-else-if="estado === 'concluido'" class="vl-approval-state-card fade-in">
        <div class="text-6xl mb-4" aria-hidden="true">{{ resultado?.acao === 'aprovar' ? '✅' : '❌' }}</div>
        <h2 class="text-2xl font-bold mb-1">{{ resultado?.acao === 'aprovar' ? 'Aprovado!' : 'Reprovado' }}</h2>
        <p class="text-slate-500 mb-1">Protocolo: <strong class="text-blue-700">{{ resultado?.protocolo }}</strong></p>
        <p class="text-slate-400 text-sm">Novo status: <strong>{{ resultado?.status }}</strong></p>
        <div
          v-if="resultado?.acao === 'aprovar' && resultado?.status === 'AGUARDANDO_N2'"
          class="mt-4 vl-amber-alert-surface p-3 text-sm text-amber-700"
        >
          ⏳ E-mail de <strong>Aprovação N2</strong> enviado ao diretor responsável.
        </div>
        <div v-else-if="resultado?.acao === 'aprovar'" class="mt-4 vl-green-success-surface p-3 text-sm text-green-700">
          🎯 O setor de viagens foi notificado e iniciará a cotação.
        </div>
        <p class="text-slate-300 text-xs mt-6">Você pode fechar esta janela.</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.bg-aprovacao {
  background-image:
    linear-gradient(rgba(15, 23, 42, 0.80), rgba(15, 23, 42, 0.90)),
    var(--vl-bg-aviao);
}
</style>
