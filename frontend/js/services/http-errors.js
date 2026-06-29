(function attachHttpErrors(globalScope) {
    function parseErrorMessage(payload, fallbackMessage) {
        if (!payload) return fallbackMessage;
        if (typeof payload === 'string') return payload;
        if (typeof payload.detail === 'string' && payload.detail.trim()) return payload.detail;
        if (typeof payload.message === 'string' && payload.message.trim()) return payload.message;
        return fallbackMessage;
    }

    function createError(responseLike, fallbackMessage) {
        const status = responseLike?.status || 0;
        const message = parseErrorMessage(responseLike?.data, fallbackMessage || 'Erro inesperado na API.');

        const error = new Error(message);
        error.name = 'HttpRequestError';
        error.status = status;
        error.payload = responseLike?.data || null;
        return error;
    }

    globalScope.VLHttpErrors = {
        parseErrorMessage,
        createError,
    };
})(window);
