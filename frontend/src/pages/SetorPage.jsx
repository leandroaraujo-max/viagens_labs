import React, { useEffect, useMemo, useState } from 'react'
import { createApiClient } from '../services/api-client.js'
import { parseErrorMessage } from '../services/http-errors.js'
import { createSetorApi } from '../services/setor-api.js'

const statusOptions = [
    { value: '', label: 'Todos os status' },
    { value: 'AGUARDANDO_N1', label: 'Aguardando N1' },
    { value: 'AGUARDANDO_N2', label: 'Aguardando N2' },
    { value: 'AGUARDANDO_COTACAO', label: 'Aguardando cotação' },
    { value: 'COTACAO_ENVIADA', label: 'Cotação enviada' },
    { value: 'PENDENTE_APROVACAO_SETOR_COTACAO', label: 'Decidir agência' },
]

const statusLabels = {
    AGUARDANDO_N1: 'Aguardando N1',
    AGUARDANDO_N2: 'Aguardando N2',
    AGUARDANDO_COTACAO: 'Aguardando cotação',
    COTACAO_ENVIADA: 'Cotação enviada',
    PENDENTE_APROVACAO_SETOR_COTACAO: 'Decidir agência',
    CONCLUIDA: 'Concluída',
    REPROVADA: 'Reprovada',
}

const formatDate = (value) => (value ? new Date(value).toLocaleDateString('pt-BR') : '—')

export default function SetorPage() {
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [filters, setFilters] = useState({ status: '', busca: '' })
    const [loading, setLoading] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')
    const [solicitacoes, setSolicitacoes] = useState([])
    const [detalhe, setDetalhe] = useState(null)
    const [actionLoading, setActionLoading] = useState(false)

    const apiClient = useMemo(() => createApiClient({
        baseUrl: '/api/v1',
        getToken: () => token,
        onUnauthorized: () => {
            localStorage.removeItem('token')
            setToken('')
        },
    }), [token])

    const setorApi = useMemo(() => createSetorApi(apiClient), [apiClient])

    async function carregarSolicitacoes() {
        setLoading(true)
        setErrorMessage('')
        try {
            const params = new URLSearchParams()
            if (filters.status) params.set('status', filters.status)
            if (filters.busca) params.set('busca', filters.busca)
            const response = await setorApi.listarSolicitacoes(params.toString())
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Erro ao carregar solicitações.'))
            setSolicitacoes(Array.isArray(response.data) ? response.data : [])
        } catch (error) {
            setErrorMessage(error.message)
        } finally {
            setLoading(false)
        }
    }

    async function abrirDetalhe(id) {
        setActionLoading(true)
        setErrorMessage('')
        try {
            const response = await setorApi.obterDetalhesSolicitacao(id)
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Erro ao carregar detalhes.'))
            setDetalhe(response.data || null)
        } catch (error) {
            setErrorMessage(error.message)
        } finally {
            setActionLoading(false)
        }
    }

    async function decidirSolicitacao(acao) {
        if (!detalhe?.id) return
        setActionLoading(true)
        setErrorMessage('')
        try {
            const response = await setorApi.decidirSolicitacao(detalhe.id, { acao, observacao: '' })
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Erro ao decidir solicitação.'))
            await carregarSolicitacoes()
            const refresh = await setorApi.obterDetalhesSolicitacao(detalhe.id)
            if (refresh.ok) setDetalhe(refresh.data || null)
        } catch (error) {
            setErrorMessage(error.message)
        } finally {
            setActionLoading(false)
        }
    }

    useEffect(() => {
        if (token) void carregarSolicitacoes()
    }, [token])

    if (!token) {
        return (
            <main className="min-h-screen bg-[#0a0f1e] text-white p-6 flex items-center justify-center">
                <section className="vl-shell-dark-card text-center" role="status" aria-live="polite">
                    <h1 className="text-lg font-bold mb-2">Sessão expirada</h1>
                    <p className="text-sm text-slate-300">Faça login novamente no portal principal para acessar o setor.</p>
                </section>
            </main>
        )
    }

    return (
        <main className="min-h-screen bg-[#f8fafc] text-slate-800 p-6 space-y-6">
            <header className="bg-white rounded-xl border border-gray-200 p-4">
                <h1 className="text-base font-bold">Portal do Setor (React)</h1>
                <p className="text-xs text-slate-500">Análise e decisão de solicitações de viagem.</p>
            </header>

            <section className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
                <h2 className="text-sm font-bold">Filtros</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <label className="text-xs font-semibold text-slate-700">Status
                        <select value={filters.status} onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300">
                            {statusOptions.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                        </select>
                    </label>
                    <label className="text-xs font-semibold text-slate-700">Busca
                        <input value={filters.busca} onChange={(e) => setFilters((prev) => ({ ...prev, busca: e.target.value }))} placeholder="Protocolo, usuário, destino..." className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                    </label>
                    <div className="flex items-end">
                        <button type="button" onClick={carregarSolicitacoes} className="min-h-11 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold">Atualizar</button>
                    </div>
                </div>
                {errorMessage ? <p className="text-xs text-red-600" role="status" aria-live="polite">⚠️ {errorMessage}</p> : null}
            </section>

            <section className="bg-white rounded-xl border border-gray-200 p-4 overflow-x-auto">
                <h2 className="text-sm font-bold mb-3">Solicitações</h2>
                {loading ? <p className="text-xs text-slate-500">Carregando...</p> : null}
                <table className="w-full text-xs" aria-label="Tabela de solicitações">
                    <caption className="sr-only">Solicitações de viagem do setor</caption>
                    <thead>
                        <tr className="text-left border-b border-gray-200">
                            <th scope="col" className="py-2 pr-2">Protocolo</th>
                            <th scope="col" className="py-2 pr-2">Destino</th>
                            <th scope="col" className="py-2 pr-2">Ida</th>
                            <th scope="col" className="py-2 pr-2">Status</th>
                            <th scope="col" className="py-2 pr-2">Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {solicitacoes.map((item) => (
                            <tr key={item.id} className="border-b border-gray-100">
                                <td className="py-2 pr-2 font-mono">#{item.protocolo || item.id}</td>
                                <td className="py-2 pr-2">{item.destino_cidade || '—'}</td>
                                <td className="py-2 pr-2">{formatDate(item.data_ida)}</td>
                                <td className="py-2 pr-2">{statusLabels[item.status] || item.status || '—'}</td>
                                <td className="py-2 pr-2">
                                    <button type="button" onClick={() => abrirDetalhe(item.id)} className="min-h-11 px-3 py-1.5 text-[11px] font-bold rounded border border-blue-200 text-blue-700 hover:bg-blue-50">Detalhar</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </section>

            {detalhe ? (
                <section className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
                    <h2 className="text-sm font-bold">Detalhes #{detalhe.protocolo || detalhe.id}</h2>
                    <p className="text-xs"><strong>Solicitante:</strong> {detalhe.solicitante_username || '—'}</p>
                    <p className="text-xs"><strong>Motivo:</strong> {detalhe.motivo_viagem || '—'}</p>
                    <p className="text-xs"><strong>Status atual:</strong> {statusLabels[detalhe.status] || detalhe.status || '—'}</p>
                    <div className="flex gap-2 flex-wrap">
                        <button type="button" disabled={actionLoading} onClick={() => decidirSolicitacao('APROVAR')} className="min-h-11 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold disabled:opacity-50">Aprovar</button>
                        <button type="button" disabled={actionLoading} onClick={() => decidirSolicitacao('REPROVAR')} className="min-h-11 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold disabled:opacity-50">Reprovar</button>
                    </div>
                </section>
            ) : null}
        </main>
    )
}
