import React from 'react'

export default function LgpdConsentModal({ isOpen, loading, errorMessage, onAccept, onReject }) {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/80 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="lgpd-modal-title">
            <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
                <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-5">
                    <h2 id="lgpd-modal-title" className="text-lg font-bold text-white">Lei Geral de Proteção de Dados (LGPD)</h2>
                </div>

                <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
                    <p className="text-sm text-gray-700 leading-relaxed">
                        Para usar o <strong>Viagens Labs</strong>, você precisa consentir com o processamento de dados pessoais.
                    </p>

                    <div className="vl-blue-info-surface p-4 space-y-2 text-xs text-gray-700">
                        <p><strong>📋 O que coletamos:</strong></p>
                        <ul className="list-disc list-inside space-y-1 ml-1">
                            <li>Nome, CPF e data de nascimento</li>
                            <li>Dados profissionais e de viagem</li>
                            <li>Dados de sistema para auditoria</li>
                        </ul>
                    </div>

                    {errorMessage ? (
                        <div className="vl-red-error-surface p-3 text-xs text-red-700" role="status" aria-live="polite">
                            {errorMessage}
                        </div>
                    ) : null}
                </div>

                <div className="px-6 py-4 border-t border-gray-100 flex justify-between items-center gap-3 shrink-0">
                    <button type="button" className="min-h-11 px-3 py-2 border border-gray-300 text-gray-600 rounded-lg text-xs font-semibold hover:bg-gray-50 transition" onClick={onReject}>
                        Rejeitar e Sair
                    </button>
                    <button type="button" disabled={loading} className="min-h-11 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50" onClick={onAccept}>
                        {loading ? 'Processando...' : 'Aceitar e Continuar'}
                    </button>
                </div>
            </div>
        </div>
    )
}
