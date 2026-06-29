/**
 * Módulo de API para o portal do Setor (Fase 2)
 * Encapsula todas as chamadas de rede do painel administrativo.
 */
window.VLSetorApi = {
    create: function (apiClient) {
        return {
            // ==========================================
            // LGPD
            // ==========================================
            registrarConsentimentoLGPD: (payload) => 
                apiClient.request('/lgpd/consentimento', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                }),

            // ==========================================
            // SOLICITAÇÕES
            // ==========================================
            listarSolicitacoes: (queryString) => 
                apiClient.request(`/setor/solicitacoes?${queryString}`),

            obterDetalhesSolicitacao: (id) => 
                apiClient.request(`/setor/solicitacoes/${id}`),

            baixarPdfAssinado: (url) => 
                fetch(url, {
                    headers: { 'Authorization': `Bearer ${apiClient.getToken()}` }
                }),

            decidirSolicitacao: (id, payload) => 
                apiClient.request(`/setor/solicitacoes/${id}/acao`, {
                    method: 'POST',
                    body: JSON.stringify(payload)
                }),

            cancelarSolicitacao: (id, payload) => 
                apiClient.request(`/setor/solicitacoes/${id}/decidir-cancelamento`, {
                    method: 'POST',
                    body: JSON.stringify(payload)
                }),

            // ==========================================
            // CASAMENTOS / AGRUPAMENTOS
            // ==========================================
            listarCasamentos: () => 
                apiClient.request('/setor/casamentos'),

            decidirCasamento: (id, acao, payload) => 
                apiClient.request(`/setor/casamentos/${id}/${acao}`, {
                    method: 'POST',
                    body: JSON.stringify(payload)
                }),

            // ==========================================
            // TERCEIROS / DELEGAÇÕES
            // ==========================================
            listarTerceiros: (statusFiltro) => {
                const query = statusFiltro ? `?status_filtro=${statusFiltro}` : '';
                return apiClient.request(`/terceiros/admin/todos${query}`);
            },

            decidirTerceiro: (id, formData) => 
                apiClient.request(`/terceiros/admin/${id}/decisao`, {
                    method: 'PATCH',
                    json: false,
                    body: formData
                }),

            // ==========================================
            // PROXIES
            // ==========================================
            buscarCnpj: (cnpj) => 
                apiClient.request(`/setor/proxy/cnpj/${cnpj}`),

            buscarCep: (cep) => 
                apiClient.request(`/setor/proxy/cep/${cep}`),

            buscarBanco: (cod) => 
                apiClient.request(`/setor/proxy/bank/${cod}`),

            // ==========================================
            // AGÊNCIAS
            // ==========================================
            listarAgencias: () => 
                apiClient.request('/setor/agencias'),

            salvarAgencia: (url, method, payload) => 
                apiClient.request(url, {
                    method: method,
                    body: JSON.stringify(payload)
                }),

            excluirAgencia: (id) => 
                apiClient.request(`/setor/agencias/${id}`, {
                    method: 'DELETE'
                }),

            alternarStatusAgencia: (id, payload) => 
                apiClient.request(`/setor/agencias/${id}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                }),

            // ==========================================
            // DASHBOARD / STATS
            // ==========================================
            obterStats: () => 
                apiClient.request('/setor/stats'),

            obterAlertasAcesso: () => 
                apiClient.request('/setor/alertas-acesso')
        };
    }
};
