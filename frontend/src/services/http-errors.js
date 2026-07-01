/**
 * parseErrorMessage
 * Extrai mensagem legível de um payload de erro da API.
 */
export function parseErrorMessage(payload, fallbackMessage) {
    if (!payload) return fallbackMessage
    if (typeof payload === 'string') return payload
    if (typeof payload.detail === 'string' && payload.detail.trim()) return payload.detail
    if (typeof payload.message === 'string' && payload.message.trim()) return payload.message
    return fallbackMessage
}

/**
 * createError
 * Cria um Error com propriedades extras de status e payload HTTP.
 */
export function createError(responseLike, fallbackMessage) {
    const status = responseLike?.status || 0
    const message = parseErrorMessage(
        responseLike?.data,
        fallbackMessage || 'Erro inesperado na API.',
    )

    const error = new Error(message)
    error.name = 'HttpRequestError'
    error.status = status
    error.payload = responseLike?.data || null
    return error
}
