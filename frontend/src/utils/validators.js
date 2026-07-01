function onlyDigits(value) {
    return String(value || '').replace(/\D/g, '')
}

export function maskDateBR(rawValue) {
    const digits = onlyDigits(rawValue).slice(0, 8)
    if (digits.length >= 5) return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`
    if (digits.length >= 3) return `${digits.slice(0, 2)}/${digits.slice(2)}`
    return digits
}

export function parseDateBR(value) {
    if (!value || value.length < 10) return null
    const [day, month, year] = String(value).split('/')
    if (!day || !month || !year) return null
    return new Date(`${year}-${month}-${day}T12:00:00`)
}

export function toISODateTime(value) {
    if (!value || value.length < 10) return null
    const [day, month, year] = String(value).split('/')
    if (!day || !month || !year) return null
    return `${year}-${month}-${day}T12:00:00`
}

export function isoToDisplay(value) {
    if (!value) return ''
    const [year, month, day] = String(value).split('-')
    if (!day || !month || !year) return ''
    return `${day}/${month}/${year}`
}

export function maskPhoneBR(rawValue) {
    const digits = onlyDigits(rawValue).slice(0, 11)
    if (digits.length === 0) return ''
    if (digits.length <= 2) return `(${digits}`
    if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
    if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

export { onlyDigits }
