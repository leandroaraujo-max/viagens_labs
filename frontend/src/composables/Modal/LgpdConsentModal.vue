<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/80 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="lgpd-modal-title"
    >
      <div class="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
        <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-5">
          <h2 id="lgpd-modal-title" class="text-lg font-bold text-white">Lei Geral de Proteção de Dados (LGPD)</h2>
        </div>

        <div class="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          <p class="text-sm text-gray-700 leading-relaxed">
            Para usar o <strong>Viagens Labs</strong>, você precisa consentir com o processamento de dados pessoais.
          </p>

          <div class="vl-blue-info-surface p-4 space-y-2 text-xs text-gray-700">
            <p><strong>📋 O que coletamos:</strong></p>
            <ul class="list-disc list-inside space-y-1 ml-1">
              <li>Nome, CPF e data de nascimento</li>
              <li>Dados profissionais e de viagem</li>
              <li>Dados de sistema para auditoria</li>
            </ul>
          </div>

          <div v-if="errorMessage" class="vl-red-error-surface p-3 text-xs text-red-700" role="status" aria-live="polite">
            {{ errorMessage }}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 flex justify-between items-center gap-3 shrink-0">
          <button
            type="button"
            class="min-h-11 px-3 py-2 border border-gray-300 text-gray-600 rounded-lg text-xs font-semibold hover:bg-gray-50 transition"
            @click="$emit('reject')"
          >
            Rejeitar e Sair
          </button>
          <button
            type="button"
            :disabled="loading"
            class="min-h-11 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50"
            @click="$emit('accept')"
          >
            {{ loading ? 'Processando...' : 'Aceitar e Continuar' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  isOpen: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
})

defineEmits(['accept', 'reject'])
</script>
