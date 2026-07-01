import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import IndexPage from './pages/IndexPage.jsx'
import AgenciaPage from './pages/AgenciaPage.jsx'
import PlaceholderPage from './pages/PlaceholderPage.jsx'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<IndexPage />} />
            <Route path="/setor" element={<PlaceholderPage title="Setor" description="Página em migração para React." />} />
            <Route path="/agencia" element={<AgenciaPage />} />
            <Route path="/dev" element={<PlaceholderPage title="Dev" description="Página em migração para React." />} />
            <Route path="/dashboard" element={<PlaceholderPage title="Dashboard" description="Página em migração para React." />} />
            <Route path="/aprovacao" element={<PlaceholderPage title="Aprovação" description="Página em migração para React." />} />
            <Route path="/politica-privacidade" element={<PlaceholderPage title="Política de Privacidade" description="Página em migração para React." />} />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}
