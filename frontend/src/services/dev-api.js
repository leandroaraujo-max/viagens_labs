export function createDevApi(apiClient) {
    if (!apiClient || typeof apiClient.request !== 'function') {
        throw new Error('createDevApi requer um apiClient válido com método request.')
    }

    return {
        obterStats() {
            return apiClient.request('/dev/stats')
        },
        obterAtividade(limit = 20) {
            return apiClient.request(`/dev/atividade?limit=${limit}`)
        },
        listarSolicitacoes(queryString = '') {
            const suffix = queryString ? `?${queryString}` : ''
            return apiClient.request(`/dev/solicitacoes${suffix}`)
        },
        recarregarNginx() {
            return apiClient.request('/dev/servicos/recarregar-nginx', { method: 'POST' })
        },
        reiniciarBackend() {
            return apiClient.request('/dev/servicos/reiniciar-backend', { method: 'POST' })
        },
    }
}
