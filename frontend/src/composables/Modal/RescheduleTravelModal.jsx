import React, { useEffect, useState } from 'react'

export default function RescheduleTravelModal({ isOpen, loading, trip, onClose, onSubmit }) {
    const [dataIda, setDataIda] = useState('')
    const [dataVolta, setDataVolta] = useState('')
    const [motivo, setMotivo] = useState('')

    useEffect(() => {
        if (!isOpen) return
        setDataIda('')
        setDataVolta('')
        setMotivo('')
    }, [isOpen])

    if (!isOpen) return null

    function enviar(event) {
        event.preventDefault()
        onSubmit({ data_ida: dataIda, data_volta: dataVolta, motivo })
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="reschedule-modal-title">
            <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 flex flex-col max-h-[90vh]">
                <div className="absolute top-0 left-0 w-full h-[3px] bg-blue-500" />
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                    <h3 id="reschedule-modal-title" className="text-base font-bold text-gray-800">Solicitar Remarcação de Viagem</h3>
                    <button type="button" aria-label="Fechar modal de remarcação" className="min-h-11 min-w-11 text-gray-400 hover:text-gray-600 text-sm" onClick={onClose}>✕</button>
                </div>

                <form className="p-6 overflow-y-auto space-y-4" onSubmit={enviar}>
                    {trip ? (
                        <div className="bg-gray-50 p-3 rounded-lg border text-xs text-gray-600">
                            Protocolo: <strong className="text-gray-800">#{trip.protocolo}</strong><br />
                            Destino: <strong className="text-gray-800">{trip.destino_cidade}</strong>
                        </div>
                    ) : null}

                    <div>
                        <label htmlFor="reschedule-new-ida" className="block text-xs font-semibold text-gray-700 mb-1.5">Nova Data de Ida <span className="text-red-500">*</span></label>
                        <input id="reschedule-new-ida" value={dataIda} onChange={(e) => setDataIda(e.target.value)} type="date" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" required />
                    </div>

                    <div>
                        <label htmlFor="reschedule-new-volta" className="block text-xs font-semibold text-gray-700 mb-1.5">Nova Data de Volta</label>
                        <input id="reschedule-new-volta" value={dataVolta} onChange={(e) => setDataVolta(e.target.value)} type="date" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>

                    <div>
                        <label htmlFor="reschedule-motivo" className="block text-xs font-semibold text-gray-700 mb-1.5">Justificativa <span className="text-red-500">*</span></label>
                        <textarea id="reschedule-motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} rows={3} placeholder="Descreva o motivo do reagendamento..." className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none" />
                    </div>

                    <div className="px-0 py-1 flex justify-end gap-3 shrink-0">
                        <button type="button" className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-50 transition" onClick={onClose}>Fechar</button>
                        <button type="submit" disabled={loading || !motivo || !dataIda} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50">
                            {loading ? 'Enviando...' : 'Solicitar Remarcação'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
