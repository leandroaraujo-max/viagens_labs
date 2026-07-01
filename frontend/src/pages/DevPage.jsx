import React, { useEffect, useMemo, useState } from 'react'
import { createApiClient } from '../services/api-client.js'
import { createDevApi } from '../services/dev-api.js'
import { parseErrorMessage } from '../services/http-errors.js'

function formatDateTime(value) {
    if (!value) return '—'
    try {
        return new Date(value).toLocaleString('pt-BR')
    } catch {
        return String(value)
    }
}

export default function DevPage() {
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [nomeUsuario] = useState(localStorage.getItem('nome_usuario') || 'Dev')
    const [stats, setStats] = useState(null)
    const [atividade, setAtividade] = useState([])
    const [solicitacoes, setSolicitacoes] = useState([])
    const [loading, setLoading] = useState(false)
    const [actionLoading, setActionLoading] = useState(false)
    const [feedback, setFeedback] = useState({ kind: '', message: '' })

    const apiClient = useMemo(() => createApiClient({
        baseUrl: '/api/v1',
        getToken: () => token,
        onUnauthorized: () => {
            localStorage.removeItem('token')
            localStorage.removeItem('nome_usuario')
            localStorage.removeItem('perfil')
            setToken('')
        },
    }), [token])

    const devApi = useMemo(() => createDevApi(apiClient), [apiClient])

    async function carregarTudo() {
        setLoading(true)
        setFeedback({ kind: '', message: '' })
        try {
            const [statsResp, atividadeResp, solicitacoesResp] = await Promise.all([
                devApi.obterStats(),
                devApi.obterAtividade(20),
                devApi.listarSolicitacoes('limit=15'),
            ])

            if (!statsResp.ok) throw new Error(parseErrorMessage(statsResp.data, 'Erro ao carregar métricas.'))
            if (!atividadeResp.ok) throw new Error(parseErrorMessage(atividadeResp.data, 'Erro ao carregar atividade.'))
            if (!solicitacoesResp.ok) throw new Error(parseErrorMessage(solicitacoesResp.data, 'Erro ao carregar solicitações.'))

            setStats(statsResp.data || null)
            setAtividade(Array.isArray(atividadeResp.data) ? atividadeResp.data : [])
            setSolicitacoes(Array.isArray(solicitacoesResp.data) ? solicitacoesResp.data : [])
        } catch (error) {
            setFeedback({ kind: 'error', message: error.message || 'Falha no carregamento.' })
        } finally {
            setLoading(false)
        }
    }

    async function executarAcaoServico(action) {
        setActionLoading(true)
        setFeedback({ kind: '', message: '' })
        try {
            const response = action === 'nginx' ? await devApi.recarregarNginx() : await devApi.reiniciarBackend()
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Falha ao executar ação.'))
            setFeedback({ kind: 'success', message: action === 'nginx' ? 'Nginx recarregado com sucesso.' : 'Backend reiniciado com sucesso.' })
        } catch (error) {
            setFeedback({ kind: 'error', message: error.message || 'Erro ao executar ação.' })
        } finally {
            setActionLoading(false)
        }
    }

    useEffect(() => {
        if (token) void carregarTudo()
    }, [token])

    if (!token) {
        return (
            <main className="min-h-screen bg-[#0a0f1e] p-6 flex items-center justify-center">
                <section className="vl-shell-dark-card text-center" role="status" aria-live="polite">
                    <h1 className="text-lg font-bold text-white mb-2">Sessão expirada</h1>
                    <p className="text-sm text-slate-300">Faça login no portal principal para acessar o Dev.</p>
                </section>
            </main>
        )
    }

    return (
        <main className="min-h-screen bg-[#0a0f1e] text-slate-200 p-6 space-y-6">
            <header className="bg-[#111827] border border-slate-700 rounded-xl p-4 flex items-center justify-between">
                <div>
                    <h1 className="text-base font-bold text-white">Portal Dev (React)</h1>
                    <p className="text-xs text-slate-400">Operador: {nomeUsuario}</p>
                </div>
                <button type="button" onClick={carregarTudo} disabled={loading} className="min-h-11 px-4 py-2 rounded-lg border border-slate-600 text-xs font-bold hover:bg-slate-800 disabled:opacity-50">{loading ? 'Atualizando...' : 'Atualizar'}</button>
            </header>

            {feedback.message ? (
                <p className={`text-xs px-3 py-2 rounded-lg border ${feedback.kind === 'error' ? 'bg-red-950/40 border-red-700 text-red-300' : 'bg-emerald-950/30 border-emerald-700 text-emerald-300'}`} role="status" aria-live="polite">
                    {feedback.kind === 'error' ? '⚠️ ' : '✅ '}
                    {feedback.message}
                </p>
            ) : null}

            <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <article className="bg-[#111827] border border-slate-700 rounded-xl p-4"><p className="text-[11px] text-slate-400">Solicitações</p><p className="text-2xl font-bold mt-1">{stats?.total_solicitacoes ?? '—'}</p></article>
                <article className="bg-[#111827] border border-slate-700 rounded-xl p-4"><p className="text-[11px] text-slate-400">Agências</p><p className="text-2xl font-bold mt-1">{stats?.total_agencias ?? '—'}</p></article>
                <article className="bg-[#111827] border border-slate-700 rounded-xl p-4"><p className="text-[11px] text-slate-400">Cotações</p><p className="text-2xl font-bold mt-1">{stats?.total_cotacoes ?? '—'}</p></article>
                <article className="bg-[#111827] border border-slate-700 rounded-xl p-4"><p className="text-[11px] text-slate-400">Vouchers</p><p className="text-2xl font-bold mt-1">{stats?.total_vouchers ?? '—'}</p></article>
            </section>

            <section className="bg-[#111827] border border-slate-700 rounded-xl p-4 space-y-3">
                <h2 className="text-sm font-bold text-white">Ações de serviço</h2>
                <div className="flex flex-wrap gap-2">
                    <button type="button" disabled={actionLoading} onClick={() => executarAcaoServico('nginx')} className="min-h-11 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold disabled:opacity-50">Recarregar Nginx</button>
                    <button type="button" disabled={actionLoading} onClick={() => executarAcaoServico('backend')} className="min-h-11 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold disabled:opacity-50">Reiniciar Backend</button>
                </div>
            </section>

            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <article className="bg-[#111827] border border-slate-700 rounded-xl p-4">
                    <h2 className="text-sm font-bold text-white mb-3">Atividade recente</h2>
                    <ul className="space-y-2 text-xs max-h-64 overflow-y-auto">
                        {atividade.map((item, idx) => <li key={item.id || idx} className="border border-slate-800 rounded-lg p-2"><p className="text-slate-200">{item.acao || item.evento || 'Evento'}</p><p className="text-slate-500">{formatDateTime(item.data || item.timestamp)}</p></li>)}
                        {!atividade.length ? <li className="text-slate-500">Sem eventos.</li> : null}
                    </ul>
                </article>
                <article className="bg-[#111827] border border-slate-700 rounded-xl p-4">
                    <h2 className="text-sm font-bold text-white mb-3">Solicitações recentes</h2>
                    <div className="space-y-2 text-xs max-h-64 overflow-y-auto">
                        {solicitacoes.map((item) => <div key={item.id} className="border border-slate-800 rounded-lg p-2"><p className="font-mono text-slate-300">#{item.protocolo || item.id}</p><p className="text-slate-400">{item.destino_cidade || '—'} · {item.status || '—'}</p></div>)}
                        {!solicitacoes.length ? <p className="text-slate-500">Sem solicitações.</p> : null}
                    </div>
                </article>
            </section>
        </main>
    )
}
