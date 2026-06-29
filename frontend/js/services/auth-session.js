(function attachAuthSession(globalScope) {
    const STORAGE = globalScope.localStorage;

    function createNamespace(namespace) {
        const prefix = `${namespace}_`;

        function get(key) {
            return STORAGE.getItem(`${prefix}${key}`) || '';
        }

        function set(key, value) {
            if (!value) {
                STORAGE.removeItem(`${prefix}${key}`);
                return;
            }
            STORAGE.setItem(`${prefix}${key}`, value);
        }

        function remove(key) {
            STORAGE.removeItem(`${prefix}${key}`);
        }

        function clearAll() {
            remove('token');
            remove('nome');
        }

        return {
            get,
            set,
            remove,
            clearAll,
            getToken: () => get('token'),
            setToken: (token) => set('token', token),
            getNome: () => get('nome'),
            setNome: (nome) => set('nome', nome),
        };
    }

    globalScope.VLAuthSession = {
        createNamespace,
    };
})(window);
