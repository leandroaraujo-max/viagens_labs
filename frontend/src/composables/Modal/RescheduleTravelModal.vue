<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="reschedule-modal-title"
    >
      <div class="relative w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 flex flex-col max-h-[90vh]">
        <div class="absolute top-0 left-0 w-full h-[3px] bg-blue-500" />

        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 id="reschedule-modal-title" class="text-base font-bold text-gray-800">Solicitar Remarcação de Viagem</h3>
          <button type="button" class="text-gray-400 hover:text-gray-600 text-sm" @click="$emit('close')">✕</button>
        </div>

        <form class="p-6 overflow-y-auto space-y-4" @submit.prevent="enviar">
          <div v-if="trip" class="bg-gray-50 p-3 rounded-lg border text-xs text-gray-600">
            Protocolo: <strong class="text-gray-800">#{{ trip.protocolo }}</strong><br>
            Destino: <strong class="text-gray-800">{{ trip.destino_cidade }}</strong>
          </div>

          <div>
            <label for="reschedule-new-ida" class="block text-xs font-semibold text-gray-700 mb-1.5">Nova Data de Ida <span class="text-red-500">*</span></label>
            <input id="reschedule-new-ida" v-model="dataIda" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" required>
          </div>

          <div>
            <label for="reschedule-new-volta" class="block text-xs font-semibold text-gray-700 mb-1.5">Nova Data de Volta</label>
            <input id="reschedule-new-volta" v-model="dataVolta" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
          </div>

          <div>
            <label for="reschedule-motivo" class="block text-xs font-semibold text-gray-700 mb-1.5">Justificativa <span class="text-red-500">*</span></label>
            <textarea
              id="reschedule-motivo"
              v-model.trim="motivo"
              rows="3"
              placeholder="Descreva o motivo do reagendamento..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none"
            />
          </div>

          <div class="px-0 py-1 flex justify-end gap-3 shrink-0">
            <button type="button" class="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-50 transition" @click="$emit('close')">Fechar</button>
            <button type="submit" :disabled="loading || !motivo || !dataIda" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50">
              {{ loading ? 'Enviando...' : 'Solicitar Remarcação' }}
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

const dataIda = ref('')
const dataVolta = ref('')
const motivo = ref('')

watch(() => props.isOpen, (open) => {
  if (!open) return
  dataIda.value = ''
  dataVolta.value = ''
  motivo.value = ''
})

function enviar() {
  emit('submit', {
    data_ida: dataIda.value,
    data_volta: dataVolta.value,
    motivo: motivo.value,
  })
}
</script>
