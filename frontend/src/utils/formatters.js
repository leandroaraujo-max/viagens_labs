export function formatCPF(value) {
    if (!value) return '—'
    const digits = String(value).replace(/\D/g, '').padStart(11, '0')
    return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
}

export function formatHourFromIso(value) {
    if (!value) return '—'
    return String(value).slice(11, 16)
}
