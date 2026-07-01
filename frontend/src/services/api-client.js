import { createError } from './http-errors.js'

function joinUrl(baseUrl, path) {
    if (!path.startsWith('/')) return `${baseUrl}/${path}`
    return `${baseUrl}${path}`
}

/**
 * createApiClient
 * Wrapper de fetch com autenticação, parsing de JSON e tratamento de 401/403.
 *
 * @param {{ baseUrl?: string, getToken?: () => string, onUnauthorized?: () => void }} options
 */
export function createApiClient(options = {}) {
    const baseUrl = options.baseUrl || '/api/v1'
    const getToken = options.getToken || (() => '')
    const onUnauthorized = options.onUnauthorized || (() => { })

    function buildHeaders({ auth = true, json = true, extraHeaders = {} } = {}) {
        const headers = { ...extraHeaders }

        if (json && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json'
        }

        if (auth) {
            const token = getToken()
            if (token) headers.Authorization = `Bearer ${token}`
        }

        return headers
    }

    async function request(path, { method = 'GET', auth = true, json = true, body, headers = {} } = {}) {
        const response = await fetch(joinUrl(baseUrl, path), {
            method,
            headers: buildHeaders({ auth, json, extraHeaders: headers }),
            body,
        })

        let data = null
        const contentType = response.headers.get('content-type') || ''

        if (contentType.includes('application/json')) {
            data = await response.json()
        } else {
            const text = await response.text()
            data = text ? { message: text } : null
        }

        if ((response.status === 401 || response.status === 403) && auth) {
            onUnauthorized()
        }

        return { ok: response.ok, status: response.status, data }
    }

    async function requestJson(path, options) {
        const result = await request(path, options)
        if (!result.ok) {
            throw createError(result, 'Erro ao processar requisição.')
        }
        return result.data
    }

    return { buildHeaders, request, requestJson }
}
