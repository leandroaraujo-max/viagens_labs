import React, { useEffect, useMemo, useState } from 'react'
import { createApiClient } from '../services/api-client.js'
import { parseErrorMessage } from '../services/http-errors.js'

function joinServices(tipoServico) {
    if (!tipoServico) return '—'
    if (Array.isArray(tipoServico)) return tipoServico.join(' · ')
    return String(tipoServico)
}

export default function AprovacaoPage() {
    const [state, setState] = useState('loading')
    const [errorMessage, setErrorMessage] = useState('')
    const [actionError, setActionError] = useState('')
    const [processing, setProcessing] = useState(false)
    const [currentAction, setCurrentAction] = useState('')
    const [observacao, setObservacao] = useState('')
    const [detalhes, setDetalhes] = useState(null)
    const [resultado, setResultado] = useState(null)

    const tokenUuid = useMemo(() => new URLSearchParams(window.location.search).get('token') || '', [])
    const apiClient = useMemo(() => createApiClient({ baseUrl: '/api/v1' }), [])

    useEffect(() => {
        async function carregar() {
            if (!tokenUuid) {
                setErrorMessage('Token não informado na URL.')
                setState('error')
                return
            }

            const response = await apiClient.request(`/aprovacao/${tokenUuid}`, { auth: false })
            if (!response.ok) {
                setErrorMessage(parseErrorMessage(response.data, 'Token inválido.'))
                setState('error')
                return
            }

            const data = response.data || {}
            setDetalhes(data)

            if (data.expirado) {
                setState('expired')
                return
            }

            if (data.status_token && data.status_token !== 'PENDENTE') {
                setState('already-answered')
                return
            }

            setState('pending')
        }

        void carregar()
    }, [apiClient, tokenUuid])

    async function processar(acao) {
        if (!tokenUuid) return

        setProcessing(true)
        setCurrentAction(acao)
        setActionError('')

        const response = await apiClient.request(`/aprovacao/${tokenUuid}`, {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ acao, observacao }),
        })

        if (!response.ok) {
            setActionError(parseErrorMessage(response.data, 'Erro ao processar aprovação.'))
            setProcessing(false)
            setCurrentAction('')
            return
        }

        setResultado(response.data || null)
        setState('completed')
        setProcessing(false)
        setCurrentAction('')
    }

    if (state === 'loading') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4" aria-live="polite">
                <section className="vl-shell-dark-card text-center">
                    <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-slate-300 text-sm">Carregando solicitação...</p>
                </section>
            </main>
        )
    }

    if (state === 'error') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4">
                <section className="vl-shell-dark-card text-center" role="status" aria-live="polite">
                    <h1 className="text-lg font-bold text-red-300 mb-2">Token inválido</h1>
                    <p className="text-sm text-slate-300">{errorMessage}</p>
                </section>
            </main>
        )
    }

    if (state === 'already-answered') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4">
                <section className="vl-shell-dark-card text-center">
                    <h1 className="text-lg font-bold text-white mb-2">Solicitação já respondida</h1>
                    <p className="text-sm text-slate-300">Protocolo {detalhes?.solicitacao?.protocolo || '—'} já foi processado.</p>
                </section>
            </main>
        )
    }

    if (state === 'expired') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4">
                <section className="vl-shell-dark-card text-center">
                    <h1 className="text-lg font-bold text-white mb-2">Link expirado</h1>
                    <p className="text-sm text-slate-300">O prazo de aprovação foi encerrado.</p>
                </section>
            </main>
        )
    }

    if (state === 'completed') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4">
                <section className="vl-shell-dark-card text-center" role="status" aria-live="polite">
                    <h1 className="text-xl font-bold text-white mb-2">{resultado?.acao === 'aprovar' ? '✅ Aprovado' : '❌ Reprovado'}</h1>
                    <p className="text-sm text-slate-300">Protocolo: {resultado?.protocolo || '—'}</p>
                    <p className="text-xs text-slate-400 mt-2">Status final: {resultado?.status || '—'}</p>
                </section>
            </main>
        )
    }

    return (
        <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4 text-slate-800">
            <section className="bg-white rounded-2xl border border-gray-200 shadow-xl w-full max-w-xl p-6 space-y-4">
                <header>
                    <p className="text-[11px] font-bold uppercase tracking-wider text-blue-600">Aprovação de Viagem</p>
                    <h1 className="text-lg font-bold text-slate-800">Protocolo {detalhes?.solicitacao?.protocolo || '—'}</h1>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <p><strong>Solicitante:</strong> {detalhes?.solicitacao?.solicitante_username || '—'}</p>
                    <p><strong>Destino:</strong> {detalhes?.solicitacao?.destino_cidade || '—'} / {detalhes?.solicitacao?.destino_estado || '—'}</p>
                    <p><strong>Ida:</strong> {detalhes?.solicitacao?.data_ida || '—'}</p>
                    <p><strong>Volta:</strong> {detalhes?.solicitacao?.data_volta || '—'}</p>
                    <p className="md:col-span-2"><strong>Serviços:</strong> {joinServices(detalhes?.solicitacao?.tipo_servico)}</p>
                    <p className="md:col-span-2"><strong>Motivo:</strong> {detalhes?.solicitacao?.motivo_viagem || '—'}</p>
                </div>

                <label className="text-xs font-semibold text-slate-700 block">
                    Observação (opcional)
                    <textarea
                        value={observacao}
                        onChange={(event) => setObservacao(event.target.value)}
                        rows={3}
                        className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300"
                    />
                </label>

                {actionError ? <p className="text-xs text-red-600">⚠️ {actionError}</p> : null}

                <div className="grid grid-cols-2 gap-3">
                    <button
                        type="button"
                        onClick={() => processar('reprovar')}
                        disabled={processing}
                        className="min-h-11 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold disabled:opacity-50"
                    >
                        {processing && currentAction === 'reprovar' ? 'Processando...' : 'Reprovar'}
                    </button>
                    <button
                        type="button"
                        onClick={() => processar('aprovar')}
                        disabled={processing}
                        className="min-h-11 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold disabled:opacity-50"
                    >
                        {processing && currentAction === 'aprovar' ? 'Processando...' : 'Aprovar'}
                    </button>
                </div>
            </section>
        </main>
    )
}
