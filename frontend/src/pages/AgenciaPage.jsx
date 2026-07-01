import React, { useEffect, useMemo, useState } from 'react'
import { createApiClient } from '../services/api-client.js'
import { createAgenciaApi } from '../services/agencia-api.js'
import { parseErrorMessage } from '../services/http-errors.js'

const SERVICE_TO_VOUCHER = {
    Aereo: { value: 'aereo', label: 'Passagem Aérea' },
    Hospedagem: { value: 'hospedagem', label: 'Hospedagem' },
    Rodoviario: { value: 'rodoviario', label: 'Transporte Rodoviário' },
    Carro: { value: 'carro', label: 'Locação de Carro' },
}

function formatDate(value) {
    if (!value) return '—'
    return new Date(value).toLocaleDateString('pt-BR')
}

function parseServices(value) {
    return (value || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
}

export default function AgenciaPage() {
    const [screen, setScreen] = useState('loading')
    const [errorMessage, setErrorMessage] = useState('')
    const [agenciaNome, setAgenciaNome] = useState('Agência')
    const [solicitacao, setSolicitacao] = useState(null)
    const [tokenUuid, setTokenUuid] = useState('')

    const [sendingQuote, setSendingQuote] = useState(false)
    const [quoteError, setQuoteError] = useState('')
    const [quoteSuccess, setQuoteSuccess] = useState('')
    const [quoteForm, setQuoteForm] = useState({
        aereo_companhia: '',
        aereo_numero_voo: '',
        hotel_nome: '',
        rodov_empresa: '',
        carro_locadora: '',
        valor_total: '',
        observacoes: '',
    })

    const [sendingVoucherType, setSendingVoucherType] = useState('')
    const [voucherError, setVoucherError] = useState('')
    const [voucherSuccess, setVoucherSuccess] = useState('')

    const apiClient = useMemo(() => createApiClient({ baseUrl: '/api/v1' }), [])
    const agenciaApi = useMemo(() => createAgenciaApi(apiClient), [apiClient])

    const voucherTypes = useMemo(() => {
        return parseServices(solicitacao?.tipo_servico)
            .map((service) => SERVICE_TO_VOUCHER[service])
            .filter(Boolean)
    }, [solicitacao?.tipo_servico])

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const token = params.get('token')

        if (!token) {
            setErrorMessage('Este portal requer um link de cotação válido enviado por e-mail.')
            setScreen('error')
            return
        }

        setTokenUuid(token)

        async function loadByToken() {
            setScreen('loading')
            const response = await agenciaApi.obterSolicitacaoPorToken(token)

            if (!response.ok) {
                setErrorMessage(parseErrorMessage(response.data, 'Link inválido ou expirado.'))
                setScreen('error')
                return
            }

            const data = response.data || {}
            setAgenciaNome(data.agencia_nome || 'Agência')
            setSolicitacao(data.solicitacao || null)

            if (data.solicitacao?.cotacao) {
                setQuoteForm((prev) => ({ ...prev, ...data.solicitacao.cotacao }))
            }

            setScreen('detail')
        }

        void loadByToken()
    }, [agenciaApi])

    async function handleSubmitQuote(event) {
        event.preventDefault()
        if (!tokenUuid) return

        setSendingQuote(true)
        setQuoteError('')
        setQuoteSuccess('')

        const payload = {
            ...quoteForm,
            valor_total: quoteForm.valor_total === '' ? null : Number(quoteForm.valor_total),
        }

        const response = await agenciaApi.enviarCotacaoPorToken(tokenUuid, payload)

        if (!response.ok) {
            setQuoteError(parseErrorMessage(response.data, 'Erro ao registrar cotação.'))
            setSendingQuote(false)
            return
        }

        setQuoteSuccess('Cotação registrada com sucesso!')
        setSolicitacao((prev) => {
            if (!prev) return prev
            return { ...prev, cotacao: response.data || payload }
        })
        setSendingQuote(false)
    }

    async function handleUploadVoucher(event, voucherType) {
        const file = event.target.files?.[0]
        if (!file || !tokenUuid) return

        setSendingVoucherType(voucherType)
        setVoucherError('')
        setVoucherSuccess('')

        const response = await agenciaApi.enviarVoucherPorToken(tokenUuid, voucherType, file)

        if (!response.ok) {
            setVoucherError(parseErrorMessage(response.data, 'Erro ao enviar voucher.'))
            setSendingVoucherType('')
            return
        }

        setVoucherSuccess(`Voucher (${voucherType}) enviado com sucesso.`)
        setSendingVoucherType('')
        event.target.value = ''
    }

    if (screen === 'loading') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4">
                <section className="vl-shell-dark-card text-center" aria-live="polite">
                    <div className="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-5" />
                    <h1 className="text-lg font-bold text-white">Carregando solicitação...</h1>
                </section>
            </main>
        )
    }

    if (screen === 'error') {
        return (
            <main className="bg-[#0a0f1e] min-h-screen flex items-center justify-center p-4">
                <section className="vl-shell-dark-card text-center">
                    <h1 className="text-xl font-bold text-white mb-3">Link inválido ou expirado</h1>
                    <p className="text-slate-300 text-sm">{errorMessage}</p>
                </section>
            </main>
        )
    }

    return (
        <div className="min-h-screen bg-[#f8fafc] text-slate-800">
            <header className="bg-white border-b border-gray-200/80 px-6 py-3 flex items-center justify-between">
                <div>
                    <h1 className="text-sm font-bold text-gray-800">Portal da Agência (React)</h1>
                    <p className="text-[11px] text-slate-500">{agenciaNome}</p>
                </div>
            </header>

            <main className="max-w-5xl mx-auto p-6 space-y-6">
                <section className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
                    <h2 className="text-base font-bold">Solicitação #{solicitacao?.protocolo || '—'}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                        <p><strong>Destino:</strong> {solicitacao?.destino_cidade || '—'}</p>
                        <p><strong>Ida:</strong> {formatDate(solicitacao?.data_ida)}</p>
                        <p><strong>Volta:</strong> {formatDate(solicitacao?.data_volta)}</p>
                        <p className="md:col-span-3"><strong>Serviços:</strong> {solicitacao?.tipo_servico || '—'}</p>
                    </div>
                </section>

                <section className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
                    <h2 className="text-base font-bold">Registrar cotação comercial</h2>

                    {quoteError ? <p className="text-xs text-red-600">{quoteError}</p> : null}
                    {quoteSuccess ? <p className="text-xs text-emerald-700">{quoteSuccess}</p> : null}

                    <form onSubmit={handleSubmitQuote} className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <label className="text-xs font-semibold text-slate-700">
                            Companhia aérea
                            <input value={quoteForm.aereo_companhia || ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, aereo_companhia: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                        </label>
                        <label className="text-xs font-semibold text-slate-700">
                            Número do voo
                            <input value={quoteForm.aereo_numero_voo || ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, aereo_numero_voo: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                        </label>
                        <label className="text-xs font-semibold text-slate-700">
                            Hotel
                            <input value={quoteForm.hotel_nome || ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, hotel_nome: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                        </label>
                        <label className="text-xs font-semibold text-slate-700">
                            Empresa rodoviária
                            <input value={quoteForm.rodov_empresa || ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, rodov_empresa: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                        </label>
                        <label className="text-xs font-semibold text-slate-700">
                            Locadora
                            <input value={quoteForm.carro_locadora || ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, carro_locadora: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                        </label>
                        <label className="text-xs font-semibold text-slate-700">
                            Valor total (R$)
                            <input type="number" min="0" step="0.01" value={quoteForm.valor_total ?? ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, valor_total: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" />
                        </label>
                        <label className="text-xs font-semibold text-slate-700 md:col-span-2">
                            Observações
                            <textarea value={quoteForm.observacoes || ''} onChange={(e) => setQuoteForm((prev) => ({ ...prev, observacoes: e.target.value }))} className="mt-1 w-full px-3 py-2 rounded-lg border border-gray-300" rows={3} />
                        </label>
                        <div className="md:col-span-2 flex justify-end">
                            <button type="submit" disabled={sendingQuote} className="min-h-11 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold disabled:opacity-50">
                                {sendingQuote ? 'Enviando...' : 'Salvar cotação'}
                            </button>
                        </div>
                    </form>
                </section>

                <section className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
                    <h2 className="text-base font-bold">Upload de vouchers</h2>
                    {voucherError ? <p className="text-xs text-red-600">{voucherError}</p> : null}
                    {voucherSuccess ? <p className="text-xs text-emerald-700">{voucherSuccess}</p> : null}

                    <div className="space-y-3">
                        {voucherTypes.map((type) => (
                            <div key={type.value} className="border border-gray-200 rounded-lg p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                                <p className="text-xs font-semibold text-slate-700">{type.label}</p>
                                <label className="text-xs font-bold text-blue-700 cursor-pointer">
                                    <span className="inline-flex min-h-11 items-center px-3 py-2 rounded-lg border border-blue-200 bg-blue-50">{sendingVoucherType === type.value ? 'Enviando...' : 'Selecionar e enviar arquivo'}</span>
                                    <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden" disabled={sendingVoucherType === type.value} onChange={(event) => handleUploadVoucher(event, type.value)} />
                                </label>
                            </div>
                        ))}
                        {!voucherTypes.length ? <p className="text-xs text-slate-500">Nenhum serviço encontrado para upload de voucher.</p> : null}
                    </div>
                </section>
            </main>
        </div>
    )
}
