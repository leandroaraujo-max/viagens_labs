import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'portal-viajante',
        component: () => import('../pages/IndexPage.vue'),
    },
    {
        path: '/setor',
        name: 'setor',
        component: () => import('../pages/SetorPage.vue'),
    },
    {
        path: '/agencia',
        name: 'agencia',
        component: () => import('../pages/AgenciaPage.vue'),
    },
    {
        path: '/dev',
        name: 'dev',
        component: () => import('../pages/DevPage.vue'),
    },
    {
        path: '/dashboard',
        name: 'dashboard',
        component: () => import('../pages/DashboardPage.vue'),
    },
    {
        path: '/aprovacao',
        name: 'aprovacao',
        component: () => import('../pages/AprovaPage.vue'),
    },
    {
        path: '/politica-privacidade',
        name: 'politica-privacidade',
        component: () => import('../pages/PoliticaPrivacidadePage.vue'),
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
