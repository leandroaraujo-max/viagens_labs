import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import IndexPage from './pages/IndexPage.jsx'
import AgenciaPage from './pages/AgenciaPage.jsx'
import SetorPage from './pages/SetorPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import AprovacaoPage from './pages/AprovacaoPage.jsx'
import DevPage from './pages/DevPage.jsx'
import PlaceholderPage from './pages/PlaceholderPage.jsx'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<IndexPage />} />
            <Route path="/setor" element={<SetorPage />} />
            <Route path="/agencia" element={<AgenciaPage />} />
            <Route path="/dev" element={<DevPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/aprovacao" element={<AprovacaoPage />} />
            <Route path="/politica-privacidade" element={<PlaceholderPage title="Política de Privacidade" description="Página em migração para React." />} />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}
