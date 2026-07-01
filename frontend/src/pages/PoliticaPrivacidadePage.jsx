import React from 'react'

const sections = [
    {
        title: '1. Controlador de Dados',
        body: [
            'Empresa: Magazine Luiza S.A. (Luizalabs).',
            'Contato DPO: dpo@luizalabs.com.',
            'Esta política descreve como seus dados são utilizados no Viagens Labs.',
        ],
    },
    {
        title: '2. Dados Pessoais Coletados',
        body: [
            'Dados de identificação: nome, CPF, data de nascimento e e-mail corporativo.',
            'Dados profissionais: usuário AD, cargo, centro de custo e informações de vínculo.',
            'Dados de viagem: origem, destino, datas, serviços e motivo.',
            'Dados de auditoria: IP, timestamps e trilhas de aprovação.',
        ],
    },
    {
        title: '3. Base Legal',
        body: [
            'Execução de contrato e obrigações legais para o processo de viagens corporativas.',
            'Consentimento quando aplicável para funcionalidades específicas.',
            'Legítimo interesse para segurança, conformidade e melhoria contínua do sistema.',
        ],
    },
    {
        title: '4. Finalidades do Tratamento',
        body: [
            'Criar, gerenciar e acompanhar solicitações de viagem.',
            'Permitir aprovações N1/N2 e comunicação com agências parceiras.',
            'Processar cotações, vouchers, auditorias e indicadores operacionais.',
        ],
    },
    {
        title: '5. Compartilhamento de Dados',
        body: [
            'Gestores aprovadores e setor de viagens.',
            'Agências parceiras credenciadas no processo de cotação.',
            'Sistemas integrados corporativos (ex.: autenticação e auditoria).',
        ],
    },
    {
        title: '6. Retenção e Segurança',
        body: [
            'Os dados são mantidos pelo período necessário às finalidades e exigências legais.',
            'São aplicadas medidas técnicas e organizacionais de segurança.',
            'Após o prazo legal, dados são anonimizados ou removidos conforme política interna.',
        ],
    },
    {
        title: '7. Direitos do Titular',
        body: [
            'Você pode solicitar acesso, correção, portabilidade e exclusão quando cabível.',
            'Também pode revogar consentimentos que não estejam vinculados a obrigação legal.',
            'Solicitações: dpo@luizalabs.com.',
        ],
    },
]

export default function PoliticaPrivacidadePage() {
    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-10 px-4">
            <section className="max-w-4xl mx-auto bg-white rounded-2xl border border-slate-200 shadow-lg p-6 md:p-10 space-y-8">
                <header className="border-b border-slate-200 pb-6">
                    <h1 className="text-2xl md:text-3xl font-bold text-slate-900">🔐 Política de Privacidade</h1>
                    <p className="text-slate-600 mt-2">Viagens Labs — Portal Corporativo de Viagens</p>
                    <p className="text-xs text-slate-500 mt-2">Última atualização: 23 de junho de 2026</p>
                </header>

                {sections.map((section) => (
                    <article key={section.title} className="space-y-3">
                        <h2 className="text-xl font-bold text-slate-900">{section.title}</h2>
                        <ul className="space-y-2">
                            {section.body.map((item) => (
                                <li key={item} className="text-sm text-slate-700 leading-relaxed flex gap-2">
                                    <span className="text-blue-600 font-bold" aria-hidden="true">•</span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </article>
                ))}

                <footer className="pt-4 border-t border-slate-200 text-xs text-slate-500">
                    Dúvidas ou solicitações relacionadas à LGPD: <a href="mailto:dpo@luizalabs.com" className="text-blue-600 hover:underline">dpo@luizalabs.com</a>
                </footer>
            </section>
        </main>
    )
}
