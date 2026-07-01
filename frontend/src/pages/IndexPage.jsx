import React, { useEffect, useMemo, useState } from 'react'
import { createApiClient } from '../services/api-client.js'
import { createIndexApi } from '../services/index-api.js'
import { parseErrorMessage } from '../services/http-errors.js'
import { formatCPF } from '../utils/formatters.js'
import { maskDateBR, maskPhoneBR } from '../utils/validators.js'
import LgpdConsentModal from '../composables/Modal/LgpdConsentModal.jsx'
import CancelTravelModal from '../composables/Modal/CancelTravelModal.jsx'
import RescheduleTravelModal from '../composables/Modal/RescheduleTravelModal.jsx'

const LGPD_ACCEPT_KEY = 'lgpd_aceito'
const LGPD_ACCEPT_DATE_KEY = 'lgpd_data_aceito'

export default function IndexPage() {
    const [token, setToken] = useState(localStorage.getItem('token') || '')
    const [nomeUsuario, setNomeUsuario] = useState(localStorage.getItem('nome_usuario') || '')
    const [perfilUsuario, setPerfilUsuario] = useState(localStorage.getItem('perfil') || 'viajante')
    const [loginForm, setLoginForm] = useState({ username: '', password: '' })
    const [carregando, setCarregando] = useState(false)
    const [erroLogin, setErroLogin] = useState('')
    const [semAcessoAd, setSemAcessoAd] = useState(false)

    const [abaAtiva, setAbaAtiva] = useState('nova_solicitacao')
    const [cpfBusca, setCpfBusca] = useState('')
    const [viajanteDados, setViajanteDados] = useState(null)
    const [buscandoColaborador, setBuscandoColaborador] = useState(false)
    const [erroBusca, setErroBusca] = useState('')

    const [celularViajante, setCelularViajante] = useState('')
    const [dataNascimentoViajante, setDataNascimentoViajante] = useState('')
    const [erroEnvio, setErroEnvio] = useState('')

    const [historico, setHistorico] = useState([])
    const [historicoCarregando, setHistoricoCarregando] = useState(false)
    const [meusCreditos, setMeusCreditos] = useState([])

    const [viagemACancelar, setViagemACancelar] = useState(null)
    const [viagemARemarcar, setViagemARemarcar] = useState(null)
    const [enviandoCancelar, setEnviandoCancelar] = useState(false)
    const [enviandoRemarcar, setEnviandoRemarcar] = useState(false)

    const [mostrandoModalLGPD, setMostrandoModalLGPD] = useState(false)
    const [registrandoConsentimento, setRegistrandoConsentimento] = useState(false)
    const [erroConsentimento, setErroConsentimento] = useState('')

    const isAuthenticated = Boolean(token)

    const apiClient = useMemo(() => {
        return createApiClient({
            baseUrl: '/api/v1',
            getToken: () => token,
            onUnauthorized: () => logout(),
        })
    }, [token])

    const indexApi = useMemo(() => createIndexApi(apiClient), [apiClient])

    async function realizarLogin(event) {
        event.preventDefault()
        setErroLogin('')
        setSemAcessoAd(false)
        setCarregando(true)

        try {
            const response = await indexApi.realizarLogin({
                username: loginForm.username,
                password: loginForm.password,
                agencia: null,
            })

            if (response.status === 403) {
                setSemAcessoAd(true)
            }

            if (!response.ok) {
                throw new Error(parseErrorMessage(response.data, 'Falha ao autenticar.'))
            }

            const data = response.data || {}
            localStorage.setItem('token', data.access_token || '')
            localStorage.setItem('nome_usuario', data.nome_usuario || '')
            localStorage.setItem('perfil', data.perfil || 'viajante')
            localStorage.setItem('username_ad', data.username || '')

            setToken(data.access_token || '')
            setNomeUsuario(data.nome_usuario || '')
            setPerfilUsuario(data.perfil || 'viajante')
            setLoginForm((prev) => ({ ...prev, password: '' }))
        } catch (error) {
            setErroLogin(error.message || 'Erro inesperado no login.')
        } finally {
            setCarregando(false)
        }
    }

    function logout() {
        const lgpdAceito = localStorage.getItem(LGPD_ACCEPT_KEY)
        const lgpdData = localStorage.getItem(LGPD_ACCEPT_DATE_KEY)

        localStorage.removeItem('token')
        localStorage.removeItem('nome_usuario')
        localStorage.removeItem('perfil')
        localStorage.removeItem('username_ad')

        if (lgpdAceito) localStorage.setItem(LGPD_ACCEPT_KEY, lgpdAceito)
        if (lgpdData) localStorage.setItem(LGPD_ACCEPT_DATE_KEY, lgpdData)

        setToken('')
        setNomeUsuario('')
        setPerfilUsuario('viajante')
        setMostrandoModalLGPD(false)
    }

    async function buscarColaborador() {
        if (!cpfBusca.trim()) {
            setErroBusca('Informe CPF ou matrícula para buscar.')
            return
        }

        setBuscandoColaborador(true)
        setErroBusca('')
        try {
            const response = await indexApi.buscarColaborador(cpfBusca.trim())
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Colaborador não encontrado.'))
            const data = response.data
            setViajanteDados(data?.dados || data)
        } catch (error) {
            setErroBusca(error.message || 'Erro ao buscar colaborador.')
            setViajanteDados(null)
        } finally {
            setBuscandoColaborador(false)
        }
    }

    async function carregarHistorico() {
        if (!isAuthenticated) return
        setHistoricoCarregando(true)
        try {
            const response = await indexApi.listarMinhasViagens()
            setHistorico(response.ok && Array.isArray(response.data) ? response.data : [])
        } finally {
            setHistoricoCarregando(false)
        }
    }

    async function carregarMeusCreditos() {
        if (!isAuthenticated) return
        const response = await indexApi.listarMeusCreditos()
        setMeusCreditos(response.ok && Array.isArray(response.data) ? response.data : [])
    }

    async function aceitarConsentimentoLGPD() {
        setRegistrandoConsentimento(true)
        setErroConsentimento('')
        try {
            const response = await indexApi.registrarConsentimentoLGPD({ aceito: true, versao_politica: '1.0' })
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Erro ao registrar consentimento.'))
            const hoje = new Date().toISOString().split('T')[0]
            localStorage.setItem(LGPD_ACCEPT_KEY, 'true')
            localStorage.setItem(LGPD_ACCEPT_DATE_KEY, hoje)
            setMostrandoModalLGPD(false)
        } catch (error) {
            setErroConsentimento(error.message || 'Erro ao registrar consentimento.')
        } finally {
            setRegistrandoConsentimento(false)
        }
    }

    async function confirmarCancelarViagem(payload) {
        if (!viagemACancelar?.id) return
        setEnviandoCancelar(true)
        try {
            const response = await indexApi.solicitarCancelamento(viagemACancelar.id, {
                itens_a_cancelar: payload.itens.join(','),
                motivo_cancelamento: payload.motivo,
            })
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Não foi possível cancelar.'))
            setViagemACancelar(null)
            await carregarHistorico()
            await carregarMeusCreditos()
        } catch (error) {
            setErroEnvio(error.message || 'Erro no cancelamento.')
        } finally {
            setEnviandoCancelar(false)
        }
    }

    async function confirmarRemarcarViagem(payload) {
        if (!viagemARemarcar?.id) return
        setEnviandoRemarcar(true)
        try {
            const response = await indexApi.solicitarRemarcacao(viagemARemarcar.id, {
                data_ida: payload.data_ida,
                data_volta: payload.data_volta || null,
                motivo_cancelamento: payload.motivo,
            })
            if (!response.ok) throw new Error(parseErrorMessage(response.data, 'Não foi possível remarcar.'))
            setViagemARemarcar(null)
            await carregarHistorico()
        } catch (error) {
            setErroEnvio(error.message || 'Erro na remarcação.')
        } finally {
            setEnviandoRemarcar(false)
        }
    }

    useEffect(() => {
        if (!isAuthenticated) return
        const aceito = localStorage.getItem(LGPD_ACCEPT_KEY)
        const data = localStorage.getItem(LGPD_ACCEPT_DATE_KEY)
        const hoje = new Date().toISOString().split('T')[0]
        setMostrandoModalLGPD(!(aceito && data === hoje))
        void carregarHistorico()
        void carregarMeusCreditos()
    }, [isAuthenticated])

    if (!isAuthenticated) {
        return (
            <main className="bg-viagens min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] pointerEvents-none" />
                <div className="vl-shell-dark-card transition-all duration-300" role="region" aria-label="Login do portal de viagens">
                    <header className="text-center mb-8 mt-2 flex flex-col items-center select-none">
                        <span className="text-[11px] font-mono text-blue-400 block tracking-widest leading-none uppercase font-bold mt-1">Viagens</span>
                    </header>

                    {erroLogin && !semAcessoAd ? <p className="mb-5 p-4 bg-red-950/40 border-l-4 border-red-500 text-red-200 text-xs rounded-xl">{erroLogin}</p> : null}
                    {semAcessoAd ? <p className="mb-5 p-4 bg-amber-950/40 border-l-4 border-amber-500 text-amber-200 text-xs rounded-xl">Você não possui acesso ao sistema.</p> : null}

                    <form className="space-y-5" onSubmit={realizarLogin}>
                        <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2" htmlFor="username">Usuário de Rede (AD)</label>
                        <input id="username" value={loginForm.username} onChange={(e) => setLoginForm((prev) => ({ ...prev, username: e.target.value }))} className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-slate-950 text-white" required />

                        <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2" htmlFor="password">Senha Corporativa</label>
                        <input id="password" type="password" value={loginForm.password} onChange={(e) => setLoginForm((prev) => ({ ...prev, password: e.target.value }))} className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-slate-950 text-white" required />

                        <button type="submit" disabled={carregando} className="w-full min-h-11 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 px-4 rounded-xl disabled:opacity-75">
                            {carregando ? 'Autenticando...' : 'Entrar'}
                        </button>
                    </form>
                </div>
            </main>
        )
    }

    return (
        <div className="min-h-screen bg-[#f8fafc] text-slate-800">
            <header className="bg-white border-b border-gray-200/80 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
                <h1 className="text-sm font-bold text-gray-800">Portal do Viajante (React)</h1>
                <button type="button" className="vl-btn-logout" onClick={logout}>Sair</button>
            </header>

            <main className="w-full p-6 space-y-6">
                <section className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
                    <h2 className="text-sm font-bold text-slate-800">Identificar viajante</h2>
                    <div className="flex gap-2">
                        <label htmlFor="busca-viajante" className="sr-only">CPF ou matrícula</label>
                        <input id="busca-viajante" value={cpfBusca} onChange={(e) => setCpfBusca(e.target.value)} className="flex-1 px-3 py-2 rounded-lg border border-gray-300" placeholder="CPF ou matrícula" />
                        <button type="button" onClick={buscarColaborador} disabled={buscandoColaborador} className="min-h-11 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg">
                            {buscandoColaborador ? 'Buscando...' : 'Buscar'}
                        </button>
                    </div>
                    {erroBusca ? <p className="text-xs text-red-600">{erroBusca}</p> : null}
                    {viajanteDados ? (
                        <p className="text-xs text-gray-700">
                            Viajante: <strong>{viajanteDados.nome || '—'}</strong> · CPF: <strong>{formatCPF(viajanteDados.cpf)}</strong>
                        </p>
                    ) : null}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <label htmlFor="celular-viajante" className="sr-only">Celular</label>
                        <input id="celular-viajante" value={celularViajante} onChange={(e) => setCelularViajante(maskPhoneBR(e.target.value))} className="px-3 py-2 rounded-lg border border-gray-300" placeholder="Celular" />
                        <label htmlFor="data-nascimento-viajante" className="sr-only">Data de nascimento</label>
                        <input id="data-nascimento-viajante" value={dataNascimentoViajante} onChange={(e) => setDataNascimentoViajante(maskDateBR(e.target.value))} className="px-3 py-2 rounded-lg border border-gray-300" placeholder="Data de nascimento" />
                    </div>
                </section>

                <nav className="flex gap-2 flex-wrap">
                    <button type="button" aria-pressed={abaAtiva === 'minhas_viagens'} onClick={() => setAbaAtiva('minhas_viagens')} className="px-3 py-2 rounded-lg border border-gray-300 text-xs font-semibold">Minhas viagens</button>
                    <button type="button" aria-pressed={abaAtiva === 'gestao_creditos'} onClick={() => setAbaAtiva('gestao_creditos')} className="px-3 py-2 rounded-lg border border-gray-300 text-xs font-semibold">Créditos</button>
                </nav>

                {erroEnvio ? <p className="text-xs text-red-600">{erroEnvio}</p> : null}

                {abaAtiva === 'minhas_viagens' ? (
                    <section className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
                        <h2 className="text-sm font-bold text-slate-800">Minhas viagens</h2>
                        {historicoCarregando ? <p className="text-xs text-gray-500">Carregando...</p> : null}
                        <div className="space-y-2">
                            {historico.map((item) => (
                                <article key={item.id} className="border border-gray-200 rounded-lg p-3 space-y-2">
                                    <p className="text-xs text-gray-700">#{item.protocolo} · {item.destino_cidade}</p>
                                    <div className="flex gap-2">
                                        <button type="button" className="px-2 py-1 text-[11px] font-bold bg-red-50 text-red-600 border border-red-200 rounded" onClick={() => setViagemACancelar(item)}>Cancelar</button>
                                        <button type="button" className="px-2 py-1 text-[11px] font-bold bg-blue-50 text-blue-600 border border-blue-200 rounded" onClick={() => setViagemARemarcar(item)}>Remarcar</button>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </section>
                ) : null}

                {abaAtiva === 'gestao_creditos' ? (
                    <section className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
                        <h2 className="text-sm font-bold text-slate-800">Gestão de créditos</h2>
                        <ul className="space-y-2">
                            {meusCreditos.map((credito, idx) => (
                                <li key={credito.id || idx} className="p-3 rounded-lg border border-gray-200 text-xs">
                                    <strong>{credito.origem || credito.companhia || 'Crédito'}</strong> — {credito.valor || credito.saldo || '—'}
                                </li>
                            ))}
                        </ul>
                    </section>
                ) : null}
            </main>

            <LgpdConsentModal isOpen={mostrandoModalLGPD} loading={registrandoConsentimento} errorMessage={erroConsentimento} onAccept={aceitarConsentimentoLGPD} onReject={logout} />
            <CancelTravelModal isOpen={Boolean(viagemACancelar)} loading={enviandoCancelar} trip={viagemACancelar} onClose={() => setViagemACancelar(null)} onSubmit={confirmarCancelarViagem} />
            <RescheduleTravelModal isOpen={Boolean(viagemARemarcar)} loading={enviandoRemarcar} trip={viagemARemarcar} onClose={() => setViagemARemarcar(null)} onSubmit={confirmarRemarcarViagem} />
        </div>
    )
}
