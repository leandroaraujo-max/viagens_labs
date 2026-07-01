/**
 * API do portal do viajante (index).
 * Todas as chamadas recebem `apiClient` injetado para remover dependência global.
 */
export function createIndexApi(apiClient) {
    if (!apiClient || typeof apiClient.request !== 'function') {
        throw new Error('createIndexApi requer um apiClient válido com método request.');
    }

    return {
        // Auth e Login
        realizarLogin(payload) {
            return apiClient.request('/auth/login', {
                method: 'POST',
                auth: false,
                body: JSON.stringify(payload),
            });
        },

        // LGPD
        registrarConsentimentoLGPD(payload) {
            return apiClient.request('/lgpd/consentimento', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
        },

        // Viagens e solicitações
        listarMinhasViagens() {
            return apiClient.request('/viagens/minhas');
        },
        enviarSolicitacaoViagem(payload) {
            return apiClient.request('/viagens/solicitacoes', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
        },
        solicitarCancelamento(id, payload) {
            return apiClient.request(`/viagens/solicitacoes/${id}/solicitar-cancelamento`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
        },
        solicitarRemarcacao(id, payload) {
            return apiClient.request(`/viagens/solicitacoes/${id}/solicitar-remarcacao`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
        },
        listarMeusCreditos() {
            return apiClient.request('/viagens/creditos/meus');
        },

        // Colaboradores e perfil
        buscarColaborador(identificador) {
            return apiClient.request(`/viagens/colaborador/${identificador}`);
        },
        obterPerfilViajante(username) {
            return apiClient.request(`/viagens/perfil/${username}`);
        },
        salvarPerfilViajante(username, payload) {
            return apiClient.request(`/viagens/perfil/${username}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
        },

        // Delegação e terceiros
        listarAutorizacoesTerceiros() {
            return apiClient.request('/terceiros/minhas');
        },
        buscarTerceiroPorMatricula(matricula) {
            return apiClient.request(`/terceiros/buscar/${matricula}`);
        },
        solicitarAutorizacaoTerceiro(formData) {
            return apiClient.request('/terceiros/solicitar', {
                method: 'POST',
                json: false,
                body: formData,
            });
        },

        // Proxies e APIs externas
        buscarLugares(termo) {
            return apiClient.request(`/brasil-api/lugares?q=${encodeURIComponent(termo)}`);
        },
        listarPeriodosVoo() {
            return apiClient.request('/brasil-api/periodos-voo');
        },
    };
}
