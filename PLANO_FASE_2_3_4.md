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
| **2** | 5-7 dias | E-mails com username + consentimento LGPD inicial | Nenhum | 📅 Planejado |
| **3** | 1-2 sem | Encriptação em repouso + auditoria + política jurídica | Advogado | 🔒 Aguardando Legal |
| **4** | 3-4 dias | Testes integrados + deploy | Fase 3 | 🧪 Agendado |

---

## FASE 2: Personalização de E-mails e Consentimento LGPD Básico

**Duração Estimada:** 5-7 dias de trabalho  
**Pré-requisitos:** VS Code em modo administrador, acesso Git ao repositório  
**Responsáveis:** Dev Backend + Dev Frontend

---

### 2.1 Personalização de E-mails com Username

#### 2.1.1 Localizar Templates de E-mail

**Arquivo:** `app/infrastructure/email_service.py`

Tarefa:
1. Abrir arquivo Python
2. Localizar função `enviar_email_aprovacao_n1()`, `enviar_email_aprovacao_n2()`, etc.
3. Encontrar pattern: `{{ nome_viajante }}` ou similar

**Esperado:**
```python
# Atual (errado):
"Olá {{ nome_viajante }},\n\nSua solicitação foi criada..."

# Deve virar:
"Olá {{ username }},\n\nSua solicitação foi criada..."
```

#### 2.1.2 Templates de E-mail

**Arquivos de Template:**
- `app/infrastructure/email_templates/approval_n1.html`
- `app/infrastructure/email_templates/approval_n2.html`
- `app/infrastructure/email_templates/agency_cotacao.html`
- `app/infrastructure/email_templates/agency_vencedora.html`
- `app/infrastructure/email_templates/confirmacao_solicitacao.html`
- Qualquer outro com `{{ viajante_nome }}` ou `{{ nome_viajante }}`

Tarefa:
```html
<!-- Antes -->
<p>Olá {{ viajante_nome }},</p>

<!-- Depois -->
<p>Olá {{ username }},</p>
```

#### 2.1.3 Verificar Disponibilidade de `username` no Banco

**Arquivo:** `app/infrastructure/orm/models.py`

Tarefa:
1. Localizar tabela ORM `solicitacao_viagem`
2. Verificar coluna `solicitante_username` (já deve existir)
3. Se não existir, adicionar via migração:

```python
class SolicitacaoViagem(Base):
    __tablename__ = "solicitacao_viagem"
    
    # ... colunas existentes ...
    solicitante_username = Column(String(50))  # Novo campo se necessário
```

#### 2.1.4 Atualizar Context de Rendering

**Arquivo:** `app/services/viagens_service.py` ou `app/services/email_service.py`

Tarefa:
1. Ao enviar e-mail, passar contexto com `username`:

```python
context = {
    "username": solicitacao.solicitante_username,  # "lnd_araujo"
    "protocolo": solicitacao.protocolo,
    # ... outros campos ...
}

html = template.render(context)
```

#### 2.1.5 Testes

Tarefa:
1. Criar solicitação de viagem com seu usuário
2. Verificar e-mail recebido (procurar por "Olá lnd_araujo" ou seu username)
3. Confirmar que nome de display não aparece mais

**Estimado:** 3-4 horas

---

### 2.2 Modal de Consentimento LGPD na Primeira Entrada

#### 2.2.1 Criar Modal de Consentimento

**Arquivo:** `frontend/index.html`

Tarefa:
1. Adicionar novo modal Vue.js ANTES do formulário multipassos
2. Estrutura esperada:

```html
<!-- Modal LGPD Consentimento -->
<div v-if="!consentimentoLGPD.aceito && !consentimentoLGPD.localStorage" 
     class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
  <div class="bg-white rounded-2xl p-8 max-w-2xl w-full mx-4 shadow-2xl">
    
    <div class="flex items-center gap-3 mb-4">
      <span class="text-2xl">🔐</span>
      <h2 class="text-lg font-bold text-gray-800">Aviso de Privacidade — LGPD</h2>
    </div>
    
    <div class="space-y-4 mb-6 text-sm text-gray-700 max-h-96 overflow-y-auto">
      <p>Ao acessar este portal, você reconhece que:</p>
      
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
        <p><strong>✓ Dados coletados:</strong> Seu e-mail, nome completo, CPF, data de nascimento, dados de viagem (origem, destino, datas, custo).</p>
        
        <p><strong>✓ Trafego de dados:</strong> Seus dados trafegam de forma criptografada entre:</p>
        <ul class="ml-4 space-y-1">
          <li>• Seu navegador (portal)</li>
          <li>• Servidores Luizalabs (backend FastAPI)</li>
          <li>• Sistemas integrados (Google BigQuery, Active Directory, Gmail Relay, Google Apps Script)</li>
          <li>• Agências de viagem externas (Tastur, Kontrip)</li>
        </ul>
        
        <p><strong>✓ Fins do tratamento:</strong> Gerenciamento de solicitações de viagens corporativas, aprovações de gestores, cotações de agências, reembolsos.</p>
        
        <p><strong>✓ Base legal:</strong> Relação de empregado-empregador (Art. 7, Inc. V da Lei nº 13.709/2018 — LGPD) e Consentimento Explícito (Art. 7, Inc. II).</p>
        
        <p><strong>✓ Seus direitos:</strong></p>
        <ul class="ml-4 space-y-1">
          <li>• Acessar seus dados pessoais</li>
          <li>• Solicitar retificação ou exclusão</li>
          <li>• Revogar consentimento (com impacto no acesso ao sistema)</li>
          <li>• Portabilidade de dados</li>
        </ul>
        
        <p><strong>✓ DPO (Encarregado):</strong> <a href="mailto:dpo@luizalabs.com" class="text-blue-600 underline">dpo@luizalabs.com</a></p>
        
        <p><strong>✓ Prazo de retenção:</strong> Dados são mantidos enquanto você for ativo no sistema, com direito ao esquecimento (exclusão) após 30 dias de solicitação.</p>
      </div>
      
      <p class="text-xs text-gray-500">Para detalhes completos, consulte nossa <a href="/politica-privacidade.html" target="_blank" class="text-blue-600 underline">Política de Privacidade</a>.</p>
    </div>
    
    <label class="flex items-center gap-3 mb-6">
      <input v-model="consentimentoLGPD.checkbox" type="checkbox" class="w-5 h-5 rounded text-labs-blue">
      <span class="text-sm font-semibold text-gray-700">
        Declaro ter lido e aceito a Política de Privacidade e o tratamento de meus dados conforme descrito acima.
      </span>
    </label>
    
    <div class="flex gap-3 justify-end">
      <button @click="logout()" 
              class="px-4 py-2 text-sm font-semibold border border-gray-300 rounded-lg hover:bg-gray-50 transition">
        Sair
      </button>
      <button @click="aceitarConsentimentoLGPD()" 
              :disabled="!consentimentoLGPD.checkbox"
              class="px-4 py-2 text-sm font-semibold bg-labs-blue text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50">
        Aceitar e Continuar
      </button>
    </div>
  </div>
</div>
```

#### 2.2.2 Adicionar Lógica Vue.js

**Arquivo:** `frontend/index.html` (seção `<script>`)

Tarefa:
```javascript
// Estado inicial
const consentimentoLGPD = reactive({
  aceito: false,
  checkbox: false,
  localStorage: false,  // Controla se já foi aceito nesta sessão
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
    
    return {"status": "ok", "msg": "Consentimento registrado"}
```

#### 2.2.4 Adicionar Tabela ORM

**Arquivo:** `app/infrastructure/orm/models.py`

Tarefa:
```python
class LGPDConsentimento(Base):
    __tablename__ = "lgpd_consentimento"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(50), index=True)
    aceito = Column(Boolean, default=False)
    data_aceito = Column(DateTime, default=datetime.utcnow)
    data_revogacao = Column(DateTime, nullable=True)
    versao_politica = Column(String(10))
    ip_origem = Column(String(15), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
```

**Estimado:** 3-4 horas

---

### 2.3 Página de Política de Privacidade

**Arquivo:** `frontend/politica-privacidade.html`

Tarefa:
1. Criar nova página HTML simples com política LGPD completa
2. Conteúdo esperado:
   - Titulo: "Política de Privacidade — Viagens Labs"
   - Seções:
     - Controlador de Dados
     - Dados Coletados
     - Base Legal
     - Fins do Tratamento
     - Direitos do Titular
     - Tempo de Retenção
     - Procedimento de Exclusão
     - Contato do DPO
     - Última Atualização

3. Adicionar link no footer de `index.html`:
```html
<a href="/politica-privacidade.html" target="_blank" class="text-xs text-gray-400 hover:text-gray-600">
  Política de Privacidade
</a>
```

**Estimado:** 1-2 horas

---

### 2.4 Testes de Fase 2

Tarefa:
1. Criar solicitação de viagem nova
2. Verificar se modal de consentimento aparece
3. Aceitar consentimento
4. Verificar se e-mail de confirmação usa username (não nome)
5. Fazer logout e login novamente
6. Confirmar que modal não aparece por 30 dias

**Estimado:** 1 hora

---

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
