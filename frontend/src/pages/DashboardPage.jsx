import React, { useMemo, useState } from 'react'
import { createApiClient } from '../services/api-client.js'
import { parseErrorMessage } from '../services/http-errors.js'

const initialForm = {
    destino: '',
    motivo: '',
    data_ida: '',
    data_volta: '',
}

export default function DashboardPage() {
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [nomeUsuario] = useState(localStorage.getItem('nome_usuario') || 'Colaborador')
    const [form, setForm] = useState(initialForm)
    const [loading, setLoading] = useState(false)
    const [feedback, setFeedback] = useState({ kind: '', message: '' })

    const apiClient = useMemo(
        () => createApiClient({
            baseUrl: '',
            getToken: () => token,
            onUnauthorized: () => {
                localStorage.removeItem('token')
                localStorage.removeItem('nome_usuario')
                localStorage.removeItem('perfil')
                setToken('')
            },
        }),
        [token],
    )

    async function criarSolicitacao(event) {
        event.preventDefault()
        setLoading(true)
        setFeedback({ kind: '', message: '' })

        try {
            const payload = {
                ...form,
                data_ida: new Date(form.data_ida).toISOString(),
                data_volta: form.data_volta ? new Date(form.data_volta).toISOString() : null,
            }

            const response = await apiClient.request('/api/v1/viagens/solicitacoes', {
                method: 'POST',
                body: JSON.stringify(payload),
            })

            if (!response.ok) {
                throw new Error(parseErrorMessage(response.data, 'Falha ao criar solicitação.'))
            }

            const id = response.data?.id || '—'
            setFeedback({ kind: 'success', message: `Solicitação #${id} criada com sucesso!` })
            setForm(initialForm)
        } catch (error) {
            setFeedback({ kind: 'error', message: error.message || 'Erro inesperado.' })
        } finally {
            setLoading(false)
        }
    }

    if (!token) {
        return (
            <main className="min-h-screen bg-[#0a0f1e] p-6 flex items-center justify-center">
                <section className="vl-shell-dark-card text-center" role="status" aria-live="polite">
                    <h1 className="text-lg font-bold text-white mb-2">Sessão expirada</h1>
                    <p className="text-sm text-slate-300">Faça login no portal principal para usar o dashboard.</p>
                </section>
            </main>
        )
    }

    return (
        <main className="min-h-screen bg-[#f8fafc] p-6 space-y-6 text-slate-800">
            <header className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between">
                <h1 className="text-base font-bold">Dashboard · ViagensLabs</h1>
                <p className="text-xs text-slate-500">Olá, {nomeUsuario}</p>
            </header>

            <section className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
                <h2 className="text-sm font-bold">Nova solicitação de viagem</h2>

                {feedback.message ? (
                    <p
                        className={`text-xs rounded-lg px-3 py-2 ${feedback.kind === 'error'
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            }`}
                        role="status"
                        aria-live="polite"
                    >
                        {feedback.kind === 'error' ? '⚠️ ' : '✅ '}
                        {feedback.message}
                    </p>
                ) : null}

                <form onSubmit={criarSolicitacao} className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="text-xs font-semibold text-slate-700">
                        Destino
                        <input
                            required
                            value={form.destino}
                            onChange={(event) => setForm((prev) => ({ ...prev, destino: event.target.value }))}
                            className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300"
                        />
                    </label>

                    <label className="text-xs font-semibold text-slate-700">
                        Motivo
                        <input
                            required
                            value={form.motivo}
                            onChange={(event) => setForm((prev) => ({ ...prev, motivo: event.target.value }))}
                            className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300"
                        />
                    </label>

                    <label className="text-xs font-semibold text-slate-700">
                        Data de ida
                        <input
                            required
                            type="datetime-local"
                            value={form.data_ida}
                            onChange={(event) => setForm((prev) => ({ ...prev, data_ida: event.target.value }))}
                            className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300"
                        />
                    </label>

                    <label className="text-xs font-semibold text-slate-700">
                        Data de volta
                        <input
                            type="datetime-local"
                            value={form.data_volta}
                            onChange={(event) => setForm((prev) => ({ ...prev, data_volta: event.target.value }))}
                            className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300"
                        />
                    </label>

                    <div className="md:col-span-2 flex justify-end">
                        <button
                            type="submit"
                            disabled={loading}
                            className="min-h-11 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold disabled:opacity-50"
                        >
                            {loading ? 'Enviando...' : 'Enviar solicitação'}
                        </button>
                    </div>
                </form>
            </section>
        </main>
    )
}
