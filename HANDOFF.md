# Viagens Labs — Handoff Técnico

> Documento de passagem de contexto para desenvolvedores e sessões de IA.  
> Última atualização: **22/05/2026**

---

## 1. Identidade do Projeto

| Campo | Valor |
|---|---|
| Nome | **Viagens Labs** |
| Repositório | https://github.com/leandroaraujo-max/viagens_labs |
| Branch principal | `main` |
| Workspace local | `C:\Projetos\viagens_labs\` |
| Backend | FastAPI + Python 3.14 + Uvicorn (porta 8000) |
| Frontend | Vue.js 3 CDN + TailwindCSS CDN (porta 80 via Nginx) |
| Banco | PostgreSQL 5433, DB `solicitacao_viagens` |

---

## 2. Como rodar

```powershell
# Backend (em C:\Projetos\viagens_labs)
$env:PYTHONPATH="."; .\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Nginx (frontend)
nginx.exe -c C:\Projetos\viagens_labs\nginx_config\nginx.conf

# GAS (quando alterar Code.gs)
cd gas
clasp push --force
clasp deploy --description "Viagens Labs relay vX - descrição"
# Atualizar GAS_RELAY_URL no .env com a nova URL do deploy
# No editor GAS: executar setupAgencia() se for a primeira vez
```

---

## 3. Variáveis de Ambiente (`.env`)

```dotenv
DATABASE_URL=postgresql://postgres:Magazine%40123@127.0.0.1:5433/solicitacao_viagens?client_encoding=utf8
DUFFEL_TOKEN=duffel_test_1MmtcmUYHK0-...

# Agências
AGENCIA_TASTUR_EMAIL=leandro.araujo@luizalabs.com
AGENCIA_KONTRIP_EMAIL=leandro.araujo@luizalabs.com

# Fallback (sem GAS)
BASE_URL_AGENCIA=http://viagenslabs.magazineluiza.intranet
BASE_URL_APROVACAO=http://viagenslabs.magazineluiza.intranet

# GAS Relay (substitui os dois acima quando configurado)
GAS_RELAY_URL=https://script.google.com/macros/s/AKfycbykFk0vwKSe2tRcdcFY5Tm8Gt7udb_bcued1qwAQl4XOSpqjJySiga6lTRZ8NKrbT1xKQ/exec
GAS_SECRET=vl-secret-2026
GAS_POLL_INTERVALO=60

# QA
QA_APROVADOR_EMAIL=leandro.araujo@luizalabs.com
```

---

## 4. Google Apps Script Relay

| Campo | Valor |
|---|---|
| Script ID | `1VqosNh6_Sqv8vr_210MKHp0G5anbZJDmYtIAUw1WnfbPCVWOXtwMI8lY` |
| Deploy ativo | **v4** |
| URL v4 | `https://script.google.com/macros/s/AKfycbykFk0vwKSe2tRcdcFY5Tm8Gt7udb_bcued1qwAQl4XOSpqjJySiga6lTRZ8NKrbT1xKQ/exec` |
| Planilha | ID: `1o5PBNWpv9y89EVyCIXjNtuQx27Mcn0gIKPlUU_KQrrU` |
| Script Property | `GAS_SECRET = vl-secret-2026` |
| Conta clasp | `leandro.araujo@luizalabs.com` |

### Sheets da planilha GAS
| Sheet | Criada por | Uso |
|---|---|---|
| `pendentes` | `setup()` | Tokens de aprovação N1/N2 aguardando decisão |
| `decisoes` | `setup()` | Decisões submetidas pelos aprovadores |
| `cotacoes_agencia` | `setupAgencia()` | Tokens de cotação para Tastur/Kontrip |
| `respostas_agencia` | `setupAgencia()` | Cotações submetidas pelas agências |

### Endpoints GAS
| Método | Parâmetro | Descrição |
|---|---|---|
| `GET` | `?token=UUID` | Portal de aprovação HTML (N1/N2) |
| `GET` | `?agencia_token=UUID` | Portal de cotação HTML (agências) |
| `POST` | `{action:"registrar"}` | FastAPI registra aprovação pendente |
| `POST` | `{action:"poll"}` | FastAPI busca decisões |
| `POST` | `{action:"processar"}` | FastAPI marca decisão processada |
| `POST` | `{action:"registrar_agencia"}` | FastAPI registra token de cotação |
| `POST` | `{action:"poll_cotacoes"}` | FastAPI busca cotações submetidas |
| `POST` | `{action:"processar_cotacao"}` | FastAPI marca cotação processada |

### Arquitetura do relay
```
FastAPI (intranet)
  │  setor pré-aprova → registrar_agencia(tok_tastur, sol) + registrar_agencia(tok_kontrip, sol)
  │  aprovacao_service → registrar_aprovacao(token_model, sol)
  │
  ▼ POST para GAS_RELAY_URL
Google Apps Script (público — google.com)
  │  Armazena em Google Sheets
  │  Serve portal HTML para aprovadores / agências
  │  Recebe submitDecision() / submitCotacao() via google.script.run
  │
  ▲ polling cada 60s (aprovacao_relay_scheduler.py)
FastAPI scheduler
  │  poll_decisoes() → AprovacaoService.processar_resposta()
  └─ poll_cotacoes() → ViagensService.registrar_cotacao_agencia()
```

---

## 5. Fluxo de Status Completo

```
Viajante cria solicitação
       │
       ▼
AGUARDANDO_N1
  ├─ N1 de férias (BigQuery) ──────────────────────────────▶ AGUARDANDO_N2
  ├─ N1 reprova ────────────────────────────────────────────▶ REPROVADA
  └─ N1 aprova ──────────────────────────────────────────── ▼
                                                   PENDENTE_PRE_APROVACAO_SETOR
AGUARDANDO_N2                                              │
  ├─ N2 reprova ────────────────────────────────────────────▶ REPROVADA
  └─ N2 aprova ─────────────────────────────────────────────▶ mesmo destino ▲

PENDENTE_PRE_APROVACAO_SETOR
  ├─ Setor reprova ─────────────────────────────────────────▶ REPROVADA
  └─ Setor pré-aprova:
       cria tokens COTACAO (Tastur + Kontrip, TTL 7d)
       registra tokens no GAS relay
       envia e-mails com link GAS?agencia_token=UUID
       │
       ▼
AGUARDANDO_COTACAO
  ├─ 1ª agência cota ───────────────────────────────────────▶ COTACAO_ENVIADA
  └─ 2ª agência cota ───────────────────────────────────────▶ PENDENTE_APROVACAO_SETOR_COTACAO

PENDENTE_APROVACAO_SETOR_COTACAO
  ├─ Setor reprova ─────────────────────────────────────────▶ REPROVADA
  └─ Setor escolhe vencedora:
       cria token VOUCHER (vencedora, TTL 14d)
       envia e-mails: vencedora / perdedora / viajante
       │
       ▼
APROVADA_AGUARDANDO_VOUCHER
  └─ Todos vouchers entregues ──────────────────────────────▶ CONCLUIDA
                                                              (e-mail ao viajante)
```

**Regra N2:** Apenas como escalação — N1 de férias (BigQuery) OU N1 não responde no SLA. Nunca obrigatório no fluxo normal.

---

## 6. Estrutura dos Arquivos Principais

```
app/
├── main.py                              # Lifespan: migrações + schedulers (SLA + GAS relay)
├── api/v1/endpoints/
│   ├── auth.py                          # POST /auth/login (AD + agência bcrypt)
│   ├── viagens.py                       # CRUD solicitações (viajante)
│   ├── aprovacao.py                     # GET/POST por token (N1/N2, sem auth)
│   ├── agencia.py                       # Login + token cotação/voucher (agências)
│   ├── setor.py                         # Painel do setor (CRUD + ações)
│   ├── duffel.py                        # Pesquisa de voos Duffel
│   └── voucher.py                       # Upload de vouchers
├── services/
│   ├── viagens_service.py               # Criação de solicitações + registrar_cotacao_agencia
│   ├── aprovacao_service.py             # N1/N2: iniciar + processar (inclui GAS relay)
│   ├── setor_service.py                 # _pre_aprovar: cria tokens + registra no GAS
│   ├── cotacao_service.py               # Registra cotação por token de agência
│   └── voucher_service.py               # Upload + verificação de conclusão
├── infrastructure/
│   ├── google_relay_service.py          # Singleton: integra FastAPI ↔ GAS
│   │   ├── registrar_aprovacao()        # N1/N2 → GAS
│   │   ├── registrar_agencia()          # Token cotação → GAS
│   │   ├── poll_decisoes()              # GAS → decisões de aprovação
│   │   ├── poll_cotacoes()              # GAS → cotações de agências
│   │   ├── marcar_processado()          # Marca decisão processada no GAS
│   │   ├── marcar_cotacao_processada()  # Marca cotação processada no GAS
│   │   ├── link_aprovacao()             # URL GAS ou fallback intranet
│   │   └── link_agencia()              # URL GAS ou fallback intranet
│   ├── aprovacao_relay_scheduler.py     # Thread daemon: poll GAS + processa
│   │   ├── _processar_ciclo()           # Aprovações N1/N2
│   │   └── _processar_ciclo_agencia()   # Cotações de agências
│   ├── email_service.py                 # 12+ templates SMTP; usa link_agencia() quando GAS ativo
│   ├── ldap_service.py                  # Autenticação AD
│   ├── bigquery_service.py              # Hierarquia + situação do colaborador
│   └── orm/models.py                    # Todos os modelos ORM
gas/
├── Code.gs                              # GAS Web App (aprovações + cotações agência)
├── appsscript.json                      # Permissões e configurações do GAS
└── .clasp.json                          # Script ID para clasp CLI
```

---

## 7. Pendências e Próximos Passos

### ⚠️ Ação necessária: `setupAgencia()` no GAS
Após o deploy v4, é necessário executar `setupAgencia()` no editor do Google Apps Script para criar as sheets `cotacoes_agencia` e `respostas_agencia`.

1. Acesse https://script.google.com/d/1VqosNh6_Sqv8vr_210MKHp0G5anbZJDmYtIAUw1WnfbPCVWOXtwMI8lY/edit
2. Execute `setupAgencia()` no editor

### ⚠️ Tokens presos (antigos, antes do GAS relay de agências)
3 tokens em `tokens_agencia` com links intranet inacessíveis:
- `6cb43680-e60f-4b3f-a630-6fb3fb09f6a8`
- `2d0c8483-a18f-44dc-bd59-70033f130152`
- `5b5a666b-93ed-4632-92d2-6f92075a74dc`

Para recriar via `_pre_aprovar()` do setor (ação `PRE_APROVAR` na solicitação → novos tokens GAS são criados automaticamente), ou usar o endpoint de reenvio.

### Backlog Técnico
| Fase | Item | Status |
|---|---|---|
| 5B | Motor SLA (lembretes de aprovação/cotação atrasados) | Pendente |
| 5C | Casamento de viagens no painel do setor | Pendente |
| 5D | GAS relay aprovações + cotações agências | **Concluído** |
| 6 | Histórico com linha do tempo no portal do viajante | Pendente |
| 7 | GAS relay para vouchers (upload via Google Drive) | Pendente |
| 8 | Exportação CSV/Excel + dashboard de gastos | Pendente |
| 9 | Testes `pytest` + NSSM + rotação de logs | Pendente |

---

## 8. Padrões de Código

| Aspecto | Convenção |
|---|---|
| Idioma do código | Inglês (variáveis, funções, classes) |
| Idioma dos comentários | Português |
| Regra de geração IA | **NUNCA** use `...`, `# ...` ou `#existing code` — sempre código completo |
| Migrations | `ALTER TABLE … ADD COLUMN IF NOT EXISTS` em `app/main.py` |
| Imports circulares | Resolvidos com lazy import dentro das funções quando necessário |
| Error handling | Log + continuação (não deixar scheduler morrer por 1 falha) |

---

## 9. Commits Relevantes

| Hash | Descrição |
|---|---|
| `27e5249` | Setup inicial da arquitetura |
| `b3ea37e` | Portal de aprovação GAS + relay Python |
| `37200c3` | Nome corrigido "Viagens Labs"; GAS_SECRET |
| `4e303a6` | clasp push + deploy v3 |
| `88c8a61` | Frontend: seção voo de volta + hint botão Avançar |
| `139b9b9` | Fluxo aprovação: N2 apenas como escalação |
| *(atual)* | GAS relay para cotações de agências (deploy v4) |

---

## 10. Contatos

| Papel | Nome | Contato |
|---|---|---|
| Dev & Arquitetura | Leandro Araújo | leandro.araujo@luizalabs.com |
| Setor de Viagens | Rubia Paim | rubia.paim@luizalabs.com |
| E-mail do sistema | Viagens Labs | viagenslabs@luizalabs.com |
