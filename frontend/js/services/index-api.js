/**
 * VLIndexApi
 * Centraliza e abstrai todas as chamadas de API feitas no portal do viajante (index.html).
 */
(function (global) {
    class VLIndexApi {
        constructor(apiClient) {
            this.apiClient = apiClient;
        }

        // ==========================================
        // Auth e Login
        // ==========================================
        realizarLogin(payload) {
            return this.apiClient.request('/auth/login', {
                method: 'POST',
                auth: false,
                body: JSON.stringify(payload)
            });
        }

        // ==========================================
        // LGPD
        // ==========================================
        registrarConsentimentoLGPD(payload) {
            return this.apiClient.request('/lgpd/consentimento', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }

        // ==========================================
        // Viagens e Solicitações
        // ==========================================
        listarMinhasViagens() {
            return this.apiClient.request('/viagens/minhas');
        }

        enviarSolicitacaoViagem(payload) {
            return this.apiClient.request('/viagens/solicitacoes', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }

        solicitarCancelamento(id, payload) {
            return this.apiClient.request(`/viagens/solicitacoes/${id}/solicitar-cancelamento`, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }

        solicitarRemarcacao(id, payload) {
            return this.apiClient.request(`/viagens/solicitacoes/${id}/solicitar-remarcacao`, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }

        listarMeusCreditos() {
            return this.apiClient.request('/viagens/creditos/meus');
        }

        // ==========================================
        // Colaboradores e Perfil
        // ==========================================
        buscarColaborador(identificador) {
            return this.apiClient.request(`/viagens/colaborador/${identificador}`);
        }

        obterPerfilViajante(username) {
            return this.apiClient.request(`/viagens/perfil/${username}`);
        }

        salvarPerfilViajante(username, payload) {
            return this.apiClient.request(`/viagens/perfil/${username}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
        }

        // ==========================================
        // Delegação e Terceiros
        // ==========================================
        listarAutorizacoesTerceiros() {
            return this.apiClient.request('/terceiros/minhas');
        }

        buscarTerceiroPorMatricula(matricula) {
            return this.apiClient.request(`/terceiros/buscar/${matricula}`);
        }

        solicitarAutorizacaoTerceiro(formData) {
            return this.apiClient.request('/terceiros/solicitar', {
                method: 'POST',
                json: false,
                body: formData
            });
        }

        // ==========================================
        // Proxies e APIs Externas (Brasil API)
        // ==========================================
        buscarLugares(termo) {
            return this.apiClient.request(`/brasil-api/lugares?q=${encodeURIComponent(termo)}`);
        }

        listarPeriodosVoo() {
            return this.apiClient.request('/brasil-api/periodos-voo');
        }

        // ==========================================
        // Factory
        // ==========================================
        static create(apiClient) {
            if (!apiClient) {
                throw new Error("VLIndexApi requer uma instância válida de VLApiClient.");
            }
            return new VLIndexApi(apiClient);
        }
    }

    // Exporta a classe no escopo global
    global.VLIndexApi = VLIndexApi;
})(window);
