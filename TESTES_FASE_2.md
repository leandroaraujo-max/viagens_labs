# Testes Fase 2 — Checklist de Validação

**Data de Criação:** 24/06/2026  
**Status:** Pronto para Validação Manual  
**Responsável:** Equipe QA / Desenvolvedor

---

## 📋 Testes 2.4.1 — Modal LGPD

### Teste 2.4.1.1 — Primeiro Login
1. Abrir `http://localhost/index.html`
2. Fazer login com usuário corporativo (AD)
3. **Esperado:** Modal LGPD aparece com 4 seções:
   - Header: "Consentimento para Processamento de Dados"
   - Explicação: "Coletamos dados para..."
   - Botão "Rejeitar e Sair"
   - Botão "✓ Aceitar e Continuar"

**Status:** ⏳ Pendente Validação Manual

### Teste 2.4.1.2 — localStorage Funcional
1. Após aceitar modal, abrir DevTools (F12)
2. Console → Verificar:
   ```javascript
   localStorage.getItem('lgpd_aceito')      // Esperado: "true"
   localStorage.getItem('lgpd_data_aceito') // Esperado: "2026-06-24" (data de hoje)
   ```
3. **Esperado:** Ambas as chaves existem com valores corretos

**Status:** ⏳ Pendente Validação Manual

### Teste 2.4.1.3 — Bloqueio Mesmo Dia
1. Com localStorage já preenchido, fazer logout
2. Fazer login novamente (MESMO DIA)
3. **Esperado:** Modal LGPD NÃO aparece (localStorage bloqueia)
4. Dashboard carrega normalmente

**Status:** ⏳ Pendente Validação Manual

### Teste 2.4.1.4 — Reset Dia Seguinte
1. Abrir DevTools (F12)
2. Console:
   ```javascript
   localStorage.setItem('lgpd_data_aceito', '2026-06-23')  // Data anterior
   ```
3. Fazer logout e login
4. **Esperado:** Modal LGPD reaparece (data anterior dispara novo consentimento)
5. Clicar "Aceitar"
6. localStorage é atualizado para data de hoje

**Status:** ⏳ Pendente Validação Manual

---

## 🔗 Testes 2.4.2 — Endpoints LGPD

### Teste 2.4.2.1 — POST /api/v1/lgpd/consentimento

**Pré-requisito:** Obter JWT token válido do login

```bash
# Comando
curl -X POST http://localhost:8000/api/v1/lgpd/consentimento \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"aceito": true, "versao_politica": "1.0"}'

# Esperado (200 OK):
# {"id": 1, "usuario_id": "lnd_araujo", "aceito": true, "data_aceito": "2026-06-24T..."}
```

**Status:** ⏳ Pendente Validação

### Teste 2.4.2.2 — GET /api/v1/lgpd/meus-dados

**Pré-requisito:** Estar logado

```bash
# Comando
curl -X GET http://localhost:8000/api/v1/lgpd/meus-dados \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Esperado (200 OK):
# {
#   "usuario_id": "lnd_araujo",
#   "viagens": [...],
#   "aprovacoes": [...],
#   "consentimentos": [...]
# }
```

**Status:** ⏳ Pendente Validação

### Teste 2.4.2.3 — POST /api/v1/lgpd/revogar-consentimento

```bash
# Comando
curl -X POST http://localhost:8000/api/v1/lgpd/revogar-consentimento \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Esperado (200 OK):
# {"mensagem": "Consentimento revogado com sucesso"}
```

**Status:** ⏳ Pendente Validação

---

## 📄 Testes 2.4.3 — Página de Política de Privacidade

### Teste 2.4.3.1 — Página Carrega Corretamente
1. Abrir `http://localhost/politica-privacidade.html` (ou click no link footer)
2. **Esperado:** Página carrega sem erros com 10 seções visíveis:
   - ✓ 1. Controlador de Dados
   - ✓ 2. Dados Coletados
   - ✓ 3. Base Legal
   - ✓ 4. Fins do Processamento
   - ✓ 5. Destinatários
   - ✓ 6. Retenção de Dados
   - ✓ 7. Seus Direitos LGPD
   - ✓ 8. Segurança
   - ✓ 9. Processadores de Dados
   - ✓ 10. Alterações da Política

**Status:** ⏳ Pendente Validação Manual

### Teste 2.4.3.2 — Links Funcionais
1. Na política, localizar links:
   - Link para Google (BigQuery): Deve abrir em nova aba
   - Link para Microsoft (Azure AD): Deve abrir em nova aba
   - Email DPO (dpo@luizalabs.com): Deve abrir cliente de e-mail
   - "Voltar ao Portal": Deve retornar para index.html

2. **Esperado:** Todos os links funcionam sem erros

**Status:** ⏳ Pendente Validação Manual

### Teste 2.4.3.3 — Link Footer Funciona
1. Em index.html ou setor.html, localizar footer com link "Política de Privacidade"
2. Clicar no link
3. **Esperado:** Abre `politica-privacidade.html` em nova aba

**Status:** ⏳ Pendente Validação Manual

---

## 📧 Testes 2.4.4 — E-mails com Username

### Teste 2.4.4.1 — Verificação de Saudação
1. Criar nova solicitação de viagem como colaborador
2. Sistema envia e-mail de confirmação
3. **Esperado:** E-mail contém saudação:
   ```
   Olá, lnd_araujo,
   
   Sua solicitação foi criada com sucesso...
   ```
   (Username em vez de nome completo)

4. **Verificação:** Todos os 6 tipos de e-mail usam username:
   - ✓ Solicitação criada
   - ✓ Resultado de aprovação
   - ✓ Cotação recebida
   - ✓ Voucher criado
   - ✓ Conclusão de viagem
   - ✓ Cotação concluída

**Status:** ✅ VERIFICADO NA IMPLEMENTAÇÃO (Fase 2.1 - 100% completo)

---

## 🗄️ Verificação de Banco de Dados

### Tabela lgpd_consentimento
Após restart do FastAPI, a tabela deve ser criada automaticamente:

```sql
-- Verificação no PostgreSQL
SELECT * FROM lgpd_consentimento;

-- Esperado: Coluna criada com schema:
-- id (int, pk)
-- usuario_id (string, indexed)
-- aceito (boolean)
-- data_aceito (datetime)
-- data_revogacao (datetime, nullable)
-- versao_politica (string)
-- ip_origem (string, nullable)
-- user_agent (string, nullable)
-- criado_em (datetime, indexed)
```

**Status:** ✅ MODELO ORM CRIADO (Fase 2.2)

---

## 📊 Resumo de Status

| Componente | Implementação | Testes Manuais |
|-----------|---|---|
| Modelo LGPD (ORM) | ✅ Completo | ⏳ Pendente |
| Endpoints LGPD (3x) | ✅ Completo | ⏳ Pendente |
| Modal Vue.js | ✅ Completo | ⏳ Pendente |
| localStorage Controle | ✅ Completo | ⏳ Pendente |
| Página Política (10 seções) | ✅ Completo | ⏳ Pendente |
| Footer Links (index.html) | ✅ Completo | ⏳ Pendente |
| Footer Links (setor.html) | ✅ Completo | ⏳ Pendente |
| E-mails com Username | ✅ Completo | ✅ Verificado |

---

## 🚀 Próximos Passos

1. **Validação Completa:** Executar todos os testes manuais
2. **Deploy Staging:** Seguir procedimento de infraestrutura
3. **Documentação:** Atualizar wiki interna se necessário
4. **Fase 3:** Aguardar revisão jurídica para encriptação + auditoria

---

**Criado:** 24/06/2026  
**Versão:** 1.0
