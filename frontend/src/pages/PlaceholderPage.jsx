import React from 'react'
import { Link } from 'react-router-dom'

export default function PlaceholderPage({ title, description }) {
    return (
        <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
            <section className="w-full max-w-lg bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h1 className="text-xl font-bold">{title}</h1>
                <p className="text-sm text-slate-300">{description}</p>
                <Link to="/" className="inline-flex min-h-11 items-center px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold">
                    Voltar ao portal
                </Link>
            </section>
        </main>
    )
}
