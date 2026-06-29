(function attachValidators(globalScope) {
    function onlyDigits(value) {
        return String(value || '').replace(/\D/g, '');
    }

    function maskDateBR(rawValue) {
        const digits = onlyDigits(rawValue).slice(0, 8);
        if (digits.length >= 5) {
            return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
        }
        if (digits.length >= 3) {
            return `${digits.slice(0, 2)}/${digits.slice(2)}`;
        }
        return digits;
    }

    function parseDateBR(value) {
        if (!value || value.length < 10) return null;
        const [day, month, year] = String(value).split('/');
        if (!day || !month || !year) return null;
        return new Date(`${year}-${month}-${day}T12:00:00`);
    }

    function toISODateTime(value) {
        if (!value || value.length < 10) return null;
        const [day, month, year] = String(value).split('/');
        if (!day || !month || !year) return null;
        return `${year}-${month}-${day}T12:00:00`;
    }

    function isoToDisplay(value) {
        if (!value) return '';
        const [year, month, day] = String(value).split('-');
        if (!day || !month || !year) return '';
        return `${day}/${month}/${year}`;
    }

    function maskPhoneBR(rawValue) {
        const digits = onlyDigits(rawValue).slice(0, 11);
        if (digits.length === 0) return '';
        if (digits.length <= 2) return `(${digits}`;
        if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
        if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
        return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
    }

    globalScope.VLValidators = {
        onlyDigits,
        maskDateBR,
        parseDateBR,
        toISODateTime,
        isoToDisplay,
        maskPhoneBR,
    };
})(window);
