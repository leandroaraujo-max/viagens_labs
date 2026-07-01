<template>
  <div class="min-h-screen flex flex-col font-sans antialiased text-gray-800 selection:bg-blue-600 selection:text-white">
    <transition name="fade">
      <section
        v-if="!isAuthenticated"
        class="bg-viagens min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      >
        <div class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
        <div class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />

        <div class="vl-shell-dark-card transition-all duration-300" role="region" aria-label="Login do portal de viagens">
          <div class="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />

          <header class="text-center mb-8 mt-2 flex flex-col items-center select-none">
            <img :src="logoUrl" alt="Luizalabs" class="h-10 object-contain mb-3" />
            <span class="text-[11px] font-mono text-blue-400 block tracking-widest leading-none uppercase font-bold mt-1">Viagens</span>
          </header>

          <div
            v-if="erroLogin && !semAcessoAd"
            class="mb-5 p-4 bg-red-950/40 border-l-4 border-red-500 text-red-200 text-xs rounded-xl shadow-sm border border-red-900/30"
            role="alert"
            aria-live="polite"
          >
            {{ erroLogin }}
          </div>

          <div
            v-if="semAcessoAd"
            class="mb-5 p-4 bg-amber-950/40 border-l-4 border-amber-500 text-amber-200 text-xs rounded-xl shadow-sm border border-amber-900/30"
            role="alert"
            aria-live="polite"
          >
            <p class="font-semibold mb-1">Acesso negado ao portal.</p>
            <p>
              Solicite liberação no TURIA para o grupo
              <strong>G_ACCESS_VIAGENSLABS_USERS</strong>.
            </p>
          </div>

          <form class="space-y-5" @submit.prevent="realizarLogin">
            <div>
              <label class="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2" for="username">Usuário de Rede (AD)</label>
              <input
                id="username"
                v-model.trim="loginForm.username"
                type="text"
                autocomplete="username"
                required
                class="w-full px-4 py-3 rounded-xl border border-slate-800 bg-slate-950 text-white placeholder-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-900/30 transition-all duration-200 text-sm shadow-sm"
                placeholder="ex: nome.sobrenome"
              />
            </div>

            <div>
              <label class="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2" for="password">Senha Corporativa</label>
              <input
                id="password"
                v-model="loginForm.password"
                type="password"
                autocomplete="current-password"
                required
                class="w-full px-4 py-3 rounded-xl border border-slate-800 bg-slate-950 text-white placeholder-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-900/30 transition-all duration-200 text-sm shadow-sm"
                placeholder="Mesma senha do e-mail"
              />
            </div>

            <button
              type="submit"
              :disabled="carregando"
              class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg hover:shadow-blue-500/20 transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-75 disabled:cursor-not-allowed disabled:transform-none mt-2"
            >
              <span v-if="carregando">Autenticando...</span>
              <span v-else>Entrar</span>
            </button>
          </form>
        </div>
      </section>
    </transition>

    <transition name="fade">
      <div v-if="isAuthenticated" class="min-h-screen flex bg-[#f8fafc] text-slate-800 w-full relative">
        <aside
          :class="menuRecolhido ? 'w-20' : 'w-64'"
          class="bg-[#0a0f1e] text-slate-300 flex flex-col shrink-0 border-r border-slate-800/40 min-h-screen transition-all duration-300 z-30 relative shadow-2xl"
        >
          <div class="p-5 flex flex-col items-center border-b border-slate-800/40 gap-2 select-none">
            <img :src="logoUrl" alt="Luizalabs" :class="menuRecolhido ? 'h-6' : 'h-8'" class="object-contain shrink-0" />
            <span v-if="!menuRecolhido" class="text-[10px] font-mono text-blue-400 block tracking-widest leading-none uppercase font-bold mt-1">Viagens</span>
          </div>

          <nav class="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto" aria-label="Abas do portal">
            <button
              type="button"
              @click="abaAtiva = 'nova_solicitacao'"
              :class="abaAtiva === 'nova_solicitacao' ? abaAtivaClass : abaInativaClass"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-all duration-200 text-left"
            >
              <span class="text-base">➕</span>
              <span v-if="!menuRecolhido" class="truncate flex-1">Nova Solicitação</span>
            </button>

            <button
              type="button"
              @click="irParaHistorico"
              :class="abaAtiva === 'minhas_viagens' ? abaAtivaClass : abaInativaClass"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-all duration-200 text-left"
            >
              <span class="text-base">✈️</span>
              <span v-if="!menuRecolhido" class="truncate flex-1">Minhas Viagens</span>
            </button>

            <button
              type="button"
              @click="irParaCreditos"
              :class="abaAtiva === 'gestao_creditos' ? abaAtivaClass : abaInativaClass"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-all duration-200 text-left"
            >
              <span class="text-base">💳</span>
              <span v-if="!menuRecolhido" class="truncate flex-1">Gestão de Créditos</span>
            </button>
          </nav>

          <div class="p-4 border-t border-slate-800/40 flex flex-col gap-3 shrink-0">
            <button
              type="button"
              @click="menuRecolhido = !menuRecolhido"
              class="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800/20 border border-slate-800/40 hover:bg-slate-800/30 text-slate-400 hover:text-slate-200 rounded-lg text-[10px] font-mono transition"
            >
              <span>{{ menuRecolhido ? '▶' : '◀ Recolher' }}</span>
            </button>
          </div>
        </aside>

        <div class="flex-grow flex flex-col min-w-0 min-h-screen">
          <header class="bg-white border-b border-gray-200/80 px-6 py-3 flex items-center justify-between sticky top-0 z-20 shadow-xs">
            <div class="flex items-center gap-3 min-w-0">
              <h1 class="text-sm font-bold text-gray-800 tracking-tight">{{ tituloAba }}</h1>
              <p class="text-xs text-gray-400 truncate hidden sm:block">{{ subtituloAba }}</p>
            </div>

            <div class="flex items-center gap-3 shrink-0">
              <div class="hidden sm:flex flex-col items-end">
                <span class="text-xs font-semibold text-gray-700 leading-tight">{{ nomeUsuario }}</span>
                <span class="text-[9px] font-medium bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-md mt-0.5">{{ badgePerfil }}</span>
              </div>
              <div class="h-8 w-8 rounded-lg bg-[#0a0f1e] text-white flex items-center justify-center font-extrabold text-xs shadow-sm shrink-0">
                {{ inicialUsuario }}
              </div>
              <button type="button" class="vl-btn-logout" @click="logout">Sair</button>
            </div>
          </header>

          <main class="w-full p-6 flex-grow space-y-6">
            <section v-show="abaAtiva === 'nova_solicitacao'" class="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <article class="xl:col-span-2 bg-white rounded-2xl border border-gray-200 p-6 space-y-5">
                <header class="flex items-center justify-between gap-2">
                  <h2 class="text-lg font-bold text-slate-900">Nova Solicitação</h2>
                  <span v-if="protocoloGerado" class="text-[11px] px-2 py-1 rounded bg-green-50 text-green-700 border border-green-200">Protocolo {{ protocoloGerado }}</span>
                </header>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-2" role="radiogroup" aria-label="Tipo de solicitação">
                  <label class="flex items-center gap-2 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
                    <input v-model="tipoSolicitacao" type="radio" name="tipo_solicitacao" value="proprio" class="h-4 w-4" />
                    <span class="text-sm">Para mim</span>
                  </label>
                  <label class="flex items-center gap-2 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
                    <input v-model="tipoSolicitacao" type="radio" name="tipo_solicitacao" value="conjunto" class="h-4 w-4" />
                    <span class="text-sm">Em conjunto</span>
                  </label>
                  <label class="flex items-center gap-2 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
                    <input v-model="tipoSolicitacao" type="radio" name="tipo_solicitacao" value="delegado" class="h-4 w-4" />
                    <span class="text-sm">Para outro</span>
                  </label>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                  <div class="md:col-span-2">
                    <label for="cpfBusca" class="block text-xs font-semibold text-gray-700 mb-1">CPF ou matrícula do viajante</label>
                    <input
                      id="cpfBusca"
                      v-model.trim="cpfBusca"
                      type="text"
                      class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:border-blue-600"
                      placeholder="Digite CPF ou matrícula"
                    />
                  </div>
                  <button
                    type="button"
                    @click="buscarColaboradorGCP"
                    :disabled="buscandoColaborador"
                    class="h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg disabled:opacity-50"
                  >
                    {{ buscandoColaborador ? 'Buscando...' : 'Buscar' }}
                  </button>
                </div>

                <p v-if="erroBusca" class="text-xs text-red-600" role="alert">{{ erroBusca }}</p>
                <p v-if="erroBuscaProprioUsuario" class="text-xs text-amber-700">{{ erroBuscaProprioUsuario }}</p>

                <div v-if="viajanteDados" class="rounded-xl border border-blue-100 bg-blue-50/50 p-4 space-y-3">
                  <h3 class="text-sm font-bold text-blue-900">Viajante identificado</h3>
                  <dl class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    <div><dt class="text-gray-500">Nome</dt><dd class="font-semibold text-gray-800">{{ viajanteDados.nome || '—' }}</dd></div>
                    <div><dt class="text-gray-500">CPF</dt><dd class="font-semibold text-gray-800">{{ formatCPF(viajanteDados.cpf) }}</dd></div>
                    <div><dt class="text-gray-500">Matrícula</dt><dd class="font-semibold text-gray-800">{{ viajanteDados.matricula || '—' }}</dd></div>
                    <div><dt class="text-gray-500">Cargo</dt><dd class="font-semibold text-gray-800">{{ viajanteDados.cargo || '—' }}</dd></div>
                  </dl>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label for="celularViajante" class="block text-xs font-semibold text-gray-700 mb-1">Celular</label>
                      <input
                        id="celularViajante"
                        v-model="celularViajante"
                        type="text"
                        class="w-full px-3 py-2 rounded-lg border border-gray-300"
                        placeholder="(11) 99999-9999"
                        @input="mascaraCelular"
                      />
                    </div>
                    <div>
                      <label for="nascimentoViajante" class="block text-xs font-semibold text-gray-700 mb-1">Data de nascimento</label>
                      <input
                        id="nascimentoViajante"
                        v-model="dataNascimentoViajante"
                        type="text"
                        class="w-full px-3 py-2 rounded-lg border border-gray-300"
                        placeholder="dd/mm/aaaa"
                        @input="mascaraData"
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    @click="salvarPerfilViajante"
                    class="px-3 py-2 text-xs rounded-lg border border-blue-200 bg-white hover:bg-blue-50"
                  >
                    {{ perfilSalvo ? 'Perfil salvo ✓' : 'Salvar perfil' }}
                  </button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label for="origemCidade" class="block text-xs font-semibold text-gray-700 mb-1">Origem</label>
                    <input id="origemCidade" v-model.trim="formViagem.origem_cidade" type="text" class="w-full px-3 py-2 rounded-lg border border-gray-300" />
                  </div>
                  <div>
                    <label for="destinoCidade" class="block text-xs font-semibold text-gray-700 mb-1">Destino *</label>
                    <input id="destinoCidade" v-model.trim="formViagem.destino_cidade" type="text" required class="w-full px-3 py-2 rounded-lg border border-gray-300" />
                  </div>
                  <div>
                    <label for="dataIda" class="block text-xs font-semibold text-gray-700 mb-1">Data ida *</label>
                    <input id="dataIda" v-model="formViagem.data_ida" type="text" placeholder="dd/mm/aaaa" class="w-full px-3 py-2 rounded-lg border border-gray-300" @input="mascaraDataIda" />
                  </div>
                  <div>
                    <label for="dataVolta" class="block text-xs font-semibold text-gray-700 mb-1">Data volta</label>
                    <input id="dataVolta" v-model="formViagem.data_volta" type="text" placeholder="dd/mm/aaaa" class="w-full px-3 py-2 rounded-lg border border-gray-300" @input="mascaraDataVolta" />
                  </div>
                </div>

                <div>
                  <p class="block text-xs font-semibold text-gray-700 mb-2">Serviços *</p>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <label v-for="servico in servicosDisponiveis" :key="servico.valor" class="flex items-center gap-2 p-2 rounded-lg border border-gray-200 text-xs cursor-pointer hover:bg-gray-50">
                      <input v-model="formViagem.tipo_servico" :value="servico.valor" type="checkbox" class="h-4 w-4" />
                      <span>{{ servico.label }}</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label for="motivoViagem" class="block text-xs font-semibold text-gray-700 mb-1">Motivo da viagem *</label>
                  <textarea id="motivoViagem" v-model.trim="formViagem.motivo_viagem" rows="3" class="w-full px-3 py-2 rounded-lg border border-gray-300" />
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label for="periodoAereo" class="block text-xs font-semibold text-gray-700 mb-1">Período preferido (aéreo)</label>
                    <select id="periodoAereo" v-model="formPreferencias.aereo_periodo_preferido" class="w-full px-3 py-2 rounded-lg border border-gray-300">
                      <option value="">Selecione</option>
                      <option v-for="periodo in periodosVoo" :key="periodo.id" :value="periodo.id">{{ periodo.nome }}</option>
                    </select>
                  </div>
                  <div class="flex items-center gap-2 pt-6">
                    <input id="bagagemExtra" v-model="formPreferencias.bagagem_extra" type="checkbox" class="h-4 w-4" />
                    <label for="bagagemExtra" class="text-xs text-gray-700">Necessita bagagem extra</label>
                  </div>
                </div>

                <div>
                  <label for="observacoesViajante" class="block text-xs font-semibold text-gray-700 mb-1">Observações</label>
                  <textarea id="observacoesViajante" v-model.trim="formPreferencias.observacoes_viajante" rows="3" class="w-full px-3 py-2 rounded-lg border border-gray-300" />
                </div>

                <p v-if="erroEnvio" class="text-xs text-red-600" role="alert">{{ erroEnvio }}</p>
                <p v-if="classificacaoGerada" class="text-xs text-blue-700">Classificação: <strong>{{ classificacaoGerada }}</strong></p>

                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    @click="enviarSolicitacao"
                    :disabled="enviandoSolicitacao || !passo2Valido || !viajanteDados"
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold disabled:opacity-50"
                  >
                    {{ enviandoSolicitacao ? 'Enviando...' : 'Enviar solicitação' }}
                  </button>
                  <button type="button" @click="novaSolicitacao" class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-semibold hover:bg-gray-50">
                    Limpar formulário
                  </button>
                </div>
              </article>

              <aside class="bg-white rounded-2xl border border-gray-200 p-4 space-y-3">
                <h2 class="text-sm font-bold text-slate-800">Resumo rápido</h2>
                <p class="text-xs text-gray-600">Status do envio e dados essenciais da solicitação.</p>
                <dl class="space-y-2 text-xs">
                  <div class="flex justify-between gap-2"><dt>Viajante</dt><dd class="font-semibold text-right">{{ viajanteDados?.nome || 'Não identificado' }}</dd></div>
                  <div class="flex justify-between gap-2"><dt>Destino</dt><dd class="font-semibold text-right">{{ formViagem.destino_cidade || '—' }}</dd></div>
                  <div class="flex justify-between gap-2"><dt>Data ida</dt><dd class="font-semibold text-right">{{ formViagem.data_ida || '—' }}</dd></div>
                  <div class="flex justify-between gap-2"><dt>Serviços</dt><dd class="font-semibold text-right">{{ formViagem.tipo_servico.join(', ') || '—' }}</dd></div>
                </dl>
              </aside>
            </section>

            <section v-show="abaAtiva === 'minhas_viagens'" class="bg-white rounded-2xl border border-gray-200 p-5 space-y-4">
              <header class="flex items-center justify-between gap-2">
                <h2 class="text-base font-bold text-slate-800">Minhas viagens</h2>
                <button type="button" @click="carregarHistorico" :disabled="historicoCarregando" class="px-3 py-2 border border-gray-300 rounded-lg text-xs font-semibold hover:bg-gray-50 disabled:opacity-50">
                  {{ historicoCarregando ? 'Atualizando...' : 'Atualizar' }}
                </button>
              </header>

              <p v-if="historicoCarregando" class="text-xs text-gray-500" role="status">Carregando histórico...</p>
              <p v-else-if="historico.length === 0" class="text-xs text-gray-500">Nenhuma solicitação encontrada.</p>

              <div v-else class="space-y-3">
                <article v-for="item in historico" :key="item.id" class="border border-gray-200 rounded-xl p-4 space-y-3">
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 class="text-sm font-bold text-slate-800">{{ item.destino_cidade || 'Destino não informado' }}</h3>
                      <p class="text-xs text-gray-500">Protocolo: {{ item.protocolo || '—' }} · Ida: {{ formatarData(item.data_ida) }}</p>
                    </div>
                    <span :class="statusCorMini(item.status)" class="text-[10px] px-2 py-1 rounded border font-semibold">{{ statusLabelMini(item.status) }}</span>
                  </div>

                  <p class="text-xs text-gray-700">{{ item.motivo_viagem || 'Sem observações.' }}</p>

                  <div class="flex flex-wrap gap-2">
                    <button type="button" class="px-3 py-1.5 rounded border border-amber-300 text-amber-700 text-xs font-semibold hover:bg-amber-50" @click="abrirCancelar(item)">
                      Solicitar cancelamento
                    </button>
                    <button type="button" class="px-3 py-1.5 rounded border border-blue-300 text-blue-700 text-xs font-semibold hover:bg-blue-50" @click="abrirRemarcacao(item)">
                      Solicitar remarcação
                    </button>
                  </div>

                </article>
              </div>
            </section>

            <section v-show="abaAtiva === 'gestao_creditos'" class="bg-white rounded-2xl border border-gray-200 p-5 space-y-4">
              <header class="flex items-center justify-between gap-2">
                <h2 class="text-base font-bold text-slate-800">Gestão de créditos</h2>
                <button type="button" @click="carregarMeusCreditos" class="px-3 py-2 border border-gray-300 rounded-lg text-xs font-semibold hover:bg-gray-50">
                  Atualizar
                </button>
              </header>

              <p v-if="meusCreditos.length === 0" class="text-xs text-gray-500">Nenhum crédito disponível.</p>
              <ul v-else class="space-y-2">
                <li v-for="(credito, idx) in meusCreditos" :key="credito.id || idx" class="p-3 rounded-lg border border-gray-200 text-xs">
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <span class="font-semibold text-gray-800">{{ credito.origem || 'Crédito de viagem' }}</span>
                    <span class="text-green-700 font-bold">{{ credito.valor || credito.saldo || '—' }}</span>
                  </div>
                  <p class="text-gray-500 mt-1">Validade: {{ formatarData(credito.validade) }}</p>
                </li>
              </ul>
            </section>
          </main>
        </div>
      </div>
    </transition>

    <LgpdConsentModal
      :is-open="mostrandoModalLGPD"
      :loading="registrandoConsentimento"
      :error-message="erroConsentimento"
      @accept="aceitarConsentimentoLGPD"
      @reject="logout"
    />

    <CancelTravelModal
      :is-open="cancelamentoAbertoId !== null"
      :loading="enviandoCancelar"
      :trip="viagemACancelar"
      @close="fecharCancelamento"
      @submit="confirmarCancelarViagem"
    />

    <RescheduleTravelModal
      :is-open="remarcacaoAbertaId !== null"
      :loading="enviandoRemarcar"
      :trip="viagemARemarcar"
      @close="fecharRemarcacao"
      @submit="confirmarRemarcarViagem"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LgpdConsentModal from '../composables/Modal/LgpdConsentModal.vue'
import CancelTravelModal from '../composables/Modal/CancelTravelModal.vue'
import RescheduleTravelModal from '../composables/Modal/RescheduleTravelModal.vue'

import { createApiClient } from '../services/api-client.js'
import { createIndexApi } from '../services/index-api.js'
import { createError, parseErrorMessage } from '../services/http-errors.js'
import { useAuthStore } from '../stores/auth.js'
import { formatCPF } from '../utils/formatters.js'
import { maskDateBR, maskPhoneBR, parseDateBR, toISODateTime } from '../utils/validators.js'

const logoUrl = new URL('../../img/luizalabs-logo.png', import.meta.url).href

const router = useRouter()
const authStore = useAuthStore()

const LGPD_ACCEPT_KEY = 'lgpd_aceito'
const LGPD_ACCEPT_DATE_KEY = 'lgpd_data_aceito'

const carregando = ref(false)
const erroLogin = ref('')
const semAcessoAd = ref(false)
const loginForm = reactive({ username: '', password: '' })

const nomeUsuario = computed(() => authStore.nome || 'Usuário')
const perfilUsuario = computed(() => authStore.perfil || 'viajante')
const isAuthenticated = computed(() => authStore.isAuthenticated)
const inicialUsuario = computed(() => nomeUsuario.value.charAt(0).toUpperCase())

const badgePerfil = computed(() => {
  if (perfilUsuario.value === 'setor') return 'Setor de Viagens'
  if (perfilUsuario.value === 'dev') return 'Desenvolvedor'
  return 'Colaborador'
})

const menuRecolhido = ref(false)
const abaAtiva = ref('nova_solicitacao')
const abaAtivaClass = 'bg-blue-600/15 text-blue-400 border-l-4 border-blue-500 font-bold rounded-lg'
const abaInativaClass = 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/20 border-l-4 border-transparent rounded-lg'

const tituloAba = computed(() => {
  if (abaAtiva.value === 'minhas_viagens') return 'Minhas Viagens'
  if (abaAtiva.value === 'gestao_creditos') return 'Gestão de Créditos'
  return 'Nova Solicitação de Viagem'
})

const subtituloAba = computed(() => {
  if (abaAtiva.value === 'minhas_viagens') return 'Monitore e acione cancelamentos/remarcações.'
  if (abaAtiva.value === 'gestao_creditos') return 'Acompanhe créditos gerados pelas solicitações.'
  return 'Preencha os dados para abrir uma nova solicitação corporativa.'
})

const apiClient = createApiClient({
  baseUrl: '/api/v1',
  getToken: () => authStore.getToken(),
  onUnauthorized: () => {
    authStore.clearAll()
  },
})

const indexApi = createIndexApi(apiClient)

const tipoSolicitacao = ref('proprio')
const cpfBusca = ref('')
const buscandoColaborador = ref(false)
const viajanteDados = ref(null)
const celularViajante = ref('')
const dataNascimentoViajante = ref('')
const perfilSalvo = ref(false)
const erroBusca = ref('')
const erroBuscaProprioUsuario = ref('')

const formViagem = reactive({
  origem_cidade: '',
  origem_estado: '',
  destino_cidade: '',
  destino_estado: '',
  data_ida: '',
  data_volta: '',
  motivo_viagem: '',
  tipo_servico: [],
  preferencia_voo: null,
  preferencia_voo_volta: null,
})

const formPreferencias = reactive({
  aereo_periodo_preferido: '',
  aereo_tipo_trecho: 'ambos',
  bagagem_extra: false,
  observacoes_viajante: '',
  quarto_excecao_saude: false,
})

const periodosVoo = ref([])
const enviandoSolicitacao = ref(false)
const erroEnvio = ref('')
const protocoloGerado = ref('')
const classificacaoGerada = ref('')

const historico = ref([])
const historicoCarregando = ref(false)

const meusCreditos = ref([])
const viagemACancelar = ref(null)
const viagemARemarcar = ref(null)

const cancelamentoAbertoId = ref(null)
const remarcacaoAbertaId = ref(null)
const enviandoCancelar = ref(false)
const enviandoRemarcar = ref(false)

const mostrandoModalLGPD = ref(false)
const registrandoConsentimento = ref(false)
const erroConsentimento = ref('')

const servicosDisponiveis = [
  { valor: 'Aereo', label: 'Aéreo' },
  { valor: 'Rodoviario', label: 'Rodoviário' },
  { valor: 'Hospedagem', label: 'Hospedagem' },
  { valor: 'Carro', label: 'Carro' },
]

const passo2Valido = computed(() => {
  return (
    formViagem.destino_cidade.trim() !== ''
    && formViagem.data_ida.length === 10
    && formViagem.motivo_viagem.trim() !== ''
    && formViagem.tipo_servico.length > 0
  )
})

function hydrateSessionFromLegacyStorage() {
  const token = localStorage.getItem('token')
  const nome = localStorage.getItem('nome_usuario')
  const perfil = localStorage.getItem('perfil')
  const username = localStorage.getItem('username_ad')

  if (token && !authStore.token) authStore.setToken(token)
  if (nome && !authStore.nome) authStore.setNome(nome)
  if (perfil && !authStore.perfil) authStore.setPerfil(perfil)
  if (username && !authStore.username) authStore.setUsername(username)
}

async function ensureOk(responseLike, fallbackMessage) {
  if (responseLike.ok) return responseLike.data
  throw createError(responseLike, fallbackMessage)
}

function parseApiError(error, fallbackMessage) {
  return parseErrorMessage(error?.payload, error?.message || fallbackMessage)
}

async function realizarLogin() {
  erroLogin.value = ''
  semAcessoAd.value = false
  carregando.value = true

  try {
    const response = await indexApi.realizarLogin({
      username: loginForm.username,
      password: loginForm.password,
      agencia: null,
    })

    if (response.status === 403) {
      semAcessoAd.value = true
      throw createError(response, 'Você não possui acesso ao sistema.')
    }

    const data = await ensureOk(response, 'Erro de autenticação.')

    authStore.setToken(data.access_token || '')
    authStore.setNome(data.nome_usuario || '')
    authStore.setPerfil(data.perfil || 'viajante')
    authStore.setUsername(data.username || '')

    localStorage.setItem('token', data.access_token || '')
    localStorage.setItem('nome_usuario', data.nome_usuario || '')
    localStorage.setItem('perfil', data.perfil || 'viajante')
    localStorage.setItem('username_ad', data.username || '')

    if (data.perfil === 'setor') {
      await router.push('/setor')
      return
    }

    await bootstrapPagina()
  } catch (error) {
    erroLogin.value = parseApiError(error, 'Falha ao autenticar.')
  } finally {
    carregando.value = false
  }
}

function logout() {
  const lgpdAceito = localStorage.getItem(LGPD_ACCEPT_KEY)
  const lgpdData = localStorage.getItem(LGPD_ACCEPT_DATE_KEY)

  authStore.clearAll()
  localStorage.removeItem('token')
  localStorage.removeItem('nome_usuario')
  localStorage.removeItem('perfil')
  localStorage.removeItem('username_ad')

  if (lgpdAceito) localStorage.setItem(LGPD_ACCEPT_KEY, lgpdAceito)
  if (lgpdData) localStorage.setItem(LGPD_ACCEPT_DATE_KEY, lgpdData)

  loginForm.password = ''
  abaAtiva.value = 'nova_solicitacao'
  novaSolicitacao()
}

function verificarConsentimentoLGPD() {
  const aceito = localStorage.getItem(LGPD_ACCEPT_KEY)
  const data = localStorage.getItem(LGPD_ACCEPT_DATE_KEY)
  const hoje = new Date().toISOString().split('T')[0]
  mostrandoModalLGPD.value = !(aceito && data === hoje)
}

async function aceitarConsentimentoLGPD() {
  registrandoConsentimento.value = true
  erroConsentimento.value = ''
  try {
    const response = await indexApi.registrarConsentimentoLGPD({ aceito: true, versao_politica: '1.0' })
    await ensureOk(response, 'Erro ao registrar consentimento.')
    const hoje = new Date().toISOString().split('T')[0]
    localStorage.setItem(LGPD_ACCEPT_KEY, 'true')
    localStorage.setItem(LGPD_ACCEPT_DATE_KEY, hoje)
    mostrandoModalLGPD.value = false
  } catch (error) {
    erroConsentimento.value = parseApiError(error, 'Erro de conexão ao registrar consentimento.')
  } finally {
    registrandoConsentimento.value = false
  }
}

async function buscarProprioUsuario() {
  erroBuscaProprioUsuario.value = ''
  if (!authStore.username) {
    erroBuscaProprioUsuario.value = 'Não foi possível identificar seu usuário AD.'
    return
  }

  buscandoColaborador.value = true
  try {
    const response = await indexApi.buscarColaborador(authStore.username)
    const data = await ensureOk(response, 'Não foi possível identificar seu cadastro.')
    if (!data?.sucesso || !data?.dados) {
      throw new Error('Não foi possível identificar seu cadastro automaticamente.')
    }
    viajanteDados.value = data.dados
    celularViajante.value = ''
    dataNascimentoViajante.value = ''
    perfilSalvo.value = false
    await carregarPerfilViajante(data.dados.user_name)
  } catch (error) {
    viajanteDados.value = null
    erroBuscaProprioUsuario.value = parseApiError(error, 'Informe CPF ou matrícula manualmente para continuar.')
  } finally {
    buscandoColaborador.value = false
  }
}

async function buscarColaboradorGCP() {
  erroBusca.value = ''
  if (!cpfBusca.value.trim()) {
    erroBusca.value = 'Informe CPF ou matrícula para buscar.'
    return
  }

  buscandoColaborador.value = true
  try {
    const response = await indexApi.buscarColaborador(cpfBusca.value.trim())
    const data = await ensureOk(response, 'Colaborador não encontrado.')
    viajanteDados.value = data.dados || data
    celularViajante.value = ''
    dataNascimentoViajante.value = ''
    perfilSalvo.value = false
    await carregarPerfilViajante(viajanteDados.value?.user_name)
  } catch (error) {
    erroBusca.value = parseApiError(error, 'Falha ao buscar colaborador.')
  } finally {
    buscandoColaborador.value = false
  }
}

function mascaraData(event) {
  dataNascimentoViajante.value = maskDateBR(event.target.value)
}

function mascaraDataIda(event) {
  formViagem.data_ida = maskDateBR(event.target.value)
}

function mascaraDataVolta(event) {
  formViagem.data_volta = maskDateBR(event.target.value)
}

function mascaraCelular(event) {
  celularViajante.value = maskPhoneBR(event.target.value)
}

async function carregarPerfilViajante(username) {
  if (!username) return
  try {
    const response = await indexApi.obterPerfilViajante(username)
    if (!response.ok) return

    const perfil = response.data || {}
    if (perfil.celular) celularViajante.value = maskPhoneBR(perfil.celular)
    if (perfil.data_nascimento) dataNascimentoViajante.value = perfil.data_nascimento
    if (perfil.celular || perfil.data_nascimento) perfilSalvo.value = true
  } catch {
    // silencioso no carregamento passivo
  }
}

async function salvarPerfilViajante() {
  if (!viajanteDados.value?.user_name) return
  if (!celularViajante.value && !dataNascimentoViajante.value) return

  try {
    const response = await indexApi.salvarPerfilViajante(viajanteDados.value.user_name, {
      celular: celularViajante.value,
      data_nascimento: dataNascimentoViajante.value,
    })
    await ensureOk(response, 'Erro ao salvar perfil do viajante.')
    perfilSalvo.value = true
  } catch (error) {
    erroEnvio.value = parseApiError(error, 'Erro ao salvar dados do perfil.')
  }
}

async function carregarPeriodosVoo() {
  try {
    const response = await indexApi.listarPeriodosVoo()
    if (!response.ok) return
    periodosVoo.value = response.data?.periodos || []
  } catch {
    periodosVoo.value = []
  }
}

async function enviarSolicitacao() {
  erroEnvio.value = ''
  if (!viajanteDados.value) {
    erroEnvio.value = 'Identifique o viajante antes de enviar a solicitação.'
    return
  }

  if (
    formPreferencias.quarto_excecao_saude
    && formViagem.tipo_servico.includes('Aereo')
    && !formPreferencias.observacoes_viajante.trim()
  ) {
    erroEnvio.value = 'Preencha observações para exceção de quarto por saúde.'
    return
  }

  if (formViagem.data_volta) {
    const ida = parseDateBR(formViagem.data_ida)
    const volta = parseDateBR(formViagem.data_volta)
    if (ida && volta && volta < ida) {
      erroEnvio.value = 'A data de volta não pode ser anterior à data de ida.'
      return
    }
  }

  enviandoSolicitacao.value = true
  try {
    const payload = {
      ...formViagem,
      ...formPreferencias,
      data_ida: toISODateTime(formViagem.data_ida),
      data_volta: toISODateTime(formViagem.data_volta) || null,
      via_delegacao: tipoSolicitacao.value !== 'proprio',
      aprovador_n1_email: viajanteDados.value?.aprovador_n1_email || '',
      aprovador_n1_nome: viajanteDados.value?.aprovador_n1_nome || '',
      aprovador_n2_email: viajanteDados.value?.aprovador_n2_email || '',
      aprovador_n2_nome: viajanteDados.value?.aprovador_n2_nome || '',
      viajante_nome: viajanteDados.value?.nome || '',
      viajante_cpf: viajanteDados.value?.cpf || '',
      viajante_matricula: viajanteDados.value?.matricula || '',
      viajante_email: viajanteDados.value?.email || '',
      viajante_cargo: viajanteDados.value?.cargo || '',
      viajante_filial: viajanteDados.value?.filial || '',
      viajante_centro_custo: viajanteDados.value?.centro_custo || '',
      viajante_cod_centro_custo: viajanteDados.value?.cod_centro_custo || '',
      viajante_data_admissao: viajanteDados.value?.data_admissao || '',
      viajante_celular: celularViajante.value,
      viajante_data_nascimento: dataNascimentoViajante.value,
    }

    const response = await indexApi.enviarSolicitacaoViagem(payload)
    const data = await ensureOk(response, 'Erro ao enviar solicitação.')
    protocoloGerado.value = data.protocolo || ''
    classificacaoGerada.value = data.classificacao || ''
    await carregarHistorico()
    abaAtiva.value = 'minhas_viagens'
  } catch (error) {
    erroEnvio.value = parseApiError(error, 'Erro ao enviar solicitação.')
  } finally {
    enviandoSolicitacao.value = false
  }
}

function novaSolicitacao() {
  tipoSolicitacao.value = 'proprio'
  cpfBusca.value = ''
  viajanteDados.value = null
  celularViajante.value = ''
  dataNascimentoViajante.value = ''
  perfilSalvo.value = false
  erroBusca.value = ''
  erroBuscaProprioUsuario.value = ''
  erroEnvio.value = ''
  protocoloGerado.value = ''
  classificacaoGerada.value = ''

  formViagem.origem_cidade = ''
  formViagem.origem_estado = ''
  formViagem.destino_cidade = ''
  formViagem.destino_estado = ''
  formViagem.data_ida = ''
  formViagem.data_volta = ''
  formViagem.motivo_viagem = ''
  formViagem.tipo_servico = []
  formViagem.preferencia_voo = null
  formViagem.preferencia_voo_volta = null

  formPreferencias.aereo_periodo_preferido = ''
  formPreferencias.aereo_tipo_trecho = 'ambos'
  formPreferencias.bagagem_extra = false
  formPreferencias.observacoes_viajante = ''
  formPreferencias.quarto_excecao_saude = false

  if (isAuthenticated.value && tipoSolicitacao.value === 'proprio') {
    buscarProprioUsuario()
  }
}

async function carregarHistorico() {
  if (!isAuthenticated.value) return
  historicoCarregando.value = true
  try {
    const response = await indexApi.listarMinhasViagens()
    if (!response.ok) {
      historico.value = []
      return
    }
    historico.value = Array.isArray(response.data) ? response.data : []
  } catch {
    historico.value = []
  } finally {
    historicoCarregando.value = false
  }
}

async function carregarMeusCreditos() {
  if (!isAuthenticated.value) return
  try {
    const response = await indexApi.listarMeusCreditos()
    if (!response.ok) {
      meusCreditos.value = []
      return
    }
    meusCreditos.value = Array.isArray(response.data) ? response.data : []
  } catch {
    meusCreditos.value = []
  }
}

function abrirCancelar(item) {
  viagemACancelar.value = item
  cancelamentoAbertoId.value = item.id
  remarcacaoAbertaId.value = null
  viagemARemarcar.value = null
}

function abrirRemarcacao(item) {
  viagemARemarcar.value = item
  remarcacaoAbertaId.value = item.id
  cancelamentoAbertoId.value = null
  viagemACancelar.value = null
}

function fecharCancelamento() {
  cancelamentoAbertoId.value = null
  viagemACancelar.value = null
}

function fecharRemarcacao() {
  remarcacaoAbertoId.value = null
  viagemARemarcar.value = null
}

async function confirmarCancelarViagem(payload) {
  if (!viagemACancelar.value?.id) return
  enviandoCancelar.value = true
  try {
    const response = await indexApi.solicitarCancelamento(viagemACancelar.value.id, {
      itens_a_cancelar: payload.itens.join(','),
      motivo_cancelamento: payload.motivo,
    })
    await ensureOk(response, 'Erro ao solicitar cancelamento.')
    fecharCancelamento()
    await carregarHistorico()
    await carregarMeusCreditos()
  } catch (error) {
    erroEnvio.value = parseApiError(error, 'Não foi possível solicitar cancelamento.')
  } finally {
    enviandoCancelar.value = false
  }
}

async function confirmarRemarcarViagem(payload) {
  if (!viagemARemarcar.value?.id) return
  enviandoRemarcar.value = true
  try {
    const response = await indexApi.solicitarRemarcacao(viagemARemarcar.value.id, {
      data_ida: payload.data_ida,
      data_volta: payload.data_volta || null,
      motivo_cancelamento: payload.motivo,
    })
    await ensureOk(response, 'Erro ao solicitar remarcação.')
    fecharRemarcacao()
    await carregarHistorico()
  } catch (error) {
    erroEnvio.value = parseApiError(error, 'Não foi possível solicitar remarcação.')
  } finally {
    enviandoRemarcar.value = false
  }
}

function statusLabelMini(status) {
  return {
    pendente: 'Pendente',
    aprovada: 'Aprovada',
    reprovada: 'Reprovada',
    cotando: 'Em Cotação',
    cotacao_enviada: 'Cotação Enviada',
    cancelada: 'Cancelada',
    concluida: 'Concluída',
    pendente_cancelamento: 'Cancelamento em Liquidação',
    pendente_remarcacao: 'Remarcação em Liquidação',
    pendente_aprovacao_cancelamento: 'Aprovação de Cancelamento',
    pendente_aprovacao_remarcacao: 'Aprovação de Remarcação',
  }[status] || status
}

function statusCorMini(status) {
  return {
    pendente: 'bg-amber-100 text-amber-700 border-amber-200',
    aprovada: 'bg-green-100 text-green-700 border-green-200',
    reprovada: 'bg-red-100 text-red-700 border-red-200',
    cotando: 'bg-blue-100 text-blue-700 border-blue-200',
    cotacao_enviada: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    cancelada: 'bg-gray-200 text-gray-500 border-gray-300',
    concluida: 'bg-teal-100 text-teal-700 border-teal-200',
    pendente_cancelamento: 'bg-orange-100 text-orange-700 border-orange-200',
    pendente_remarcacao: 'bg-cyan-100 text-cyan-700 border-cyan-200',
    pendente_aprovacao_cancelamento: 'bg-purple-100 text-purple-700 border-purple-200',
    pendente_aprovacao_remarcacao: 'bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200',
  }[status] || 'bg-gray-100 text-gray-500 border-gray-200'
}

function formatarData(data) {
  if (!data) return '—'
  try {
    const dataBase = String(data).split('T')[0]
    const [ano, mes, dia] = dataBase.split('-')
    return `${dia}/${mes}/${ano}`
  } catch {
    return String(data)
  }
}

function irParaHistorico() {
  abaAtiva.value = 'minhas_viagens'
  carregarHistorico()
}

function irParaCreditos() {
  abaAtiva.value = 'gestao_creditos'
  carregarMeusCreditos()
}

async function bootstrapPagina() {
  verificarConsentimentoLGPD()
  await carregarPeriodosVoo()
  await carregarHistorico()
  await carregarMeusCreditos()
  if (tipoSolicitacao.value === 'proprio') {
    await buscarProprioUsuario()
  }
}

watch(tipoSolicitacao, (novoTipo) => {
  viajanteDados.value = null
  celularViajante.value = ''
  dataNascimentoViajante.value = ''
  perfilSalvo.value = false
  erroBusca.value = ''
  erroBuscaProprioUsuario.value = ''
  if (novoTipo === 'proprio' && isAuthenticated.value) {
    buscarProprioUsuario()
  }
})

onMounted(async () => {
  hydrateSessionFromLegacyStorage()
  if (isAuthenticated.value) {
    await bootstrapPagina()
  }
})
</script>

<style>
.bg-viagens {
  background-image: linear-gradient(rgba(15, 23, 42, 0.75), rgba(15, 23, 42, 0.9)), var(--vl-bg-aviao);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
