# Fase 4 - Validação, Testes e Deploy

**Data de Início:** 23/06/2026  
**Status Atual:** Em Progresso (Fase 4.1 - Testes Integrados)  
**Taxa de Conformidade:** 68% (13/19 testes aprovados)

---

## 📊 Resumo Executivo

A Fase 4 é responsável por validar a conformidade completa do sistema antes do deploy em produção. Atualmente, **68% das validações de teste passaram**, com foco nos testes de funcionalidade e conformidade LGPD.

| Categoria | Aprovados | Reprovados | Pendentes | Taxa |
|-----------|-----------|-----------|-----------|------|
| Funcionalidade | 6/7 | 0 | 1 | 86% |
| Segurança | 3/6 | 1 | 2 | 50% |
| Conformidade LGPD | 4/6 | 0 | 2 | 67% |
| **TOTAL** | **13/19** | **1/19** | **5/19** | **68%** |

---

## 🎯 Roadmap para 100% de Conformidade

### ✅ Testes Já Aprovados (13)

#### Funcionalidade (6/7)
- ✓ Modal de consentimento viajante (index.html)
- ✓ Modal de consentimento gestor (setor.html)
- ✓ Logs sem dados sensíveis
- ✓ Portabilidade em JSON (GET /api/v1/lgpd/meus-dados)
- ✓ Solicitação de deleção com deduplicação
- ✓ Scheduler automático a cada hora

#### Segurança (3/6)
- ✓ Auditoria LGPD implementada (tabela + middleware)
- ✓ Token TTL válido (SLA scheduler)
- ✓ Sem credenciais expostas em código

#### Conformidade LGPD (4/6)
- ✓ Política de Privacidade publicada
- ✓ Consentimento obrigatório (modal bloqueia)
- ✓ Revogar consentimento (POST /api/v1/lgpd/revogar-consentimento)
- ✓ Portabilidade de dados (GET /api/v1/lgpd/meus-dados)

---

### 🔄 Testes Pendentes (5) - Requerem Ação

#### 1. **Email com Username Correto** ⚠️
**Status:** Pendente (requer teste em produção)  
**Ação:** Executar teste de envio de e-mail real com verificação de username

```bash
# Teste manual:
1. Criar solicitação de viagem como viajante
2. Atribuir para aprovação N1 
3. Aguardar e-mail de lembrete
4. Verificar se saudação é "Oi João" e não "Oi joao.silva"
```

**Responsável:** Dev Backend + QA  
**Prazo:** Antes de deploy em produção  

---

#### 2. **HTTPS Ativo em Produção** ⚠️
**Status:** Pendente (requer ambiente produção)  
**Ação:** Validar HTTPS em servidor de produção

```bash
# Verificação:
curl -I https://viagenslabs.magazineluiza.intranet/
# Esperado: 200 OK com header "Strict-Transport-Security"
```

**Responsável:** DevOps + Segurança  
**Prazo:** Configuração pré-deploy  

---

#### 3. **Certificado SSL Válido e Atualizado** ⚠️
**Status:** Pendente (requer ambiente produção)  
**Ação:** Validar validade e renovação do certificado

```bash
# Verificação:
openssl s_client -connect viagenslabs.magazineluiza.intranet:443 -showcerts
# Verificar: Valid from / Valid until
```

**Responsável:** DevOps + Segurança  
**Prazo:** Antes de deploy (renovar se necessário)  

---

#### 4. **DPO Informado de Processamento de Dados** ⚠️
**Status:** Pendente (requer comunicação formal)  
**Ação:** Enviar documento de conformidade ao DPO

**Documentos Necessários:**
- PLANO_FASE_2_3_4.md (este plano)
- README.md (com seção LGPD)
- Relatório de Testes (tests/fase4_test_report.json)
- Descrição de base legal (Art. 7º, V LGPD - execução de contrato)

**Modelo de E-mail:**
```
Assunto: Notificação de Conformidade LGPD - Sistema Viagens Labs

Prezado(a) [DPO],

Informamos a implementação de conformidade LGPD no sistema Viagens Labs
conforme Lei 13.709/2018, incluindo:

1. Modal de consentimento obrigatório para viajantes e gestores
2. Trilha de auditoria em endpoint sensíveis
3. Solicitações de deleção com janela de 30 dias
4. Scheduler automático para processamento de exclusões
5. Endpoint de portabilidade de dados (JSON)

Base legal: Art. 7º, V LGPD (necessário para execução de contrato de trabalho)

Documentação: PLANO_FASE_2_3_4.md

Disponível para esclarecimentos.
```

**Responsável:** Legal/DPO + Dev  
**Prazo:** Antes de deploy em produção  

---

#### 5. **Política de Retenção Aprovada** ⚠️
**Status:** Bloqueado (Etapa 3.2 - aguardando jurídico)  
**Ação:** Coordenar com jurídico sobre retenção de dados

**Questões Pendentes:**
- Quanto tempo manter dados de viagem após conclusão? (Sugestão: 2 anos mínimo por lei)
- Quanto tempo manter auditoria LGPD? (Sugestão: 5 anos para conformidade)
- Quando deletar dados após solicitação? (Implementado: 30 dias + processamento automático)

**Responsável:** Jurídico/DPO  
**Prazo:** Quando Etapa 3.2 (encriptação) for destravada  

---

### ❌ Teste Reprovado (1) - Crítico

#### **Encriptação de Dados em Repouso** ✗
**Status:** Bloqueado - Etapa 3.2 (aguardando aprovação de política de retenção)  
**Impacto:** Crítico para conformidade LGPD  
**Ação:** Aguardar aprovação de política de retenção para implementar

**Requisitos quando destravado:**
1. Implementar encriptação de CPF, data de nascimento em SolicitacaoModel
2. Chave gerada via `cryptography.Fernet` em `app/core/security.py`
3. Variável de ambiente: `ENCRYPTION_KEY`
4. Migration script para encriptar dados históricos
5. Testes unitários de encrypt/decrypt

**Responsável:** Dev Backend + Jurídico/DPO  
**Prazo:** Após aprovação de política (Etapa 3.2)  

---

## 🔨 Próximos Passos

### Imediato (Esta Semana)
- [ ] **4.1.1** Executar teste de e-mail com username real (produção)
- [ ] **4.1.2** Validar HTTPS e certificado SSL em produção
- [ ] **4.1.3** Enviar notificação formal ao DPO com documentação
- [ ] Executar todos os testes unitários (pytest) novamente: `pytest tests -m "not integration"`

### Curto Prazo (Próxima Semana)
- [ ] **Fase 4.2** - Auditoria Interna: Convidar especialista em LGPD para revisar conformidade
- [ ] **Fase 4.3** - Preparar deployment: backup, variáveis de ambiente, checklist pré-deploy

### Médio Prazo (Aguardando Jurídico)
- [ ] Etapa 3.2: Implementar encriptação em repouso (após aprovação de política)
- [ ] Atualizar Fase 4.1 testes para validar encriptação

---

## 📋 Checklist de Deploy (Fase 4.3)

### Pré-Deploy (48h antes)
- [ ] Todos os testes unitários passando (`pytest tests -m "not integration"`)
- [ ] Configurar variáveis de ambiente em produção
- [ ] Realizar backup do banco de dados
- [ ] Testar migrations em ambiente de staging
- [ ] Validar e-mails com username real
- [ ] Verificar HTTPS e certificado SSL

### Deploy
- [ ] Pull da branch main
- [ ] Executar migrations
- [ ] Reiniciar backend (Uvicorn)
- [ ] Reiniciar frontend (nginx)
- [ ] Validar health check: `curl https://viagenslabs.../api/v1/health`

### Pós-Deploy (4h depois)
- [ ] Verificar logs de erro
- [ ] Testar modal de consentimento
- [ ] Testar envio de e-mail
- [ ] Testar endpoints LGPD (/api/v1/lgpd/*)
- [ ] Validar auditoria LGPD (tabela auditoria_lgpd)
- [ ] Monitorar performance do scheduler

---

## 📞 Contatos Críticos

| Papel | Contato | Assunto |
|-------|---------|---------|
| **DPO/Jurídico** | dpo@luizalabs.com | Conformidade LGPD, política retenção |
| **DevOps** | [infra@luizalabs.com] | Deploy, HTTPS, certificado SSL |
| **Dev Backend** | leandro.araujo@luizalabs.com | Implementação técnica |

---

## 📈 Métricas de Sucesso

| Métrica | Target | Status |
|---------|--------|--------|
| Taxa de Conformidade Testes | 100% | 68% ✓ em progresso |
| Testes Unitários | 100% passando | 18/18 ✓ |
| Testes de Integração | 100% passando | Pendente |
| Auditoria LGPD | Aprovada | Pendente (Fase 4.2) |
| Deploy em Produção | Go/No-Go | Aguardando Fase 4.2 |

---

## 📝 Última Atualização

- **Data:** 23/06/2026
- **Autor:** Leandro Araujo (Dev)
- **Status:** ✓ Fase 4.1 em execução
- **Próxima Review:** 24/06/2026

---

**Documento essencial para go-live. Não proceder com deploy sem atingir 100% de conformidade.**
