import React, { useEffect, useState } from 'react'

const itensDisponiveis = ['Aereo', 'Hospedagem', 'Rodoviario', 'Carro']

export default function CancelTravelModal({ isOpen, loading, trip, onClose, onSubmit }) {
    const [motivo, setMotivo] = useState('')
    const [itens, setItens] = useState([])

    useEffect(() => {
        if (!isOpen) return
        setMotivo('')
        setItens([])
    }, [isOpen])

    if (!isOpen) return null

    function toggleItem(item) {
        setItens((prev) => (prev.includes(item) ? prev.filter((v) => v !== item) : [...prev, item]))
    }

    function enviar(event) {
        event.preventDefault()
        onSubmit({ motivo, itens })
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="cancel-modal-title">
            <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 flex flex-col max-h-[90vh]">
                <div className="absolute top-0 left-0 w-full h-[3px] bg-red-500" />
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                    <h3 id="cancel-modal-title" className="text-base font-bold text-gray-800">Solicitar Cancelamento de Viagem</h3>
                    <button type="button" className="text-gray-400 hover:text-gray-600 text-sm" onClick={onClose}>✕</button>
                </div>

                <form className="p-6 overflow-y-auto space-y-4" onSubmit={enviar}>
                    <div className="vl-blue-info-surface p-3 text-xs text-blue-800 font-medium">ℹ️ <strong>Regra:</strong> cancelamento sem custos até 24 horas após criação.</div>

                    {trip ? (
                        <div className="bg-gray-50 p-3 rounded-lg border text-xs text-gray-600">
                            Protocolo: <strong className="text-gray-800">#{trip.protocolo}</strong><br />
                            Destino: <strong className="text-gray-800">{trip.destino_cidade}</strong>
                        </div>
                    ) : null}

                    <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-2">Itens a cancelar <span className="text-red-500">*</span></label>
                        <div className="grid grid-cols-2 gap-2">
                            {itensDisponiveis.map((item) => (
                                <label key={item} className="flex items-center p-2 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer text-xs transition">
                                    <input type="checkbox" checked={itens.includes(item)} onChange={() => toggleItem(item)} className="text-red-600 focus:ring-red-500 h-3.5 w-3.5" />
                                    <span className="ml-2 font-medium text-gray-700">{item}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label htmlFor="cancel-modal-motivo" className="block text-xs font-semibold text-gray-700 mb-1.5">Justificativa <span className="text-red-500">*</span></label>
                        <textarea id="cancel-modal-motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} rows={3} placeholder="Descreva o motivo..." className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 resize-none" />
                    </div>

                    <div className="px-0 py-1 flex justify-end gap-3 shrink-0">
                        <button type="button" className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-50 transition" onClick={onClose}>Fechar</button>
                        <button type="submit" disabled={loading || !motivo || !itens.length} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50">
                            {loading ? 'Enviando...' : 'Solicitar Cancelamento'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
