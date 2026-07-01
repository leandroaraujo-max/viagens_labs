export function createAgenciaApi(apiClient) {
    if (!apiClient || typeof apiClient.request !== 'function') {
        throw new Error('createAgenciaApi requer um apiClient válido com método request.')
    }

    return {
        obterSolicitacaoPorToken(uuid) {
            return apiClient.request(`/agencia/token/${uuid}`, { auth: false })
        },

        enviarCotacaoPorToken(uuid, payload) {
            return apiClient.request(`/agencia/token/${uuid}/cotacao`, {
                method: 'POST',
                auth: false,
                body: JSON.stringify(payload),
            })
        },

        enviarVoucherPorToken(uuid, tipoVoucher, arquivo) {
            const formData = new FormData()
            formData.append('tipo_voucher', tipoVoucher)
            formData.append('arquivo', arquivo)

            return apiClient.request(`/agencia/token/${uuid}/voucher`, {
                method: 'POST',
                auth: false,
                json: false,
                body: formData,
            })
        },
    }
}
