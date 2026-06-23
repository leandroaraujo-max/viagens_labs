# Plano de Implementação — Ajustes Viagens Labs

**Data:** 23 de junho de 2026  
**Status:** Em planejamento

---

## 1. DEMANDAS IMEDIATAS (Frontend UI/UX)

### 1.1 Remover Avisos Desnecessários
**Prioridade:** Alta  
**Esforço:** 10 min

**Ações:**
- Remover alerta "Preencha a data de volta para buscar voo de retorno" (linha ~555 em index.html)
- Remover caixa azul "O período de voo deve ser escolhido nos cards abaixo." (linha ~565 em index.html)

**Impacto:** UX mais limpa e direta

**Status:** Pronto para implementação

---

### 1.2 Simplificar Integração de Hotéis
**Prioridade:** Alta  
**Esforço:** 30 min

**Ações:**
1. Remover integração com Google Places API (Google Relay Service)
2. Remover botão "Sugerir" de busca de hotéis
3. Remover dropdown de resultados de hotéis
4. Manter apenas:
   - Textbox simples: "Sugestão de Hotel (opcional)"
   - Label: "Informe manualmente o hotel preferido"
5. Remover erros/validações de busca de hotel

**Componentes afetados:**
- [frontend/index.html](frontend/index.html) — linhas ~695-730
- Backend: remover ou desabilitar endpoint Google Places (se existir)

**Dependências:** Remover uso de `buscarHoteisGoogle()`, `hoteisGoogle[]`, `hoteisGoogleErro`

**Status:** Pronto para implementação

---

### 1.3 Converter Painel de Indicadores (BI) para SVG
**Prioridade:** Média  
**Esforço:** 2-3 horas

**Ações:**
1. Localizar [frontend/setor.html](frontend/setor.html) — painel de indicadores (KPIs)
2. Converter ícones neon/emojis para SVG inline
3. Aplicar script `svgify-emojis.js` (já existe)
4. Reduzir paleta de cores neon:
   - Substituir `bg-cyan-100/30`, `bg-amber-100/30` por tons mais neutros
   - Usar escala cinza + azul corporativo (labs-blue)
   - Remover brilho excessivo

**Componentes afetados:**
- [frontend/setor.html](frontend/setor.html) — blocos de status (linhas ~1660+)
- CSS: revisar classes Tailwind com `neon` ou `glow`

**Status:** Pronto para implementação

---

## 2. PERSONALIZAÇÃO DE E-MAILS

### 2.1 Usar Username em Saudações
**Prioridade:** Média  
**Esforço:** 45 min

**Ações:**
1. Localizar templates de e-mail (provavelmente em `app/infrastructure/email_service.py` ou GAS relay)
2. Substituir `{{ nome_viajante }}` por `{{ username }}` (username AD = "lnd_araujo")
3. Templates afetados:
   - Confirmação de solicitação
   - Notificação N1
   - Notificação N2
   - Aprovação/Rejeição
   - Cotação de agência

**Estrutura esperada:**
```
Olá {{ username }},

Sua solicitação de viagem foi registrada no sistema...
```

**Onde:** Provavelmente em GAS relay (`gas/Code.gs`) ou backend (`app/infrastructure/email_service.py`)

**Status:** Requer localização exata dos templates

---

## 3. CONFORMIDADE LGPD (Demanda Crítica)

### 3.1 Contexto Legal
- **Lei:** Lei Geral de Proteção de Dados (Lei nº 13.709/2018)
- **Dados:** Colaboradores (e-mail, CPF, data nascimento, dados pessoais)
- **Operação:** Trafego ponta-a-ponta entre portal (frontend), backend e sistemas externos (GAS, BigQuery, LDAP)
- **Base Legal Aplicável:** Artigo 7, inciso II (consentimento explícito) e/ou inciso V (execução de contrato de trabalho)

---

### 3.2 Ações Necessárias

#### 3.2.1 Consentimento Explícito do Usuário
**Prioridade:** CRÍTICA  
**Esforço:** 2 horas

**Ações:**
1. Criar modal de consentimento LGPD na primeira entrada do colaborador
2. Conteúdo mínimo:
   ```
   🔐 Aviso de Privacidade — LGPD

   Ao acessar este portal, você reconhece que:

   ✓ Seus dados pessoais (email, CPF, nome, data nascimento) 
     serão processados pela Luizalabs para gerenciamento de viagens corporativas.
   
   ✓ Os dados trafegam de forma criptografada entre:
     - Seu navegador (portal)
     - Servidores Luizalabs (backend)
     - Sistemas integrados (Google Apps, BigQuery, Active Directory)

   ✓ Você tem direito a:
     - Acessar seus dados
     - Solicitar retificação ou exclusão
     - Revogar consentimento (com impacto no serviço)

   ✓ Gestão de dados: DPO (Encarregado) = [email@luizalabs.com]

   [ ] Declaro ter lido e concordo com esta política
   ```

3. Armazenar consentimento em BD com timestamp
4. Exigir aceitar antes de qualquer ação no sistema
5. Permitir revogar consentimento (com confirmação de impacto)

**Componentes:**
- Frontend: novo modal em [frontend/index.html](frontend/index.html) ou página separada
- Backend: endpoint para registrar consentimento (`POST /api/v1/lgpd/consentimento`)
- BD: tabela `lgpd_consentimentos` com campos:
  ```
  id, usuario_id, aceito (bool), data_aceito, data_revogacao, versao_politica
  ```

**Status:** Requer especificação de política completa

---

#### 3.2.2 Política de Privacidade Formal
**Prioridade:** CRÍTICA  
**Esforço:** 4-6 horas (requer revisão legal)

**Ações:**
1. Elaborar documento formal com advogado:
   - Identificação do Controlador (Luizalabs)
   - Identificação do DPO (encarregado)
   - Base legal (contrato de trabalho, artigo 7, inciso V LGPD)
   - Dados coletados (lista completa)
   - Fins de tratamento (gestão de viagens, aprovações, reembolsos)
   - Destinatários (Google, BigQuery, agências, gestores)
   - Direitos do titular
   - Período de retenção
   - Procedimento de exclusão

2. Publicar em página acessível: `/politica-privacidade.html`

3. Incluir no portal: link no footer + aceitar na primeira entrada

**Documento esperado:** 2-3 páginas formatadas

**Status:** Requer suporte legal externo

---

#### 3.2.3 Encriptação de Dados em Trânsito
**Prioridade:** ALTA  
**Esforço:** 1 hora (verificação)

**Ações:**
1. Verificar se HTTPS está ativado:
   - Frontend: confirmar protocolo HTTPS em produção
   - Backend: verificar certificado SSL/TLS
   - Nginx: validar configuração HTTPS

2. Testar:
   ```bash
   curl -v https://viagenslabs.magazineluiza.intranet 2>&1 | grep "SSL"
   ```

3. Se necessário, ativar:
   - Adquirir certificado SSL (Let's Encrypt gratuito ou corporativo)
   - Configurar em Nginx
   - Redirecionar HTTP → HTTPS

**Status:** Provavelmente já implementado

---

#### 3.2.4 Proteção de Dados em Repouso
**Prioridade:** ALTA  
**Esforço:** 2-4 horas

**Ações:**
1. Avaliar campos sensíveis em BD:
   - CPF: criptografar com chave corporativa
   - Data de nascimento: criptografar
   - Email: já seguro (LCPF)

2. Implementar:
   - Usar biblioteca `cryptography` (Python)
   - Armazenar chave em variável de ambiente segura
   - Criar migração para criptografar dados existentes

3. Exemplo (Python):
   ```python
   from cryptography.fernet import Fernet
   
   cipher = Fernet(os.getenv("ENCRYPTION_KEY"))
   cpf_criptografado = cipher.encrypt(cpf.encode())
   ```

**Status:** Requer implementação

---

#### 3.2.5 Auditoria e Logging de Acesso
**Prioridade:** ALTA  
**Esforço:** 2 horas

**Ações:**
1. Ativar logging de acesso a dados sensíveis:
   - Quem acessou (usuário)
   - Quando (timestamp)
   - Qual dado (CPF, nome, etc.)
   - Motivo (viagem, aprovação, etc.)

2. Implementar em backend:
   ```python
   @app.middleware("http")
   async def log_acesso_dados_sensivel(request, call_next):
       # Log se acessou endpoint com dados sensíveis
       if "/viagens/" in request.url.path:
           logger.info(f"Acesso: {request.user} em {request.url}")
       response = await call_next(request)
       return response
   ```

3. Armazenar em tabela `auditoria_lgpd`:
   ```
   id, usuario_id, acao, dados_acessados, timestamp, ip
   ```

**Status:** Pronto para implementação

---

#### 3.2.6 Direito de Acesso e Portabilidade
**Prioridade:** MÉDIA  
**Esforço:** 3 horas

**Ações:**
1. Criar endpoint: `GET /api/v1/lgpd/meus-dados`
   - Retorna todos os dados pessoais do usuário em JSON

2. Criar endpoint: `POST /api/v1/lgpd/solicitar-delecao`
   - Usuário solicita exclusão
   - Sistema marca para exclusão após 30 dias
   - Notifica DPO

3. Frontend: página "Meus Dados LGPD"
   - Visualizar dados coletados
   - Botão: "Baixar meus dados"
   - Botão: "Solicitar exclusão"

**Status:** Pronto para implementação

---

#### 3.2.7 Direito ao Esquecimento
**Prioridade:** MÉDIA  
**Esforço:** 2 horas

**Ações:**
1. Criar procedimento automático de exclusão:
   - Após 2 anos sem acesso ou 30 dias após solicitação
   - Excluir de tabelas: `colaboradores`, `viagens`, `aprovacoes`, `cotacoes`
   - Manter apenas: `auditoria_lgpd` (obrigação legal)

2. Implementar job agendado:
   ```python
   @scheduler.scheduled_job('cron', day_of_week='sun', hour=2)
   def limpar_dados_expirados():
       # Excluir colaboradores marcados para exclusão
       pass
   ```

**Status:** Pronto para implementação

---

#### 3.2.8 Termo de Consentimento para Gestores/Aprovadores
**Prioridade:** MÉDIA  
**Esforço:** 1 hora

**Ações:**
1. Criar termo específico para N1/N2:
   - "Ao acessar este painel, você reconhece que terá acesso a dados pessoais de colaboradores..."
   - Exigir aceitar antes de acessar `setor.html`

2. Adicionar a `setor.html`:
   - Modal de consentimento na primeira entrada
   - Checkbox: "Declaro estar ciente das obrigações LGPD ao acessar dados de colaboradores"

**Status:** Pronto para implementação

---

### 3.3 Resumo Conformidade LGPD

| Ação | Prioridade | Esforço | Dependência | Status |
|------|------------|---------|-------------|--------|
| Consentimento do usuário | CRÍTICA | 2h | Política | Planejado |
| Política de Privacidade | CRÍTICA | 6h | Advogado | Bloqueado |
| Encriptação em trânsito | ALTA | 1h | Infraestrutura | Verificar |
| Encriptação em repouso | ALTA | 4h | Backend | Planejado |
| Auditoria de acesso | ALTA | 2h | Backend | Planejado |
| Direito de acesso | MÉDIA | 3h | Backend/Frontend | Planejado |
| Direito ao esquecimento | MÉDIA | 2h | Backend | Planejado |
| Termo para gestores | MÉDIA | 1h | Frontend | Planejado |

---

## 4. CRONOGRAMA PROPOSTO

### Fase 1: Imediato (1-2 dias)
- [ ] Remover avisos desnecessários
- [ ] Simplificar hotéis
- [ ] Converter indicadores para SVG
- **Responsável:** Dev Frontend

### Fase 2: Rápido (3-5 dias)
- [ ] Personalizar e-mails com username
- [ ] Iniciar Modal de consentimento LGPD
- [ ] Ativar logging de auditoria
- **Responsável:** Dev Backend + Frontend

### Fase 3: Conformidade Legal (1-2 semanas)
- [ ] Contratar revisão jurídica
- [ ] Elaborar Política de Privacidade
- [ ] Implementar encriptação em repouso
- [ ] Criar endpoints de acesso/portabilidade
- **Responsável:** DPO (interno) + Advogado externo

### Fase 4: Validação (3-4 dias)
- [ ] Testes de conformidade LGPD
- [ ] Revisão de segurança
- [ ] Deploy em produção
- **Responsável:** QA + Segurança

---

## 5. RECURSOS NECESSÁRIOS

- **Dev Frontend:** 5-6 horas
- **Dev Backend:** 10-12 horas
- **DPO/Jurídico:** 20+ horas (externo)
- **Segurança:** 3-4 horas (verificação)
- **QA:** 4-5 horas (testes)

**Total estimado:** 40-50 horas efetivas

---

## 6. RISCOS E MITIGAÇÕES

| Risco | Impacto | Mitigation |
|-------|---------|-----------|
| Rejeição do consentimento | Usuário sem acesso | Tornar obrigatório e educativo |
| Latência de encriptação | Performance | Implementar cache de chaves |
| Conformidade incompleta | Multa LGPD | Revisar com advogado |
| Dados não excluíveis | Obrigação legal | Testar procedimento antes |

---

## 7. PRÓXIMOS PASSOS

1. **Imediato:** Executar Fase 1 (2 dias)
2. **Curto prazo:** Contratar advogado para LGPD
3. **Médio prazo:** Implementar Fase 2 + 3 em paralelo
4. **Validação:** Auditoria interna antes de publicar

---

**Assinado:** Sistema Viagens Labs  
**Data:** 23/06/2026
