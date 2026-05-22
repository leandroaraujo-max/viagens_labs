# ✈️ ViagensLabs — Portal Corporativo de Viagens

> Sistema on-premises de solicitação, aprovação e cotação de viagens corporativas do Luizalabs/Magalu.  
> Migração completa do legado em Google Apps Script (GAS) para FastAPI + PostgreSQL + Vue.js 3 + Active Directory.

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Demonstração e Funcionalidades](#-demonstração-e-funcionalidades)
3. [Pré-requisitos](#-pré-requisitos)
4. [Instalação e Configuração](#-instalação-e-configuração)
5. [Como Usar](#-como-usar)
6. [Arquitetura](#-arquitetura)
7. [Estrutura de Pastas](#-estrutura-de-pastas)
8. [Banco de Dados e Modelos](#-banco-de-dados-e-modelos)
9. [Fluxo de Status da Solicitação](#-fluxo-de-status-da-solicitação)
10. [Autenticação e Perfis de Acesso](#-autenticação-e-perfis-de-acesso)
11. [API — Endpoints](#-api--endpoints)
12. [Frontend — Portais](#-frontend--portais)
13. [Notificações por E-mail](#-notificações-por-e-mail)
14. [Estado Atual e Próximos Passos](#-estado-atual-e-próximos-passos)
15. [Como Contribuir](#-como-contribuir)
16. [Licença e Contato](#-licença-e-contato)

---

## 🎯 Visão Geral

O **ViagensLabs** é um sistema corporativo completo que gerencia o ciclo de vida de uma solicitação de viagem corporativa:

```
Viajante solicita  →  N1 aprova  →  N2 aprova (se aplicável)
    →  Setor pré-aprova  →  Agências cotam  →  Setor escolhe agência vencedora  →  Concluído
```

**Portais:**
| Portal | URL | Público |
|---|---|---|
| Portal do Viajante | `/index.html` | Colaboradores Magalu (AD) |
| Portal de Aprovação | `/portal_aprovacao.html?token=...` | Gestores N1/N2 (link por e-mail) |
| Portal da Agência | `/agencia.html` | Agências de viagem parceiras (Tastur, Kontrip) |
| Painel do Setor | `/painel.html` | Equipe interna de viagens (AD — grupo admins) |

---

## ✨ Demonstração e Funcionalidades

### Capturas de Tela

| Portal do Viajante | Painel do Setor |
|:---:|:---:|
| Login com credenciais AD + foto aérea de fundo | Tabela de solicitações com filtros e KPIs |
| Formulário multi-passo (viajante, rota, preferências) | Modal comparativo de cotações Tastur vs Kontrip |

### Funcionalidades por Perfil

**Viajante (colaborador Magalu)**
- 🔐 Login com usuário e senha da rede corporativa (AD)
- 🔍 Busca de dados do colaborador via Google BigQuery (nome, cargo, filial, gestor N1)
- ✈️ Solicitação de viagem com múltiplos serviços: aéreo, hotel, rodoviário, carro
- 📋 Tipos de viagem: individual, em conjunto (mesma rota) ou delegação (para outro colaborador)
- ⚡ Detecção automática de viagem emergencial (< 15 dias de antecedência)
- 📎 Preferências de voo e observações por serviço
- 📊 Histórico de solicitações com status em tempo real

**Gestor N1 / N2 (aprovação por e-mail)**
- 📧 Recebe link de aprovação com token único e prazo de validade
- ✅ Aprova ou reprova sem necessidade de login no sistema
- 💬 Campo de observação obrigatório na reprovação
- 🔒 Link de uso único — não pode ser reutilizado após decisão

**Agência (Tastur / Kontrip)**
- 🔐 Login exclusivo com credenciais cadastradas no sistema
- 📥 Visualiza solicitações aguardando cotação
- 💰 Envia cotação detalhada por serviço (voo, hotel, carro, rodoviário)
- 🔄 Pode atualizar cotação enquanto o setor não decidiu

**Setor de Viagens (admin)**
- 🗂️ Painel com todas as solicitações, filtráveis por status, período, agência e busca
- ⚡ Ações rápidas: pré-aprovar, reprovar, reenviar e-mail para agências
- ⚖️ Comparativo lado a lado das cotações das duas agências
- 🏆 Seleção da agência vencedora com notificação automática
- 📈 Indicadores: 9 KPIs + gráficos de distribuição e volume mensal

---

## 🔧 Pré-requisitos

| Requisito | Versão | Observação |
|---|---|---|
| Python | 3.12+ | Testado com 3.14 |
| PostgreSQL | 14+ | Porta `5433` |
| Nginx | 1.24+ | Windows |
| Git | qualquer | — |
| Google Cloud SDK | qualquer | Para BigQuery (ADC) |
| Acesso ao AD Magalu | — | `ldap3` via intranet |

> **Nota:** O sistema foi projetado para rodar on-premises na intranet da Magalu. A integração com BigQuery e AD exige conectividade com a infraestrutura interna.

O projeto foi refatorado do zero adotando o padrão **Clean Architecture**, visando testabilidade, independência de frameworks e alta coesão das regras de negócio corporativas (Luizalabs/Magalu).

*   **Front-end:** Single Page Application (SPA) usando **HTML5, Vue.js 3 (via CDN) e TailwindCSS**. Interface imersiva (glassmorphism) e aderente ao brandbook do Luizalabs (foco em minimalismo, azul sóbrio e sem o amarelo de varejo). O código está em um único arquivo `frontend/index.html`.
*   **Web Server (Reverse Proxy):** **Nginx** no Windows Server, servindo o front-end estático na porta 80 e roteando requisições `/api/*` para o Uvicorn (backend Python).

```
┌─────────────────────────────────────────────────────┐
│  Navegador (intranet)                               │
│    ↕ HTTP :80                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │  NGINX (Windows)                             │   │
│  │  /          → frontend/ (arquivos estáticos) │   │
│  │  /api/*     → proxy → Uvicorn :8000          │   │
│  └───────────────────────┬──────────────────────┘   │
│                          ↓                          │
│  ┌───────────────────────────────────────────────┐  │
│  │  FastAPI / Uvicorn (Python 3.14, venv)        │  │
│  │  app/api       → Routers + Endpoints          │  │
│  │  app/core      → Config, Segurança, JWT       │  │
│  │  app/domain    → Schemas Pydantic             │  │
│  │  app/services  → Regras de negócio            │  │
│  │  app/infra     → DB, AD, BigQuery, E-mail     │  │
│  └──────┬─────────────────┬────────────────┬─────┘  │
│         ↓                 ↓                ↓        │
│  PostgreSQL :5433   AD/LDAP Magalu   Google BQ      │
└─────────────────────────────────────────────────────┘
```

**Stack:**
| Camada | Tecnologia |
|---|---|
| Servidor web | Nginx (Windows) na porta 80 |
| Backend | Python 3.14, FastAPI, Uvicorn |
| ORM / Banco | SQLAlchemy + PostgreSQL 5433 |
| Autenticação AD | `ldap3` → `ldap://ML-ASC-AD-01.magazineluiza.intranet` |
| Autenticação Agência | bcrypt + PostgreSQL |
| JWT | HS256, validade 8h |
| BigQuery | `google-cloud-bigquery` + ADC |
| E-mail | `smtplib` → `smtpml.magazineluiza.intranet:25` |
| Frontend | Vue.js 3 CDN + TailwindCSS CDN (sem build step) |
| Design System | Inter font, glassmorphism, paleta `labs` (azul `#0055ff`) |
| Imagem de fundo | Foto aérea servida localmente em `/img/bg-aviao.jpg` |

---

## 📁 Estrutura de Pastas

```
viagens_labs/
├── app/
│   ├── main.py                         # Entrypoint FastAPI + migrações seguras
│   ├── api/
│   │   ├── dependencies.py             # require_auth, require_setor, require_agencia
│   │   └── v1/
│   │       ├── routers.py              # Registro de todos os routers
│   │       └── endpoints/
│   │           ├── auth.py             # POST /auth/login
│   │           ├── viagens.py          # CRUD de solicitações (viajante)
│   │           ├── aprovacao.py        # GET/POST aprovação por token (N1/N2)
│   │           ├── agencia.py          # Login + cotação (agências)
│   │           ├── setor.py            # Painel do setor (CRUD + ações)
│   │           └── duffel.py           # Integração Duffel (pesquisa de voos)
│   ├── core/
│   │   ├── config.py                   # Settings (Pydantic BaseSettings)
│   │   └── security.py                 # JWT encode/decode, bcrypt
│   ├── domain/
│   │   └── models/schemas.py           # Todos os schemas Pydantic
│   ├── infrastructure/
│   │   ├── database.py                 # Engine SQLAlchemy + SessionLocal
│   │   ├── orm/models.py               # Modelos ORM (tabelas)
│   │   ├── ldap_service.py             # Autenticação AD + verificação de grupos
│   │   ├── bigquery_service.py         # Consulta hierarquia do colaborador
│   │   ├── email_service.py            # SMTP relay corporativo (5 templates)
│   │   └── duffel_service.py           # API Duffel para pesquisa de voos reais
│   ├── repositories/
│   │   └── viagens_repository.py       # Acesso ao banco (queries SQLAlchemy)
│   └── services/
│       ├── viagens_service.py          # Lógica de criação de solicitações
│       ├── aprovacao_service.py        # Lógica de aprovação N1/N2
│       ├── cotacao_service.py          # Lógica de cotação das agências
│       ├── casamento_service.py        # Deduplica viagens com mesmo trecho
│       └── setor_service.py            # Painel do setor — listagem e ações
├── frontend/
│   ├── index.html                      # Portal do Viajante (SPA principal)
│   ├── portal_aprovacao.html           # Portal de Aprovação N1/N2 (link por e-mail)
│   ├── agencia.html                    # Portal da Agência (Tastur / Kontrip)
│   ├── painel.html                     # Painel do Setor de Viagens
│   └── img/
│       └── bg-aviao.jpg                # Foto aérea de fundo (servida localmente)
├── seed_agencia.py                     # Script para criar usuários de agência no BD
├── .env.example                        # Modelo de variáveis de ambiente
├── .gitignore
└── README.md
```

---

## 🗄️ Banco de Dados e Modelos

**Banco:** PostgreSQL na porta `5433`, schema `solicitacao_viagens`

### Tabela `solicitacoes`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `protocolo` | String | Ex: `VL-20260522-0001` |
| `solicitante_username` | String | Login AD do solicitante |
| `solicitante_email` | String | E-mail corporativo |
| `tipo_viagem` | String | `Para mim`, `Conjunto`, `Delegação` |
| `viajantes_adicionais` | JSON | Lista de viajantes extras |
| `origem_cidade` | String | Cidade de origem |
| `destino_cidade` / `destino_estado` | String | Destino |
| `data_ida` / `data_volta` | Date | Datas da viagem |
| `tipo_servico` | String | `aereo,hotel,carro,rodov` (CSV) |
| `motivo_viagem` | Text | Justificativa |
| `classificacao` | String | `Comum` ou `Emergencial` (< 15 dias) |
| `preferencia_voo` | Text | Preferências de voo informadas |
| `status` | String | Estado atual do fluxo |
| `agencia_vencedora` | String | `Tastur` ou `Kontrip` (após decisão) |
| `created_at` | DateTime | Timestamp de criação |

### Tabela `aprovacoes`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | Integer PK | — |
| `solicitacao_id` | FK | Referência à solicitação |
| `nivel` | String | `N1` ou `N2` |
| `email_aprovador` | String | E-mail do gestor |
| `token` | String unique | Token UUID do link de aprovação |
| `status_token` | String | `PENDENTE`, `APROVADO`, `REPROVADO`, `EXPIRADO` |
| `observacao` | Text | Observação do aprovador |
| `respondido_em` | DateTime | Timestamp da resposta |
| `expira_em` | DateTime | Prazo de validade do link |

### Tabela `cotacoes`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | Integer PK | — |
| `solicitacao_id` | FK + index | Suporta 2 cotações por solicitação (Tastur + Kontrip) |
| `agencia_nome` | String | `Tastur` ou `Kontrip` |
| `aereo_companhia` / `aereo_valor` | String / Numeric | Dados do voo cotado |
| `hotel_nome` / `hotel_valor_diaria` | String / Numeric | Dados do hotel cotado |
| `rodov_empresa` / `rodov_valor` | String / Numeric | Dados rodoviários |
| `carro_locadora` / `carro_valor_diaria` | String / Numeric | Dados de carro |
| `valor_total` | Numeric | Valor total da cotação |
| `observacoes` | Text | Observações da agência |
| `criado_em` | DateTime | — |

### Tabela `agencias_usuarios`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | Integer PK | — |
| `username` | String unique | Login da agência |
| `agencia_nome` | String | `Tastur` ou `Kontrip` |
| `hashed_password` | String | bcrypt hash |
| `ativo` | Boolean | Habilita/desabilita acesso |

> **Migrações seguras:** O `app/main.py` roda `_migracoes_seguras()` no startup que executa `ALTER TABLE … ADD COLUMN IF NOT EXISTS` e `DROP CONSTRAINT IF EXISTS` — sem necessidade de Alembic.

---

## 🔄 Fluxo de Status da Solicitação

```
[Viajante cria]
       │
       ▼
AGUARDANDO_N1  ──(reprovado)──▶  REPROVADA
       │
    (aprovado)
       │
       ▼
AGUARDANDO_N2  ──(reprovado)──▶  REPROVADA
  (se aplicável)
       │
    (aprovado ou emergencial)
       │
       ▼
PENDENTE_PRE_APROVACAO_SETOR  ──(setor reprova)──▶  REPROVADA
       │
    (setor pré-aprova)
       │
       ▼
AGUARDANDO_COTACAO  ──── e-mail enviado para Tastur + Kontrip
       │
    (agência envia cotação)
       │
       ▼
COTACAO_ENVIADA  ─── (2ª agência envia)
       │
       ▼
PENDENTE_APROVACAO_SETOR_COTACAO  ──(setor reprova)──▶  REPROVADA
       │
    (setor escolhe Tastur ou Kontrip)
       │
       ▼
CONCLUIDA
```

**Regra emergencial:** Solicitações com `data_ida` em menos de 15 dias pulam as aprovações N1/N2 e vão direto para `PENDENTE_PRE_APROVACAO_SETOR`.

---

## 🔐 Autenticação e Perfis de Acesso

### Servidores AD (ordem de tentativa)
```
ldap://ML-ASC-AD-01.magazineluiza.intranet
ldap://ML-ASC-AD2.magazineluiza.intranet
ldap://ML-HB-AD01.magazineluiza.intranet
```
- **Domain prefix:** `MAGAZINELUIZA`
- **Base DN:** `DC=magazineluiza,DC=intranet`

### Grupos AD e perfis
| Grupo AD | Perfil retornado | Acesso |
|---|---|---|
| `G_ACCESS_VIAGENSLABS_ADMINS` | `setor` | Redireciona para `/painel.html` |
| `G_ACCESS_VIAGENSLABS_AGENCIAS` | `agencia_ad` | Reservado (VPN+AD futuro) |
| *(qualquer outro colaborador)* | `viajante` | Portal principal `/index.html` |

### Agências (PostgreSQL)
Login via `POST /api/v1/agencia/login` com bcrypt. Perfil `agencia` no JWT.  
Seed inicial: `python seed_agencia.py`

### JWT
- Algoritmo: HS256 — Expiração: 8 horas
- Payload: `{ "sub": "<username>", "perfil": "<perfil>" }`

---

## 🌐 API — Endpoints

### Auth
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Login AD ou Agência → retorna JWT |

### Viagens (Viajante autenticado)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/viagens/` | Cria nova solicitação |
| `GET` | `/api/v1/viagens/minhas` | Lista solicitações do usuário logado |
| `GET` | `/api/v1/viagens/{id}` | Detalhe de uma solicitação |
| `GET` | `/api/v1/viagens/colaborador/{id}` | Busca dados do colaborador no BigQuery |

### Aprovação (link por e-mail — sem auth)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/aprovacao/{token}` | Carrega dados do token de aprovação |
| `POST` | `/api/v1/aprovacao/{token}` | Submete decisão (aprovar/reprovar) |

### Agência
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/agencia/login` | Login da agência |
| `GET` | `/api/v1/agencia/solicitacoes` | Lista solicitações em `AGUARDANDO_COTACAO` |
| `POST` | `/api/v1/agencia/solicitacoes/{id}/cotacao` | Envia ou atualiza cotação |

### Setor (requer perfil `setor`)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/setor/solicitacoes` | Lista com filtros (status, período, agência, busca) |
| `GET` | `/api/v1/setor/solicitacoes/{id}` | Detalhe + cotações das duas agências |
| `POST` | `/api/v1/setor/solicitacoes/{id}/acao` | Executa ação: `PRE_APROVAR`, `PRE_REPROVAR`, `APROVAR_TASTUR`, `APROVAR_KONTRIP`, `REPROVAR`, `REENVIAR_AGENCIAS` |

### Duffel (pesquisa de voos — experimental)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/duffel/pesquisar` | Pesquisa voos via API Duffel |

---

## 🖥️ Frontend — Portais

Todos os portais usam **Vue.js 3 (CDN) + TailwindCSS (CDN)** — sem node_modules, sem build step.

### Design System
- **Fonte:** Inter (Google Fonts)
- **Fundo:** Foto aérea servida localmente (`/img/bg-aviao.jpg`) com overlay escuro
- **Cards:** Glassmorphism — `background: rgba(255,255,255,0.95-0.97)` + `backdrop-filter: blur`
- **Cor primária:** `#0055ff` (labs.blue)
- **Cor dark:** `#0f172a` (labs.dark)

### Portal do Viajante (`index.html`)
- Tela de login com AD
- Após login com perfil `setor` → redireciona automaticamente para `/painel.html`
- Formulário de solicitação em passos:
  1. Identificação do viajante (busca BigQuery por matrícula/CPF)
  2. Dados da viagem (origem, destino, datas, serviços, preferências de voo)
  3. Confirmação e envio
- Aba "Minhas Solicitações" com histórico e status
- Header com badge de perfil e botão "Painel do Setor" (visível só para perfil `setor`)

### Portal de Aprovação (`portal_aprovacao.html`)
- Acessado via link enviado por e-mail (`?token=UUID`)
- Estados tratados: carregando, erro, já respondido, expirado, aguardando
- Exibe todos os dados da viagem
- Botões de Aprovar / Reprovar com campo de observação

### Portal da Agência (`agencia.html`)
- Login com usuário/senha específico da agência
- Lista solicitações aguardando cotação
- Formulário de cotação por serviço (aéreo, hotel, rodoviário, carro)
- Suporta 2 cotações simultâneas para a mesma solicitação (Tastur + Kontrip)

### Painel do Setor (`painel.html`)
- Requer perfil `setor` (verificado no `onMounted` via `localStorage`)
- **Aba Solicitações:** tabela com filtros por status, período, agência e busca livre
- **Ações rápidas por status:**
  - `PENDENTE_PRE_APROVACAO_SETOR` → Pré-Aprovar / Reprovar
  - `AGUARDANDO_COTACAO` → Reenviar e-mail para agências
  - `PENDENTE_APROVACAO_SETOR_COTACAO` → Modal comparativo de cotações (escolher Tastur ou Kontrip)
- **Modal de Detalhe:** dados completos + cotações lado a lado com highlight do vencedor
- **Aba Indicadores:** 9 KPIs + gráfico de distribuição por status + volume mensal (últimos 6 meses)

---

## 📧 Notificações por E-mail

**SMTP:** `smtpml.magazineluiza.intranet:25`  
**De:** `vagenslabs@luizalabs.com`  
**Reply-To:** `rubia.paim@luizalabs.com`

| Template | Disparado quando | Destinatário |
|---|---|---|
| Aprovação N1 | Solicitação criada com sucesso | Gestor N1 (BigQuery) |
| Aprovação N2 | N1 aprova | Gestor N2 (BigQuery) |
| Setor — pré-aprovação | N1 ou N2 aprova (emergencial ou comum) | `vagenslabs@luizalabs.com` |
| Agências — cotação | Setor pré-aprova | Tastur + Kontrip (config) |
| Setor — comparativo | 2ª agência envia cotação | `vagenslabs@luizalabs.com` |
| Agência vencedora | Setor escolhe agência | Agência escolhida |

---

## 📊 Estado Atual e Próximos Passos

### ✅ Implementado e Funcional

**Infraestrutura**
- [x] Clean Architecture completa (api / core / domain / infrastructure / services / repositories)
- [x] PostgreSQL com SQLAlchemy ORM + migrações automáticas no startup
- [x] Nginx servindo frontend estático + proxy reverso para a API
- [x] Imagem de fundo servida localmente (sem dependência de CDN externo)

**Autenticação**
- [x] Login AD (ldap3) com verificação de grupo para perfil (setor / viajante)
- [x] Login de agências via bcrypt + PostgreSQL
- [x] JWT HS256 com perfil embarcado no token
- [x] Guards de rota no frontend por `localStorage.perfil`

**Fluxo de Aprovação**
- [x] Cadeia N1 → N2 → Setor → Agências → Decisão do setor
- [x] Tokens UUID de aprovação com expiração
- [x] Portal de aprovação standalone (sem login) para gestores
- [x] Detecção de viagem emergencial (< 15 dias)

**Cotação Dupla**
- [x] Duas agências cotam a mesma solicitação independentemente
- [x] Setor vê comparativo lado a lado e escolhe a vencedora
- [x] Upsert de cotação por `(solicitacao_id, agencia_nome)`

**E-mails**
- [x] 5 templates HTML responsivos via SMTP relay corporativo
- [x] Envio simultâneo para Tastur e Kontrip na etapa de cotação

**Frontend**
- [x] Portal do Viajante completo (login → formulário → histórico)
- [x] Portal de Aprovação (link por e-mail)
- [x] Portal da Agência (login + envio de cotação)
- [x] Painel do Setor (tabela + filtros + indicadores + KPIs + gráficos)

---

### 🔜 Próximos Passos

#### Fase 5 — Notificação ao viajante
- [ ] E-mail para o viajante informando que a viagem foi **aprovada e encaminhada à agência**
- [ ] E-mail para o viajante ao final com os dados do voo/hotel reservados (`CONCLUIDA`)
- [ ] E-mail informando reprovação com motivo

#### Fase 6 — Portal do Viajante: Histórico completo
- [ ] Aba "Minhas Solicitações" exibindo todas as solicitações com status em tempo real
- [ ] Página de detalhe da solicitação com linha do tempo do fluxo de aprovação
- [ ] Cancelamento de solicitação pelo viajante (status `AGUARDANDO_N1`)

#### Fase 7 — Integração Duffel (voos reais)
- [ ] Endpoint `/api/v1/duffel/pesquisar` já criado — conectar ao frontend
- [ ] Widget de pesquisa de voos no formulário do viajante
- [ ] Exibir opções de voo retornadas pela Duffel para o viajante selecionar preferência

#### Fase 8 — Relatórios e Exportação
- [ ] Exportação da lista de solicitações do painel do setor para CSV/Excel
- [ ] Dashboard com gráfico de gastos por período (após cotações concluídas)
- [ ] Relatório de viagens por colaborador / diretoria

#### Fase 9 — Qualidade e Operação
- [ ] Testes unitários com `pytest` para os services
- [ ] Variáveis de ambiente via `.env` carregadas pelo Pydantic `BaseSettings`
- [ ] Script de deploy / restart automático (Windows Task Scheduler ou NSSM)
- [ ] Rotação de logs com `logging.handlers.RotatingFileHandler`

---

## � Como Contribuir

Este projeto é de uso interno do Luizalabs / Magalu. Para propor melhorias ou corrigir bugs:

1. **Crie uma branch** a partir da `main`:
   ```bash
   git checkout -b feat/minha-melhoria
   ```

2. **Faça suas alterações** seguindo as convenções do projeto:
   - Backend: manter a Clean Architecture (não coloque regras de negócio nos endpoints)
   - Frontend: não usar `node_modules` — toda dependência via CDN
   - Não commitar arquivos `.env`, `venv/` ou `__pycache__/` (já no `.gitignore`)

3. **Commits semânticos:**
   ```
   feat: adiciona notificação ao viajante na conclusão
   fix: corrige expiração do token de aprovação N2
   docs: atualiza README com novos endpoints
   refactor: extrai lógica de e-mail para EmailService
   ```

4. **Abra um Pull Request** para a branch `main` com descrição clara do que foi alterado e qual problema resolve.

5. **Aguarde revisão** — o merge só é feito após aprovação do responsável técnico.

### Padrões de código
| Aspecto | Convenção |
|---|---|
| Idioma do código | Inglês (variáveis, funções) |
| Idioma dos comentários | Português |
| Formatação Python | PEP 8 |
| Schemas Pydantic | CamelCase para classes, snake_case para campos |
| Frontend | Um arquivo por portal — sem build step |

---

## 📄 Licença e Contato

### Licença

Este projeto é **proprietário e de uso exclusivo interno do Luizalabs / Magazine Luiza S.A.**  
Não é permitida a reprodução, distribuição ou uso externo sem autorização expressa.

```
Copyright © 2026 Luizalabs — Magazine Luiza S.A.
Todos os direitos reservados.
```

### Equipe e Contato

| Papel | Nome | Contato |
|---|---|---|
| Desenvolvimento & Arquitetura | Leandro Araújo | [@leandroaraujo-max](https://github.com/leandroaraujo-max) |
| Gestão de Viagens (setor) | Rubia Paim | rubia.paim@luizalabs.com |
| E-mail do sistema | ViagensLabs | vagenslabs@luizalabs.com |

### Repositório

🔗 **https://github.com/leandroaraujo-max/viagens_labs**

---

## 🤖 Prompt de Handoff para IA

Se estiver continuando o desenvolvimento em uma nova sessão de IA, use o contexto abaixo:

```
Projeto: ViagensLabs — Portal corporativo de viagens Luizalabs/Magalu
Repo: https://github.com/leandroaraujo-max/viagens_labs
Branch: main | Workspace local: C:\Projetos\viagens_labs\

Stack: Python 3.14, FastAPI, SQLAlchemy ORM, PostgreSQL :5433, ldap3 (AD), JWT HS256,
       Vue.js 3 CDN, TailwindCSS CDN, Nginx (Windows)

Como rodar o backend:
  cd C:\Projetos\viagens_labs
  $env:PYTHONPATH="."; .\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Banco de Dados:
  PostgreSQL porta 5433, DB: solicitacao_viagens
  URL: postgresql://postgres:Magazine%40123@127.0.0.1:5433/solicitacao_viagens?client_encoding=utf8
  Migrações: automáticas no startup via _migracoes_seguras() em app/main.py

Arquitetura: Clean Architecture
  app/api/v1/endpoints/  → auth, viagens, aprovacao, agencia, setor, duffel
  app/services/          → viagens, aprovacao, cotacao, casamento, setor
  app/infrastructure/    → database, ldap_service, bigquery_service, email_service, duffel_service
  app/domain/models/     → schemas.py (Pydantic)
  frontend/              → index.html, portal_aprovacao.html, agencia.html, painel.html

Fluxo de status ATUAL (22/05/2026):
  AGUARDANDO_N1
    └─ N1 férias (BQ SITUACAO) → AGUARDANDO_N2
    └─ N1 aprova + emergencial → AGUARDANDO_N2
    └─ N1 aprova + comum      → PENDENTE_PRE_APROVACAO_SETOR
    └─ N1 reprova              → REPROVADA
  AGUARDANDO_N2
    └─ N2 aprova → PENDENTE_PRE_APROVACAO_SETOR
    └─ N2 reprova → REPROVADA
  PENDENTE_PRE_APROVACAO_SETOR
    └─ Setor pré-aprova → AGUARDANDO_COTACAO (+ e-mail Tastur+Kontrip)
    └─ Setor pré-reprova → REPROVADA
  AGUARDANDO_COTACAO
    └─ 1 agência cota → COTACAO_ENVIADA
    └─ 2 agências cotam → PENDENTE_APROVACAO_SETOR_COTACAO
  PENDENTE_APROVACAO_SETOR_COTACAO
    └─ Setor aprova Tastur/Kontrip → CONCLUIDA  ← ERRADO, deve ser APROVADA_AGUARDANDO_VOUCHER
    └─ Setor reprova → REPROVADA
  [FALTANDO] APROVADA_AGUARDANDO_VOUCHER
    └─ Todos vouchers entregues → CONCLUIDA

O PRÓXIMO PASSO É IMPLEMENTAR (Fase 5A):
  1. setor_service._aprovar_agencia(): mudar CONCLUIDA → APROVADA_AGUARDANDO_VOUCHER
  2. email_service.py: +5 templates (viajante_aprovado, agencia_perdedora, reprovacao, vouchers, conclusao)
  3. Novo voucher_service.py: upload PDF + _verificar_conclusao_vouchers()
  4. Novo app/api/v1/endpoints/voucher.py: POST /api/v1/vouchers/{id}/upload
  5. agencia.html: tela de upload de vouchers para a agência vencedora

APOS FASE 5A (ver README seção 'Plano de Implementação' para 5B e 5C):
  Fase 5B: Motor SLA (thread daemon sla_scheduler.py)
  Fase 5C: Casamento completo (vincular/ignorar no painel do setor)

QA Override:
  .env: QA_APROVADOR_EMAIL=leandro.araujo@luizalabs.com
  Remove: 1 linha em config.py + 3 linhas em aprovacao_service._criar_token()

N1 em Férias:
  bigquery_service.buscar_situacao_por_email(email) → checa SITUACAO
  aprovacao_service._aprovador_esta_de_ferias() → compara com {"férias","ferias"}

AD Groups:
  G_ACCESS_VIAGENSLABS_ADMINS   → perfil "setor"    → /painel.html
  G_ACCESS_VIAGENSLABS_USERS    → perfil "viajante" → /index.html
  G_ACCESS_VIAGENSLABS_AGENCIAS → perfil "agencia_ad" (reservado)

AD Servers:
  ldap://ML-ASC-AD-01.magazineluiza.intranet
  ldap://ML-ASC-AD2.magazineluiza.intranet
  ldap://ML-HB-AD01.magazineluiza.intranet

SMTP: smtpml.magazineluiza.intranet:25 | De: vagenslabs@luizalabs.com
BQ: maga-bigdata.kirk.assignee + maga-bigdata.mlpap.mag_v_funcionarios_ativos

Regra crítica ao gerar código: NUNCA use '...', '# ...' ou '#existing code'.
Sempre fornecer o código completo do método/função alterado.
```

---

*Última atualização: 22/05/2026 — Análise GAS vs FastAPI concluída. Próximo: Fase 5A (vouchers).*
