/**
 * API do portal do setor.
 * Remove dependência de globais e injeta apiClient explicitamente.
 */
export function createSetorApi(apiClient) {
    if (!apiClient || typeof apiClient.request !== 'function') {
        throw new Error('createSetorApi requer um apiClient válido com método request.')
    }

    const authorizationHeaders = () => apiClient.buildHeaders({ auth: true, json: false })

    return {
        // LGPD
        registrarConsentimentoLGPD(payload) {
            return apiClient.request('/lgpd/consentimento', {
                method: 'POST',
                body: JSON.stringify(payload),
            })
        },

        // Solicitações
        listarSolicitacoes(queryString) {
            return apiClient.request(`/setor/solicitacoes?${queryString}`)
        },
        obterDetalhesSolicitacao(id) {
            return apiClient.request(`/setor/solicitacoes/${id}`)
        },
        baixarPdfAssinado(url) {
            return fetch(url, {
                headers: authorizationHeaders(),
            })
        },
        decidirSolicitacao(id, payload) {
            return apiClient.request(`/setor/solicitacoes/${id}/acao`, {
                method: 'POST',
                body: JSON.stringify(payload),
            })
        },
        cancelarSolicitacao(id, payload) {
            return apiClient.request(`/setor/solicitacoes/${id}/decidir-cancelamento`, {
                method: 'POST',
                body: JSON.stringify(payload),
            })
        },

        // Casamentos
        listarCasamentos() {
            return apiClient.request('/setor/casamentos')
        },
        decidirCasamento(id, acao, payload) {
            return apiClient.request(`/setor/casamentos/${id}/${acao}`, {
                method: 'POST',
                body: JSON.stringify(payload),
            })
        },

        // Terceiros
        listarTerceiros(statusFiltro) {
            const query = statusFiltro ? `?status_filtro=${statusFiltro}` : ''
            return apiClient.request(`/terceiros/admin/todos${query}`)
        },
        decidirTerceiro(id, formData) {
            return apiClient.request(`/terceiros/admin/${id}/decisao`, {
                method: 'PATCH',
                json: false,
                body: formData,
            })
        },

        // Proxies
        buscarCnpj(cnpj) {
            return apiClient.request(`/setor/proxy/cnpj/${cnpj}`)
        },
        buscarCep(cep) {
            return apiClient.request(`/setor/proxy/cep/${cep}`)
        },
        buscarBanco(codigo) {
            return apiClient.request(`/setor/proxy/bank/${codigo}`)
        },

        // Agências
        listarAgencias() {
            return apiClient.request('/setor/agencias')
        },
        salvarAgencia(url, method, payload) {
            return apiClient.request(url, {
                method,
                body: JSON.stringify(payload),
            })
        },
        excluirAgencia(id) {
            return apiClient.request(`/setor/agencias/${id}`, { method: 'DELETE' })
        },
        alternarStatusAgencia(id, payload) {
            return apiClient.request(`/setor/agencias/${id}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            })
        },

        // Dashboard / stats
        obterStats() {
            return apiClient.request('/setor/stats')
        },
        obterAlertasAcesso() {
            return apiClient.request('/setor/alertas-acesso')
        },
    }
}
