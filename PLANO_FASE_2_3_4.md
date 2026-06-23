# Plano de Implementação — Fases 2, 3 e 4

**Data de Criação:** 23 de junho de 2026  
**Versão:** 1.0 — Pronto para Execução  
**Requer:** Execução como **Administrador** do VS Code

---

## Sumário Executivo

Este documento detalha as **Fases 2, 3 e 4** do plano de ajustes ao Viagens Labs:

| Fase | Duração | Objetivo | Bloqueador | Status |
|------|---------|----------|-----------|--------|
| **1** | 1-2 dias | Remover avisos, simplificar hotéis, converter indicadores para SVG | Nenhum | ✅ Completo |
| **2.1** | < 1 hora | E-mails com username (já implementado) | Nenhum | ✅ Completo |
| **2.2** | 2-3 horas | Modal LGPD + Política de Privacidade | Nenhum | ✅ Completo |
| **2.3** | 1 hora | Integração de links de Política nos footers | Nenhum | 📅 Planejado |
| **2.4** | 2-3 horas | Testes de consentimento + deployment | Fase 2.3 | 📅 Planejado |
| **3** | 1-2 sem | Encriptação em repouso + auditoria + política jurídica | Advogado | 🔒 Aguardando Legal |
| **4** | 3-4 dias | Testes integrados + deploy | Fase 3 | 🧪 Agendado |

---

## FASE 2: Personalização de E-mails e Consentimento LGPD Básico

**Duração Total Fase 2:** 5-7 dias de trabalho  
**Status Atual:** Fases 2.1 e 2.2 concluídas ✅ | Fases 2.3-2.4 em andamento 📅  
**Pré-requisitos:** VS Code em modo administrador, acesso Git ao repositório  
**Responsáveis:** Dev Backend + Dev Frontend

---

### ⚡ Status de Implementação — Resumo

| Item | Status | Detalhes |
|------|--------|----------|
| 2.1 — E-mails Username | ✅ Completo | 6/6 e-mails para solicitante usam `solicitante_username`. 1 e-mail para viajante (delegação) está correto como está |
| 2.2 — Modal LGPD | ✅ Completo | Modal implementado, 3 endpoints LGPD criados, Política de Privacidade (10 seções) finalizada |
| 2.3 — Links Footer | 📅 Próximo | Integrar link "Política de Privacidade" em todos os portais |
| 2.4 — Testes | 📅 Próximo | Testes manuais de consentimento + deployment staging |

---

### 2.1 Personalização de E-mails com Username — ✅ CONCLUÍDO

**Análise Realizada (24/06/2026):**

Todos os 6 e-mails enviados para o **solicitante** (quem cria a solicitação) já usam `solicitacao.solicitante_username`:

```python
# ✅ Correto em 6 funções:
def enviar_email_criacao(...)              # Linha 363
def enviar_email_resultado(...)            # Linha 405
def enviar_email_cotacao_recebida(...)     # Linha 468
def enviar_email_voucher_criado(...)       # Linha 751
def enviar_email_conclusao(...)            # Linha 790
def enviar_email_cotacao_concluida(...)    # Linha 826

# Exemplo:
<p style="margin:0 0 16px">Olá, <strong>{solicitacao.solicitante_username}</strong>,</p>
```

**Caso Especial — Linha 1039:**

A função `enviar_email_notificacao_terceiro()` envia um e-mail para o **viajante** (terceiro em delegação), não para o solicitante. Ela usa `{solicitacao.viajante_nome or solicitacao.viajante_email}`, que está **correto** porque:
- Email é enviado para `solicitacao.viajante_email` (o terceiro)
- Não existe `viajante_username` no banco
- Saudar com `viajante_nome` (ou email como fallback) é apropriado para este contexto

**Conclusão:** Fase 2.1 está 100% implementada. ✅

---

### 2.2 Modal de Consentimento LGPD na Primeira Entrada — ✅ CONCLUÍDO

**Implementação (24/06/2026):**
- ✅ Tabela `LGPDConsentimentoModel` criada em `app/infrastructure/orm/models.py`
- ✅ 3 Endpoints LGPD implementados:
  - `POST /api/v1/lgpd/consentimento` — Registra aceite
  - `GET /api/v1/lgpd/meus-dados` — Portabilidade (Art. 20)
  - `POST /api/v1/lgpd/revogar-consentimento` — Revogação (Art. 8, § 5º)
- ✅ Modal Vue.js implementado em `frontend/index.html` com localStorage diário
- ✅ Página de Política de Privacidade completa: [frontend/politica-privacidade.html](../frontend/politica-privacidade.html)
  - 10 seções com cobertura de Arts. 8, 17, 18, 19, 20 da LGPD
  - Tabela de retenção de dados
  - Links para processadores de dados
  - Formulário de contato para DPO

**Commits:**
- `feat: Fase 2.2 - Modal LGPD...` — Implementação completa
- `docs: Atualização de HANDOFF.md...` — Documentação

---

### 2.3 Integração de Links de Política de Privacidade — 📅 PRÓXIMO

**Duração Estimada:** 1 hora

#### Tarefa 2.3.1 — Adicionar Link em index.html

**Arquivo:** `frontend/index.html`

Localizar o footer (procurar por `<footer>` ou último `<div>` antes de `</body>`) e adicionar:

```html
<div class="text-center text-xs text-gray-600 mt-8 space-y-1">
  <a href="/politica-privacidade.html" target="_blank" class="hover:text-labs-blue transition">
    Política de Privacidade
  </a>
  <span class="mx-2">•</span>
  <a href="mailto:dpo@luizalabs.com" class="hover:text-labs-blue transition">
    Contato DPO
  </a>
</div>
```

#### Tarefa 2.3.2 — Adicionar Link em setor.html

**Arquivo:** `frontend/setor.html`

Mesmo padrão do index.html: adicionar footer com link para Política e DPO.

#### Tarefa 2.3.3 — Adicionar Link em Portais Técnicos (opcional)

Se aplicável, adicionar link em:
- `frontend/portal_aprovacao.html`
- `frontend/agencia.html`
- `frontend/dev.html`

---

### 2.4 Testes de Consentimento + Deployment — 📅 PRÓXIMO

**Duração Estimada:** 2-3 horas

#### Teste 2.4.1 — Verificar Modal LGPD

1. **Primeiro Login:**
   - Abrir `http://localhost/index.html`
   - Fazer login com usuário
   - Verificar se modal LGPD aparece ✓
   - Clicar em "Aceitar e Continuar"
   - Verificar se localStorage salva `lgpd_aceito` e `lgpd_data_aceito`

2. **Mesmo Dia:**
   - Fazer logout e login novamente
   - Verificar se modal NÃO aparece (deve estar bloqueado por localStorage) ✓

3. **Dia Seguinte (testar com dev tools alterando data):**
   - Abrir Console → `localStorage.setItem('lgpd_data_aceito', '2026-06-22')`
   - Fazer logout e login
   - Verificar se modal aparece novamente ✓

#### Teste 2.4.2 — Verificar Endpoints LGPD

```bash
# Teste 1: Registrar consentimento (já feito pelo modal)
curl -X POST http://localhost:8000/api/v1/lgpd/consentimento \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"aceito": true, "versao_politica": "1.0"}'

# Teste 2: Portabilidade de dados
curl -X GET http://localhost:8000/api/v1/lgpd/meus-dados \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Teste 3: Revogar consentimento
curl -X POST http://localhost:8000/api/v1/lgpd/revogar-consentimento \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Teste 2.4.3 — Verificar Política de Privacidade

1. Abrir `http://localhost/politica-privacidade.html`
2. Verificar se todas as 10 seções carregam corretamente
3. Clicar em links para Google, Microsoft (devem abrir em nova aba)
4. Verificar links "Voltar ao Portal" e "Contato DPO" funcionam

#### Teste 2.4.4 — Verificar E-mails com Username

1. Criar uma solicitação de viagem como colaborador
2. Receber e-mail de confirmação
3. Verificar se saudação é: "Olá, **lnd_araujo**," (username, não nome)
4. Verificar se todos os campos estão preenchidos corretamente

#### Deployment Staging

```bash
# 1. Criar migração (se necessária)
cd c:\Projetos\viagens_labs
alembic revision --autogenerate -m "Adicionar tabela lgpd_consentimento"
alembic upgrade head

# 2. Executar testes unitários
pytest app/tests/test_lgpd.py -v

# 3. Fazer deploy em staging
# (Seguir procedimento específico da sua infraestrutura)

# 4. Testar em staging (repetir Testes 2.4.1-2.4.4)

# 5. Se tudo OK, fazer commit final
git add -A
git commit -m "feat: Fase 2 Completa - E-mails, LGPD Modal, Política, Links Footer

- Fase 2.1: E-mails com username (já estava implementado)
- Fase 2.2: Modal LGPD + Política de Privacidade (concluído)
- Fase 2.3: Links de Política nos footers (concluído)
- Fase 2.4: Testes e deployment (concluído)

Testes incluem: Modal diário, localStorage, endpoints LGPD, e-mails, política."
git push origin main
```

---
});

// Função para aceitar consentimento
const aceitarConsentimentoLGPD = async () => {
  if (!consentimentoLGPD.checkbox) return;
  
  try {
    // Enviar consentimento para backend
    const res = await fetch('/api/v1/lgpd/consentimento', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usuario_id: usuarioId.value,
        aceito: true,
        versao_politica: '1.0'
      })
    });
    
    if (res.ok) {
      consentimentoLGPD.aceito = true;
      consentimentoLGPD.localStorage = true;
      // Armazenar em localStorage para não mostrar novamente por 30 dias
      localStorage.setItem('consentimento_lgpd_timestamp', new Date().getTime());
    }
  } catch (e) {
    console.error('Erro ao registrar consentimento:', e);
  }
};

// Verificar localStorage ao carregar
onMounted(() => {
  const timestamp = localStorage.getItem('consentimento_lgpd_timestamp');
  if (timestamp) {
    const agora = new Date().getTime();
    const dias = (agora - parseInt(timestamp)) / (1000 * 60 * 60 * 24);
    if (dias < 30) {
      consentimentoLGPD.localStorage = true;
    }
  }
});
```

#### 2.2.3 Registrar Consentimento no Backend

**Arquivo:** `app/api/v1/endpoints/lgpd.py` (novo arquivo)

Tarefa:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.orm.models import LGPDConsentimento
from app.api.dependencies import require_auth
from datetime import datetime

router = APIRouter(prefix="/api/v1/lgpd", tags=["LGPD"])

@router.post("/consentimento")
def registrar_consentimento(
    req: dict,
    usuario_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Registra aceitar consentimento LGPD do usuário."""
    
    consent = LGPDConsentimento(
        usuario_id=usuario_id,
        aceito=req['aceito'],
        data_aceito=datetime.utcnow(),
        versao_politica=req.get('versao_politica', '1.0'),
        ip_origem=request.client.host
    )
    db.add(consent)
    db.commit()

## FASE 3: Encriptação em Repouso + Auditoria + Política Jurídica

**Duração Estimada:** 1-2 semanas  
**Pré-requisitos:** Fase 2 concluída, Advogado disponível  
**Responsáveis:** Dev Backend + DPO/Jurídico

---

### 3.1 Contratação e Revisão Jurídica

**Tarefa Principal:** Validar conformidade com LGPD

**Deliverable Esperado:**
```
Documento de Política de Privacidade Formal (2-3 páginas)
  ├─ Identidade do Controlador (Luizalabs)
  ├─ DPO (Encarregado)
  ├─ Base Legal (Contrato de trabalho + consentimento)
  ├─ Dados coletados (lista completa)
  ├─ Fins de tratamento (viagem, aprovação, reembolso, auditoria)
  ├─ Destinatários (Google, Agências, Gestores, Auditores)
  ├─ Direitos dos Titulares (acesso, retificação, exclusão, portabilidade)
  ├─ Período de Retenção (mínimo 2 anos por lei, máximo N conforme política)
  └─ Procedimento de Exercício de Direitos (e-mail, formulário, SLA)
```

**Timeline:** Inicie contratação agora; target de retorno: +5 dias úteis

---

### Status de Continuidade (23/06/2026 - Sessão Atual)

- ✅ Etapa 3.4.2 iniciada e implementada no backend:
  - Novo endpoint `POST /api/v1/lgpd/solicitar-delecao` em `app/api/v1/endpoints/lgpd.py`.
  - Nova tabela `lgpd_solicitacao_delecao` via ORM (`LGPDSolicitacaoDelecaoModel`).
  - Migração segura adicionada em `app/main.py` (`CREATE TABLE IF NOT EXISTS ...`).
  - Regras implementadas: cria solicitação com janela de 30 dias e evita duplicidade pendente por usuário.
  - Cobertura de testes adicionada/atualizada em `tests/test_lgpd_api.py` e `tests/conftest.py`.

- ✅ Etapa 3.3 iniciada com base técnica implementada:
  - Nova tabela `auditoria_lgpd` em ORM (`AuditoriaLGPDModel`).
  - Migração segura adicionada em `app/main.py` (`CREATE TABLE IF NOT EXISTS ...`).
  - Middleware global atualizado para persistir trilha dedicada para endpoints sensíveis (`/api/v1/viagens`, `/api/v1/setor`, `/api/v1/aprovacao`, `/api/v1/lgpd/meus-dados`).

- ✅ Etapa 3.5 implementada e testada:
  - Novo scheduler daemon `app/infrastructure/lgpd_scheduler.py` que roda a cada 1 hora.
  - Função `_processar_delecoes_expiradas()` busca solicitações PENDENTES com `data_execucao <= now`.
  - Executa deleção de viagens (`SolicitacaoModel`) e anonimização de tokens (`TokenAprovacaoModel`).
  - Marca solicitação como PROCESSADA e registra em `AuditoriaLGPDModel`.
  - Scheduler registrado em `app/main.py` via `iniciar_lgpd_scheduler()`.
  - 3 testes novos em `tests/test_lgpd_scheduler.py` com 100% de cobertura (18 testes total passando).

- ✅ Etapa 3.6 implementada e funcional:
  - Modal de consentimento LGPD para gestores no `frontend/setor.html`.
  - Conteúdo específico para operadores de dados (gestores que acessam dados de subordinados).
  - Termo de responsabilidade destacando confidencialidade, finalidade, segurança e auditoria.
  - Integração com endpoint `/api/v1/lgpd/consentimento` com tipo `gestor_operador`.
  - Verificação diária via localStorage (renova consentimento a cada dia de acesso).
  - Modal bloqueia acesso às funcionalidades até aceite do termo.

- 🔜 Próxima execução recomendada do plano (ordem):
  1. ~~Etapa 3.5 (job de processamento de solicitações expiradas)~~ ✅ Concluída
  2. ~~Etapa 3.6 (termo de consentimento para gestores no portal do setor)~~ ✅ Concluída
  3. **Etapa 3.2** ⏸️ Aguardando alinhamento jurídico sobre política de retenção de dados (encriptação em repouso).
  4. **Fase 4** (validação, testes integrados e deploy em produção) - pode ser iniciada em paralelo.

---

## 🚧 Bloqueadores Conhecidos

- **Etapa 3.2 (Encriptação em Repouso)**: Depende de aprovação da equipe jurídica/DPO sobre política de retenção final. Contato: DPO (dpo@luizalabs.com)

---

### 3.2 Encriptação de Dados em Repouso

#### 3.2.1 Colunas Sensíveis a Criptografar

**Arquivo:** `app/infrastructure/orm/models.py`

Identificar:
- `CPF` do viajante
- Data de nascimento (`data_nascimento`)
- Qualquer dado PII adicional

#### 3.2.2 Implementar Encriptação com `cryptography`

**Arquivo:** `app/core/security.py`

Tarefa:
```python
from cryptography.fernet import Fernet
import os

class CryptographyUtil:
    def __init__(self):
        # Chave deve vir de variável de ambiente segura
        self.cipher = Fernet(os.getenv("ENCRYPTION_KEY").encode())
    
    def encrypt(self, plaintext: str) -> str:
        """Encripta string e retorna base64."""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decripta string."""
        return self.cipher.decrypt(ciphertext.encode()).decode()

crypto_util = CryptographyUtil()
```

#### 3.2.3 Usar em ORM

**Arquivo:** `app/infrastructure/orm/models.py`

Tarefa:
```python
from app.core.security import crypto_util

class SolicitacaoViagem(Base):
    # ... outras colunas ...
    
    _cpf = Column(String(255), name="cpf_criptografado")
    
    @property
    def cpf(self):
        """Propriedade que desencripta sob demanda."""
        return crypto_util.decrypt(self._cpf) if self._cpf else None
    
    @cpf.setter
    def cpf(self, value):
        """Setter que encripta ao armazenar."""
        self._cpf = crypto_util.encrypt(value) if value else None
```

#### 3.2.4 Migração de Dados Existentes

**Arquivo:** `scripts/migrate_encrypt_pii.py`

Tarefa:
```python
#!/usr/bin/env python
"""
Script de migração: encripta CPF de registros existentes.
Rodar UMA VEZ após deploy do código de encriptação.

Uso: python scripts/migrate_encrypt_pii.py
"""

from app.infrastructure.database import SessionLocal
from app.infrastructure.orm.models import SolicitacaoViagem
from app.core.security import crypto_util

session = SessionLocal()
count = 0

# Buscar todos os registros com CPF não encriptado
for solicitacao in session.query(SolicitacaoViagem).filter(
    SolicitacaoViagem._cpf.like('%;%')  # Padrão: já encriptado tem ';'
):
    if solicitacao.cpf and not solicitacao.cpf.startswith('gAAAAAA'):  # Não é Fernet
        print(f"Encriptando {solicitacao.protocolo}...")
        solicitacao.cpf = solicitacao.cpf  # Setter encripta
        count += 1

session.commit()
print(f"✅ {count} registros encriptados com sucesso.")
```

**Estimado:** 4-6 horas

---

### 3.3 Auditoria e Logging de Acesso

#### 3.3.1 Criar Tabela de Auditoria

**Arquivo:** `app/infrastructure/orm/models.py`

Tarefa:
```python
class AuditoriaLGPD(Base):
    __tablename__ = "auditoria_lgpd"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(50), index=True)
    acao = Column(String(50))  # "VER_VIAGEM", "EXPORTAR_DADOS", "ACESSAR_CPF"
    recurso = Column(String(255))  # "protocolo:REQ-2026-001"
    dados_acessados = Column(String(255))  # "cpf, data_nascimento"
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_origem = Column(String(15))
    user_agent = Column(String(255), nullable=True)
```

#### 3.3.2 Middleware de Logging

**Arquivo:** `app/main.py`

Tarefa:
```python
from app.infrastructure.orm.models import AuditoriaLGPD
from datetime import datetime

@app.middleware("http")
async def log_acesso_dados_sensivel(request: Request, call_next):
    """Middleware que loga acesso a endpoints sensíveis."""
    
    # Endpoints sensíveis que devem ser auditados
    ENDPOINTS_SENSIVEL = [
        "/api/v1/viagens",
        "/api/v1/setor/detalhe",
        "/api/v1/aprovacao"
    ]
    
    if any(request.url.path.startswith(ep) for ep in ENDPOINTS_SENSIVEL):
        usuario = getattr(request.state, "user", "anonimo")
        ip = request.client.host if request.client else "0.0.0.0"
        
        # Registrar no BD
        async with get_db() as db:
            auditoria = AuditoriaLGPD(
                usuario_id=usuario,
                acao=request.method,
                recurso=request.url.path,
                ip_origem=ip,
                user_agent=request.headers.get("user-agent", "")[:255],
                timestamp=datetime.utcnow()
            )
            db.add(auditoria)
            await db.commit()
    
    response = await call_next(request)
    return response
```

**Estimado:** 2-3 horas

---

### 3.4 Direito de Acesso e Portabilidade

#### 3.4.1 Endpoint: Baixar Meus Dados

**Arquivo:** `app/api/v1/endpoints/lgpd.py`

Tarefa:
```python
@router.get("/meus-dados")
async def meus_dados(
    usuario_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Retorna todos os dados pessoais do usuário em JSON.
    Base Legal: Art. 18, LGPD (Direito de Acesso)
    """
    
    viagens = db.query(SolicitacaoViagem).filter(
        SolicitacaoViagem.solicitante_id == usuario_id
    ).all()
    
    return {
        "usuario": {
            "id": usuario_id,
            "nome": usuario.nome,
            "email": usuario.email,
            "cpf": usuario.cpf,  # Será desencriptado automaticamente
            "data_nascimento": usuario.data_nascimento
        },
        "viagens": [
            {
                "protocolo": v.protocolo,
                "data_ida": v.data_ida,
                "data_volta": v.data_volta,
                "destino": f"{v.destino_cidade}/{v.destino_estado}",
                "status": v.status,
                "custo_total": v.custo_total
            }
            for v in viagens
        ]
    }
```

#### 3.4.2 Endpoint: Solicitar Exclusão

**Arquivo:** `app/api/v1/endpoints/lgpd.py`

Tarefa:
```python
@router.post("/solicitar-delecao")
async def solicitar_delecao(
    usuario_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Usuário solicita exclusão de seus dados.
    Será processada após 30 dias (direito ao esquecimento, Art. 17 LGPD).
    """
    
    solicitacao = SolicitacaoDeletacao(
        usuario_id=usuario_id,
        data_solicitacao=datetime.utcnow(),
        data_execucao=datetime.utcnow() + timedelta(days=30),
        status="PENDENTE"
    )
    db.add(solicitacao)
    db.commit()
    
    # Notificar DPO
    await enviar_email_dpo(
        assunto="Nova Solicitação de Exclusão de Dados",
        corpo=f"Usuário {usuario_id} solicitou exclusão. Executar em {solicitacao.data_execucao.date()}"
    )
    
    return {"status": "ok", "msg": "Solicitação registrada. Será processada em 30 dias."}
```

**Estimado:** 3-4 horas

---

### 3.5 Direito ao Esquecimento (Exclusão Automática)

#### 3.5.1 Scheduler de Limpeza

**Arquivo:** `app/infrastructure/aprovacao_relay_scheduler.py` (ou novo: `lgpd_scheduler.py`)

Tarefa:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', day_of_week='sun', hour=2)
def limpar_dados_expirados():
    """
    Executa toda domingo às 2 da manhã.
    Deleta dados de usuários com solicitação de exclusão após 30 dias.
    """
    session = SessionLocal()
    
    agora = datetime.utcnow()
    
    # Buscar solicitações expiradas
    expiradas = session.query(SolicitacaoDeletacao).filter(
        SolicitacaoDeletacao.data_execucao <= agora,
        SolicitacaoDeletacao.status == "PENDENTE"
    ).all()
    
    for sol in expiradas:
        usuario_id = sol.usuario_id
        print(f"[LGPD] Deletando dados de {usuario_id}...")
        
        # 1. Manter registro de auditoria (obrigação legal)
        # 2. Deletar SolicitacaoViagem
        session.query(SolicitacaoViagem).filter(
            SolicitacaoViagem.solicitante_id == usuario_id
        ).delete()
        
        # 3. Anonimizar em Aprovacoes (nome → "Anônimo")
        session.query(Aprovacao).filter(
            Aprovacao.usuario_id == usuario_id
        ).update({
            Aprovacao.usuario_nome: "Anônimo",
            Aprovacao.usuario_id: f"DELETED_{uuid4()}"
        })
        
        # 4. Marcar como processada
        sol.status = "PROCESSADA"
        sol.data_processamento = agora
        
        session.commit()
        
        # 5. Registrar em auditoria
        auditoria = AuditoriaLGPD(
            usuario_id="SISTEMA",
            acao="DELETACAO_AUTOMATICA",
            recurso=f"usuario:{usuario_id}",
            timestamp=agora,
            ip_origem="0.0.0.0"
        )
        session.add(auditoria)
    
    session.commit()
    print(f"[LGPD] ✅ {len(expiradas)} registros deletados.")
    session.close()

scheduler.start()
```

**Estimado:** 2-3 horas

---

### 3.6 Termo de Consentimento para Gestores

**Arquivo:** `frontend/setor.html`

Tarefa:
1. Adicionar modal de consentimento LGPD na primeira entrada de setor.html
2. Conteúdo: "Ao acessar este painel, você reconhece que terá acesso a dados pessoais de colaboradores sob proteção LGPD..."
3. Exigir aceitar antes de acessar qualquer aba

**Estimado:** 1-2 horas

---

## FASE 4: Validação, Testes e Deploy

**Duração Estimada:** 3-4 dias  
**Pré-requisitos:** Fases 2 e 3 concluídas  
**Responsáveis:** QA + Dev + Segurança

---

### 4.1 Testes Integrados

#### 4.1.1 Testes de Funcionalidade

Checklist:
- [ ] Modal de consentimento aparece na primeira entrada
- [ ] Username correto em todos os e-mails (não nome)
- [ ] Dados sensíveis não aparecem em logs ou console
- [ ] Buscar por dados exporta em JSON corretamente
- [ ] Solicitação de exclusão marca para processamento
- [ ] Scheduler executa limpeza automática aos domingos

#### 4.1.2 Testes de Segurança

Checklist:
- [ ] HTTPS está ativo em produção
- [ ] Certificado SSL válido e atualizado
- [ ] Dados encriptados em repouso (CPF, data nascimento)
- [ ] Auditoria registra todos os acessos sensíveis
- [ ] Token de aprovação tem TTL válido
- [ ] Nenhuma credencial exposta em código

#### 4.1.3 Testes de Conformidade LGPD

Checklist:
- [ ] Política de Privacidade está publicada
- [ ] Consentimento é registro obrigatório
- [ ] Usuário pode revogar consentimento
- [ ] Usuário pode baixar seus dados
- [ ] DPO foi informado de todos os processamentos
- [ ] Retenção de dados segue política

**Estimado:** 2-3 dias

---

### 4.2 Auditoria Interna

Tarefa:
1. Convidar Advogado ou especialista em LGPD para revisar
2. Validar:
   - Conformidade com Lei 13.709/2018
   - Adequação de base legal
   - Suficiência de controles de segurança
   - Documentação completa

**Estimado:** 1 dia

---

### 4.3 Deploy em Produção

#### 4.3.1 Checklist de Pré-Deploy

- [ ] Todas as migrations executadas (encriptação, auditoria, LGPD)
- [ ] Variáveis de ambiente configuradas (ENCRYPTION_KEY, etc.)
- [ ] Backend testado localmente
- [ ] Frontend testado em múltiplos browsers
- [ ] E-mails testados com username
- [ ] Política de Privacidade publicada em /politica-privacidade.html
- [ ] Logs limpos de dados sensíveis
- [ ] Certificado SSL renovado se necessário

#### 4.3.2 Plano de Deploy

```bash
# 1. Backup do banco de dados
pg_dump -h 127.0.0.1 -U postgres solicitacao_viagens > backup_2026-06-XX.sql

# 2. Pull da branch main
git pull origin main

# 3. Instalar dependências novas (se houver)
pip install -r requirements.txt

# 4. Executar migrations
python scripts/migrate_encrypt_pii.py

# 5. Reiniciar serviços
systemctl restart viagens-labs-backend
systemctl restart nginx

# 6. Verificação pós-deploy
curl https://viagenslabs.magazineluiza.intranet/api/v1/health
```

#### 4.3.3 Monitoramento Pós-Deploy

- [ ] Verificar logs para erros
- [ ] Testar criação de solicitação de viagem
- [ ] Testar envio de e-mail com username correto
- [ ] Verificar se modal de consentimento aparece
- [ ] Confirmar que dados são encriptados no BD

**Estimado:** 1 dia

---

## Resumo de Recursos Necessários

| Fase | Papel | Horas | Notas |
|------|-------|-------|-------|
| 2 | Dev Backend | 6-8h | Personalizar e-mails |
| 2 | Dev Frontend | 6-8h | Modal consentimento LGPD |
| 2 | Dev Backend | 3-4h | Política de Privacidade |
| 3 | Advogado | 20-30h | **Bloqueador crítico** |
| 3 | Dev Backend | 8-10h | Encriptação + Auditoria |
| 3 | DPO | 4-6h | Coordenação e conformidade |
| 4 | QA | 8-10h | Testes integrados |
| 4 | Dev Backend | 2-3h | Deploy e pós-monitoramento |
| | **TOTAL** | **~80-90h** | |

---

## Checklist Final

Antes de considerar o projeto concluído:

- [ ] Fase 1 concluída (avisos removidos, hotéis simplificados, SVG ativo)
- [ ] Fase 2 concluída (e-mails com username, consentimento LGPD)
- [ ] Fase 3 concluída (encriptação, auditoria, política jurídica)
- [ ] Fase 4 concluída (testes, auditoria, deploy)
- [ ] Documentação HANDOFF.md atualizada
- [ ] README.md atualizado com conformidade LGPD
- [ ] Todos os commits têm mensagens descritivas
- [ ] Nenhuma credencial ou dados sensíveis em repositório público

---

## Contatos de Suporte

| Papel | Contato |
|-------|---------|
| Dev Backend | leandro.araujo@luizalabs.com |
| DPO/Jurídico | dpo@luizalabs.com |
| Agências | Tastur, Kontrip |

---

**Documento assinado eletronicamente em 23/06/2026 — Pronto para Execução**

Qualquer dúvida ou bloqueador, refira a sessão de IA correspondente ou revisite este plano.
