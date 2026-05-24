# Viagens Labs — Handoff Técnico

> Documento de passagem de contexto para desenvolvedores e sessões de IA.  
> Última atualização: **23/05/2026**

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
  ├─ Alguma agência cota ───────────────────────────────────▶ COTACAO_ENVIADA (se faltarem outras ativas)
  └─ Todas as agências marcadas como ativas cotam ──────────▶ PENDENTE_APROVACAO_SETOR_COTACAO

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
viagens_labs/
├── app/
│   ├── main.py                         # Entrypoint FastAPI + migrações seguras e lifespan
│   ├── api/
│   │   ├── dependencies.py             # require_auth, require_setor, require_agencia, require_dev
│   │   └── v1/
│   │       ├── routers.py              # Registro de todos os routers da API
│   │       └── endpoints/
│   │           ├── auth.py             # POST /auth/login (AD)
│   │           ├── viagens.py          # CRUD solicitações do viajante
│   │           ├── aprovacao.py        # GET/POST aprovação por token N1/N2
│   │           ├── agencia.py          # Acesso de agências por token ou credenciais
│   │           ├── setor.py            # API do painel do setor (ações, listagem, agências)
│   │           ├── duffel.py           # Integração de pesquisa de voos Duffel
│   │           ├── dev.py              # API do Portal do Desenvolvedor (logs, QA, config)
│   │           ├── terceiros.py        # [NOVO] Solicitações para Terceiros (termo em PDF)
│   │           ├── hoteis.py           # [NOVO] Proxy seguro Google Places API para hotéis
│   │           └── voucher.py          # Upload de vouchers por token
│   ├── core/
│   │   ├── config.py                   # Configurações Pydantic Settings
│   │   └── security.py                 # JWT encode/decode, senhas hash bcrypt
│   ├── domain/
│   │   └── models/schemas.py           # Schemas Pydantic de requisição e resposta
│   ├── infrastructure/
│   │   ├── database.py                 # SQLAlchemy Engine e SessionLocal
│   │   ├── orm/models.py               # Todos os modelos ORM (PostgreSQL)
│   │   ├── ldap_service.py             # Autenticação AD + fallback mock
│   │   ├── bigquery_service.py         # Busca de dados do viajante + fallback mock
│   │   ├── email_service.py            # Envio SMTP relay (notificações do fluxo completo)
│   │   ├── google_relay_service.py     # Singleton do Apps Script Relay
│   │   └── aprovacao_relay_scheduler.py # Daemon polling: processa GAS ↔ DB
│   └── services/
│       ├── viagens_service.py          # Lógica de criação de solicitações
│       ├── aprovacao_service.py        # Lógica de processamento de N1/N2
│       ├── cotacao_service.py          # [ATUALIZADO] Contagem inteligente de cotações de agências ativas
│       ├── setor_service.py            # [ATUALIZADO] Criação de tokens dinâmicos para agências ativas
│       └── voucher_service.py          # Upload e conclusão com vouchers
├── frontend/
│   ├── index.html                      # Portal do Viajante (SPA em passos, Duffel e Terceiros)
│   ├── portal_aprovacao.html           # Portal de Aprovação N1/N2 via token do e-mail
│   ├── agencia.html                    # Portal da Agência (Cotações e Vouchers via token)
│   ├── setor.html                      # [REESTRUTURADO] Painel do Setor com sidebar vertical e KPIs
│   ├── dev.html                        # Portal do Desenvolvedor com console de logs ao vivo e QA
│   ├── js/lib/                         # [NOVO] CDNs de Vue 3, Tailwind e Fontes salvos localmente (offline total)
│   └── img/
│       └── bg-aviao.jpg                # Imagem de fundo corporativa
├── gas/
│   ├── Code.gs                         # Apps Script Relay (Sheets Fila pública)
│   ├── appsscript.json                 # Permissões do Google Script
│   └── .clasp.json                     # clasp CLI settings
├── service/                            # [NOVO] Wrapper para rodar como Serviço do Windows Server
│   ├── viagenslabs_service.exe
│   └── viagenslabs_service.xml
├── scripts/                            # [NOVO] Scripts de suporte, carga e migrações
│   ├── seed_agencia.py                 # Cadastra agências no DB
│   └── migrate_add_carro_voo_volta.py  # Script pontual de DDL
├── gerenciar_servidor.bat              # [NOVO] Script utilitário em lote de administração de serviços
└── .env.example
```

---

## 7. Pendências e Próximos Passos

### ⚠️ Ação necessária: `setupAgencia()` no GAS
Após o deploy v4, é necessário executar `setupAgencia()` no editor do Google Apps Script para criar as sheets `cotacoes_agencia` e `respostas_agencia`.

1. Acesse https://script.google.com/d/1VqosNh6_Sqv8vr_210MKHp0G5anbZJDmYtIAUw1WnfbPCVWOXtwMI8lY/edit
2. Execute `setupAgencia()` no editor

### Backlog Técnico
| Fase | Item | Status |
|---|---|---|
| 5B | Motor SLA (lembretes de aprovação/cotação atrasados) | Pendente |
| 6A | Portal do Desenvolvedor (`dev.html` e endpoints) | **Concluído e Homologado** |
| 6B | Redesign de Agências (Sem login, acesso exclusivo GAS) | **Concluído e Homologado** |
| 7A | Solicitação para Terceiros (Substituindo Delegação c/ PDF) | **Concluído e Homologado** |
| 7B | UI/UX Premium (Painel Responsivo + Cotações Dinâmicas) | **Concluído e Homologado** |
| 8 | Histórico com linha do tempo no portal do viajante | Pendente |
| 9 | Exportação CSV/Excel + dashboard de gastos | Pendente |
| 10 | Sistema de Auditoria de Acessos & Telemetria do AD | **Concluído e Homologado** |
| 11 | Redesenho Visual Unificado "SaaS Corporativo Premium" | *Planejado (Aprovado)* |

### 🚨 ESTABILIZAÇÃO GERAL E CORREÇÃO DE BUGS (23/05/2026) — 100% RESOLVIDA
Todas as instabilidades recentes e pendências críticas foram resolvidas com absoluto sucesso:
1. **Fim da Tela Preta:** A transição do avião foi mantida nos portais de ponta (viajante e setor), mas os portais técnicos (Dev e Agência) agora navegam de forma limpa via `target="_blank"`, evitando o travamento da tela preta.
2. **Correção de ReferenceError do Vue 3:** Identificamos e renomeamos as propriedades reativas que iniciavam com `_` (como `_toISO`, `_parseDateBR`, `_isoToDisplay` e `_fmtCnpj`), que violavam as restrições de nomes do Vue 3 e quebravam o template. Agora o Portal do Setor e o Viajante carregam de forma instantânea e sem erros de console.
3. **Dynamicização Completa das Agências de Viagem:** Removemos qualquer referência hardcoded a Tastur e Kontrip. O sistema agora lê a lista de agências ativas diretamente do banco. O dashboard do setor exibe KPIs reativos e cores automáticas para cada agência ativa, e os botões de ação e escolha no detalhe da viagem são renderizados dinamicamente sob demanda.
4. **Acoplamento de Status Inteligente:** No backend (`cotacao_service.py`), a transição para aprovação do setor agora aguarda a resposta exata de todas as agências registradas com o flag `ativo = True` (ou fallback padrão de 2 se o banco de dados de agências estiver limpo).
5. **Logs do Sistema (Console Hacker):** Desenvolvemos um console estilo terminal hacker premium escuro com atualização em tempo real de 3s para monitoramento de logs de FastAPI e Nginx.
6. **Mocks de BigQuery & LDAP:** O sistema agora cai automaticamente em mocks robustos offline caso o BigQuery ou o LDAP (gcloud ADC local ou rede intranet) falhem, permitindo desenvolvimento contínuo e estável sem conectividade com a rede corporativa.
7. **Database Migrations em PostgreSQL:** Corrigimos os erros de sintaxe SQLite no script de migração segura (`app/main.py`), permitindo a compatibilidade fluida com PostgreSQL em produção (criação agnóstica via SQLAlchemy `create_all()`).
8. **Segurança Aprimorada (Hotéis):** A chave do Google Places API foi retirada do front-end e isolada no backend (`/api/v1/hoteis/sugestoes`), consultando via proxy seguro de forma transparente.
9. **Independência de Rede (CDNs Offline):** Vue 3 CDN, TailwindCSS CDN e fontes Inter foram empacotadas no diretório local `frontend/js/lib/` para permitir que o sistema funcione de forma 100% offline em redes de intranet fechadas.
10. **Windows Service & gerenciar_servidor.bat:** Embalagem e scripts bat utilitários para instalar e gerenciar o FastAPI como serviço estável de segundo plano no Windows Server.

---

## 8. Padrões de Código

| Aspecto | Convenção |
|---|---|
| Idioma do código | Inglês (variáveis, funções, classes) |
| Idioma dos comentários | Português |
| Regra de geração IA | **NUNCA** use `...`, `# ...` ou `#existing code` — sempre código completo |
| Migrations | `ALTER TABLE … ADD COLUMN IF NOT EXISTS` ou `create_all()` no startup |
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
| `d778e77` | CRUD de agências no painel do setor + sidebar nav vertical |
| `90d232a` | feat: dynamicizacao de agencias, telemetria de logs, mocks BigQuery e correcoes Vue 3 |
| `15cabd1` | Merge branch 'main' de viagens_labs (integração remota) |
| `28c393c` | feat: implementado monitoramento unificado, middleware e telemetria operacional |
| *(atual)* | Redesenho visual unificado SaaS premium e consolidação de layouts |

---

## 10. Contatos

| Papel | Nome | Contato |
|---|---|---|
| Dev & Arquitetura | Leandro Araújo | leandro.araujo@luizalabs.com |
| Setor de Viagens | Rubia Paim | rubia.paim@luizalabs.com |
| E-mail do sistema | Viagens Labs | viagenslabs@luizalabs.com |

---

## 11. Sistema Unificado de Auditoria de Acessos, Middleware & Telemetria

Na atualização de **24/05/2026**, foi introduzido um sistema de auditoria global de altíssima resiliência e impacto de performance nulo:

### A. Banco de Dados e Modelos
* **Tabela `log_acessos` (`LogAcessoModel`):** Tabela 100% desacoplada sem chaves estrangeiras. Contém colunas `id`, `username`, `nome`, `perfil`, `ip_origem`, `status_acesso` (`SUCESSO` | `BLOQUEADO`), `observacao` e `data_criacao`.
* **Indexação Avançada:** Índices definidos nas colunas `username` e `data_criacao` para garantir respostas sub-milisegundo em queries de telemetria e KPIs.

### B. Middleware Global de Navegação (FastAPI)
* **Auditoria de Requisições:** Intercepta requisições de API (`/api/v1/`), extrai o token JWT silenciosamente em memória e gera logs ricos de console em tempo real.
* **Resiliência Ativa:** Qualquer falha na decodificação ou leitura do token é tratada de forma silenciosa para nunca interromper o carregamento da requisição do usuário.

### C. Autenticação e Logins Resilientes (`/login`)
* **Persistência de Conexões:** O endpoint `/login` agora recebe `request: Request` para capturar o IP real do cliente.
* **Logins Seguros e Tratamento de Falhas:** Tentativas de login bem-sucedidas ou bloqueadas por grupos inválidos do AD/erros de rede são gravadas na tabela de logs de forma resiliente. Qualquer erro no banco de dados SQLite nunca impedirá o login do viajante.

### D. Endpoints de Telemetria e Interfaces
* **GET `/dev/logs-acesso`:** Últimos 100 acessos integrados reativamente com polling de 5 segundos no Portal Dev.
* **GET `/setor/stats` & GET `/setor/alertas-acesso`:** KPI "Ativos Hoje" na dashboard do setor e widget de "Alertas de Onboarding (Acesso AD)" na aba de terceiros com polling automático de 8 segundos, agilizando liberações de colaboradores barrados no Active Directory.
