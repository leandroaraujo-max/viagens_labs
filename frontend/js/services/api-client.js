(function attachApiClient(globalScope) {
    function joinUrl(baseUrl, path) {
        if (!path.startsWith('/')) return `${baseUrl}/${path}`;
        return `${baseUrl}${path}`;
    }

    function create(options) {
        const baseUrl = options.baseUrl || '';
        const getToken = options.getToken || (() => '');
        const onUnauthorized = options.onUnauthorized || (() => { });

        function buildHeaders({ auth = true, json = true, extraHeaders = {} } = {}) {
            const headers = { ...extraHeaders };

            if (json && !headers['Content-Type']) {
                headers['Content-Type'] = 'application/json';
            }

            if (auth) {
                const token = getToken();
                if (token) headers.Authorization = `Bearer ${token}`;
            }

            return headers;
        }

        async function request(path, { method = 'GET', auth = true, json = true, body, headers = {} } = {}) {
            const response = await fetch(joinUrl(baseUrl, path), {
                method,
                headers: buildHeaders({ auth, json, extraHeaders: headers }),
                body,
            });

            let data = null;
            const contentType = response.headers.get('content-type') || '';

            if (contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                data = text ? { message: text } : null;
            }

            if ((response.status === 401 || response.status === 403) && auth) {
                onUnauthorized();
            }

            return {
                ok: response.ok,
                status: response.status,
                data,
            };
        }

        async function requestJson(path, options) {
            const result = await request(path, options);
            if (!result.ok) {
                throw globalScope.VLHttpErrors.createError(result, 'Erro ao processar requisição.');
            }
            return result.data;
        }

        return {
            buildHeaders,
            request,
            requestJson,
        };
    }

    globalScope.VLApiClient = {
        create,
    };
})(window);
