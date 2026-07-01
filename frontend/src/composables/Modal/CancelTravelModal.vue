<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cancel-modal-title"
    >
      <div class="relative w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 flex flex-col max-h-[90vh]">
        <div class="absolute top-0 left-0 w-full h-[3px] bg-red-500" />

        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 id="cancel-modal-title" class="text-base font-bold text-gray-800">Solicitar Cancelamento de Viagem</h3>
          <button type="button" class="text-gray-400 hover:text-gray-600 text-sm" @click="$emit('close')">✕</button>
        </div>

        <form class="p-6 overflow-y-auto space-y-4" @submit.prevent="enviar">
          <div class="vl-blue-info-surface p-3 text-xs text-blue-800 font-medium">
            ℹ️ <strong>Regra:</strong> cancelamento sem custos até 24 horas após criação.
          </div>

          <div v-if="trip" class="bg-gray-50 p-3 rounded-lg border text-xs text-gray-600">
            Protocolo: <strong class="text-gray-800">#{{ trip.protocolo }}</strong><br>
            Destino: <strong class="text-gray-800">{{ trip.destino_cidade }}</strong>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-2">Itens a cancelar <span class="text-red-500">*</span></label>
            <div class="grid grid-cols-2 gap-2">
              <label v-for="item in itensDisponiveis" :key="item" class="flex items-center p-2 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer text-xs transition">
                <input v-model="itens" type="checkbox" :value="item" class="text-red-600 focus:ring-red-500 h-3.5 w-3.5">
                <span class="ml-2 font-medium text-gray-700">{{ item }}</span>
              </label>
            </div>
          </div>

          <div>
            <label for="cancel-modal-motivo" class="block text-xs font-semibold text-gray-700 mb-1.5">Justificativa <span class="text-red-500">*</span></label>
            <textarea
              id="cancel-modal-motivo"
              v-model.trim="motivo"
              rows="3"
              placeholder="Descreva o motivo..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 resize-none"
            />
          </div>

          <div class="px-0 py-1 flex justify-end gap-3 shrink-0">
            <button type="button" class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-50 transition" @click="$emit('close')">Fechar</button>
            <button type="submit" :disabled="loading || !motivo || !itens.length" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50">
              {{ loading ? 'Enviando...' : 'Solicitar Cancelamento' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  trip: { type: Object, default: null },
})

const emit = defineEmits(['close', 'submit'])

const itensDisponiveis = ['Aereo', 'Hospedagem', 'Rodoviario', 'Carro']
const motivo = ref('')
const itens = ref([])

watch(() => props.isOpen, (open) => {
  if (!open) return
  motivo.value = ''
  itens.value = []
})

function enviar() {
  emit('submit', {
    motivo: motivo.value,
    itens: [...itens.value],
  })
}
</script>
