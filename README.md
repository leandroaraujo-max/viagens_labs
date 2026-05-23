# ✈️ Viagens Labs — Portal Corporativo de Viagens

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
| Portal | URL | Público | Acesso |
|---|---|---|---|
| Portal do Viajante | `/index.html` | Colaboradores Magalu (AD) | Login AD |
| Portal de Aprovação | `GAS_RELAY_URL?token=...` (público) | Gestores N1/N2 | Link por e-mail — acessível pelo celular |
| Portal da Agência | `GAS_RELAY_URL?agencia_token=...` (público) | Agências externas (Tastur, Kontrip) | Link por e-mail — sem login, sem VPN |
| Painel do Setor | `/painel.html` | Equipe interna de viagens (AD — grupo admins) | Login AD |

> **GAS Relay:** Aprovações e cotações de agências são servidas via Google Apps Script (deploy público).  
> O FastAPI registra tokens na planilha GAS; aprovadores e agências acessam pelo celular ou fora da intranet.

---

## ✨ Demonstração e Funcionalidades

### Capturas de Tela

| Portal do Viajante | Painel do Setor |
|:---:|:---:|
| Login com credenciais AD + foto aérea de fundo | Tabela de solicitações com filtros e KPIs |
| Formulário multi-passo (viajante, rota, preferências) | Modal comparativo dinâmico de cotações das agências |

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
- 🔐 Acesso exclusivo e seguro via link de token enviado por e-mail (GAS Relay)
- 📥 Visualiza solicitações aguardando cotação
- 💰 Envia cotação detalhada por serviço (voo, hotel, carro, rodoviário)
- 🔄 Pode atualizar cotação enquanto o setor não decidiu

**Setor de Viagens (admin)**
- 🗂️ Painel com todas as solicitações, filtráveis por status, período, agência e busca
- ⚡ Ações rápidas: pré-aprovar, reprovar, reenviar e-mail para agências
- ⚖️ Comparativo lado a lado e responsivo das cotações de todas as agências que enviaram ofertas
- 🏆 Seleção da agência vencedora com notificação automática e geração dinâmica de tokens
- 📈 Indicadores: KPIs dinâmicos + gráfico de distribuição por status + volume mensal por agência vencedora

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

---

## 🚀 Instalação e Configuração

### 1. Clonar e preparar o ambiente

```powershell
git clone https://github.com/leandroaraujo-max/viagens_labs.git
cd viagens_labs
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar o arquivo `.env`

Crie um arquivo `.env` na raiz do projeto (nunca commitar) baseado no `.env.example`:

```dotenv
# ── Banco de Dados ─────────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:SuaSenha@127.0.0.1:5433/solicitacao_viagens?client_encoding=utf8

# ── Agências — E-mails definitivos das agências parceiras ─────────────────────
# Durante testes, use seu próprio e-mail para receber os links de cotação/voucher.
AGENCIA_TASTUR_EMAIL=tastur@tastur.com.br
AGENCIA_KONTRIP_EMAIL=viagens@kontrip.com.br

# ── URL base dos links enviados ÀS AGÊNCIAS por e-mail ────────────────────────
# As agências são externas — não têm acesso à intranet, VPN ou internet do sistema.
# Este valor é a URL que aparece no botão do e-mail para as agências.
#
# Quando mudar de ambiente, só precisará alterar ESTA linha:
#   Testes (você na intranet):     BASE_URL_AGENCIA=http://viagenslabs.magazineluiza.intranet
#   Produção c/ VPN:              BASE_URL_AGENCIA=http://viagenslabs.magazineluiza.intranet
#   Produção c/ URL pública:      BASE_URL_AGENCIA=https://viagenslabs.magazineluiza.com.br
BASE_URL_AGENCIA=http://viagenslabs.magazineluiza.intranet

# ── URL base dos links de APROVAÇÃO enviados por e-mail (N1/N2) ───────────────
# Gestores aprovam pelo celular fora da intranet — basta trocar esta linha.
#   Testes (você na intranet):     BASE_URL_APROVACAO=http://viagenslabs.magazineluiza.intranet
#   Produção c/ VPN ou internet:  BASE_URL_APROVACAO=https://viagenslabs.magazineluiza.com.br
BASE_URL_APROVACAO=http://viagenslabs.magazineluiza.intranet

# ── Duffel API — busca consultiva de voos ──────────────────────────────────
DUFFEL_TOKEN=duffel_test_xxxxxxxxxxxx

# ── QA Override — redireciona aprovações para testador ─────────────────────
# Quando definido, TODOS os e-mails de aprovação (N1/N2) vão para este endereço.
# Remova ou deixe vazio em produção.
QA_APROVADOR_EMAIL=seu.email@luizalabs.com
```

> **Atenção `BASE_URL_AGENCIA`:** Quando as agências tiverem acesso via VPN ou quando o sistema
> for exposto à internet, basta trocar este valor no `.env`. Nenhum código precisa ser alterado.

### 3. Iniciar o backend

```powershell
cd C:\Projetos\viagens_labs
$env:PYTHONPATH="."; .\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> O startup executa `_migracoes_seguras()` automaticamente — todas as tabelas e colunas
> novas são criadas via `ADD COLUMN IF NOT EXISTS` sem risco de perda de dados.

### 4. Iniciar o Nginx (servidor web)

```powershell
nginx.exe -c C:\Projetos\viagens_labs\nginx_config\nginx.conf
```

### 5. Criar usuários de agência (primeira vez)

```powershell
python seed_agencia.py
```

---

## 💻 Como Usar

1. Acesse `http://viagenslabs.magazineluiza.intranet` (porta 80)
2. **Colaborador:** faz login com usuário/senha da rede → preenche solicitação
3. **Gestor N1/N2:** recebe e-mail com botão → clica → aprova/reprova sem login
4. **Setor:** acessa `/painel.html` → pré-aprova → agências recebem e-mail com link
5. **Agência:** clica no link do e-mail → registra cotação direto (sem login)
6. **Setor:** painel mostra comparativo → escolhe vencedora → agência vencedora recebe link de vouchers
7. **Agência vencedora:** clica no link → anexa vouchers por serviço → solicitação concluída, visando testabilidade, independência de frameworks e alta coesão das regras de negócio corporativas (Luizalabs/Magalu).

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
| GAS Relay (externo) | Google Apps Script Web App (Google Sheets como fila) |
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
│   │   ├── duffel_service.py           # API Duffel para pesquisa de voos
│   │   ├── google_relay_service.py     # Integração com GAS relay (aprovações + agências)
│   │   └── aprovacao_relay_scheduler.py # Thread daemon: polling GAS → processa decisões/cotações reais
│   ├── repositories/
│   │   └── viagens_repository.py       # Acesso ao banco (queries SQLAlchemy)
│   ├── services/
│       ├── viagens_service.py          # Lógica de criação de solicitações
│       ├── aprovacao_service.py        # Lógica de aprovação N1/N2
│       ├── cotacao_service.py          # Lógica de cotação das agências
│       ├── casamento_service.py        # Deduplica viagens com mesmo trecho
│       ├── setor_service.py            # Painel do setor — listagem e ações + criação de tokens
│       └── voucher_service.py          # Upload e verificação de conclusão de vouchers
├── frontend/
│   ├── index.html                      # Portal do Viajante (SPA principal)
│   ├── portal_aprovacao.html           # Portal de Aprovação N1/N2 (link por e-mail)
│   ├── agencia.html                    # Portal da Agência (Tastur / Kontrip) — login + modo token
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
| `via_delegacao` | Boolean | Solicitação feita por delegação |
| `origem_cidade` / `origem_estado` | String | Origem da viagem |
| `destino_cidade` / `destino_estado` | String | Destino |
| `data_ida` / `data_volta` | String | Datas da viagem |
| `tipo_servico` | String | `aereo,hotel,carro,rodov` (CSV) |
| `motivo_viagem` | Text | Justificativa |
| `classificacao` | String | `Comum` ou `Emergencial` (< 15 dias) |
| `antecedencia_dias` | Integer | Dias de antecedência calculados |
| `exige_aprovacao_diretoria` | Boolean | Classificação de diretoria |
| `aereo_tipo_trecho` | String | `ida_e_volta`, `somente_ida`, `multitrechos` |
| `aereo_periodo_preferido` | String | Período preferido de voo (manhã, tarde…) |
| `bagagem_extra` | Boolean | Solicita bagagem despachada |
| `assento_especial` | String | Preferência de assento |
| `preferencia_voo` | Text | Voo de ida consultado no Duffel (JSON) |
| `preferencia_voo_volta` | Text | Voo de volta consultado no Duffel (JSON) |
| `rodov_periodo_preferido` | String | Período preferido rodoviário |
| `rodov_tipo_onibus` | String | Tipo de ônibus (executivo, leito…) |
| `rodov_tipo_trecho` | String | Trecho rodoviário |
| `preferencia_hotel_nome` | String | Hotel de preferência |
| `quarto_excecao_saude` | Boolean | Quarto individual por exceção de saúde |
| `carro_data_retirada` / `carro_data_devolucao` | String | Datas independentes de retirada/devolução |
| `carro_hora_retirada` / `carro_hora_devolucao` | String | Horários de retirada/devolução |
| `carro_cidade_retirada` / `carro_cidade_devolucao` | String | Cidades de retirada/devolução |
| `observacoes_viajante` | Text | Observações livres do viajante |
| `aprovador_n1_email` / `aprovador_n1_nome` | String | Gestor N1 (do BigQuery) |
| `aprovador_n2_email` / `aprovador_n2_nome` | String | Gestor N2 (do BigQuery) |
| `viajante_nome` / `viajante_cpf` / `viajante_matricula` | String | Dados pessoais do colaborador |
| `viajante_email` / `viajante_cargo` / `viajante_filial` | String | Dados funcionais do colaborador |
| `viajante_centro_custo` / `viajante_cod_centro_custo` | String | Centro de custo |
| `viajante_celular` / `viajante_data_nascimento` / `viajante_data_admissao` | String | Dados adicionais |
| `status` | String | Estado atual do fluxo |
| `agencia_vencedora` | String | `Tastur` ou `Kontrip` (após decisão) |
| `created_at` | DateTime | Timestamp de criação |

### Tabela `tokens_agencia`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | Integer PK | — |
| `uuid` | String unique | Token UUID enviado no link do e-mail |
| `solicitacao_id` | FK | Referência à solicitação |
| `agencia_nome` | String | `Tastur` ou `Kontrip` |
| `finalidade` | String | `COTACAO` (7 dias) ou `VOUCHER` (14 dias) |
| `status` | String | `PENDENTE`, `USADO`, `EXPIRADO` |
| `data_expiracao` | DateTime | Prazo de validade do link |
| `data_criacao` | DateTime | Timestamp de criação |

### Tabela `tokens_aprovacao`
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
| `solicitacao_id` | FK + index | Suporta múltiplas cotações dinâmicas por solicitação |
| `agencia_nome` | String | Nome da agência cadastrada no banco |
| `aereo_companhia` / `aereo_valor` | String / Numeric | Dados do voo cotado |
| `hotel_nome` / `hotel_valor_diaria` | String / Numeric | Dados do hotel cotado |
| `rodov_empresa` / `rodov_valor` | String / Numeric | Dados rodoviários |
| `carro_locadora` / `carro_valor_diaria` | String / Numeric | Dados de carro |
| `valor_total` | Numeric | Valor total da cotação |
| `observacoes` | Text | Observações da agência |
| `criado_em` | DateTime | — |

### Tabela `usuarios_agencia` (AgenciaModel)
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | Integer PK | — |
| `agencia_nome` | String index | Nome fantasia (ex: Tastur / Kontrip) |
| `razao_social` / `cnpj` | String | Dados legais |
| `email` | String | E-mail de contato da agência |
| `cep` / `logradouro` / `numero` / `bairro` / `municipio` / `uf` | String | Dados de Endereço |
| `banco_nome` / `agencia_bancaria` / `conta_bancaria` | String | Dados Bancários |
| `ativo` | Boolean | Habilita/desabilita envio de novos tokens |

> **Migrações seguras:** O `app/main.py` roda `_migracoes_seguras()` no startup que executa `ALTER TABLE … ADD COLUMN IF NOT EXISTS` e `DROP CONSTRAINT IF EXISTS` — sem necessidade de Alembic.

---

## 🔄 Fluxo de Status da Solicitação

```
[Viajante cria]
       │
       ▼
AGUARDANDO_N1  ──(N1 está de Férias — BQ)──▶  AGUARDANDO_N2
       │                                              │
    (N1 aprova                                  (N2 aprova)
     + exige N2)                                      │
       │                                              │
       ▼                                              │
AGUARDANDO_N2 ◀───────────────────────────────────────┘
       │
    (N2 aprova)──(qualquer etapa reprova)──▶  REPROVADA
       │
       ▼
PENDENTE_PRE_APROVACAO_SETOR  ──(reprova)──▶  REPROVADA
       │
    (setor pré-aprova)
    Cria token COTACAO (Tastur) + token COTACAO (Kontrip)
    Envia e-mail com botão → agencia.html?token=UUID
       │
       ▼
AGUARDANDO_COTACAO
       │
    (agências cotam via link token — sem login)
       │
    1 agência ──▶  COTACAO_ENVIADA
    2 agências ──▶  PENDENTE_APROVACAO_SETOR_COTACAO
       │
    (setor escolhe vencedora)
    Cria token VOUCHER para vencedora
    Envia e-mails: vencedora (link vouchers), perdedora, viajante
       │
       ▼
APROVADA_AGUARDANDO_VOUCHER
       │
    (agência sobe vouchers por serviço via link token)
       │
       ▼
CONCLUIDA  ── e-mail com vouchers enviado ao viajante
```

**Regra de férias:** Se `SITUACAO` do N1 no BigQuery contém a substring `"ferias"` (sem acento), ele é considerado ausente e o fluxo vai direto para N2.

**Regra emergencial:** Solicitações com `data_ida` em menos de 15 dias são classificadas como `Emergencial`. Não há etapas adicionais por isso — N2 é apenas escalação (N1 de férias ou SLA excedido).

**GAS Relay:** Quando `GAS_RELAY_URL` e `GAS_SECRET` estão configurados no `.env`, o FastAPI registra cada token (aprovação N1/N2 e cotação de agência) no Google Apps Script. Aprovadores e agências recebem um link GAS público acessível de qualquer lugar. Um scheduler (thread daemon, intervalo configurável) faz polling a cada `GAS_POLL_INTERVALO` segundos e processa as respostas recebidas.

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

### Agência (acesso por token — sem login)
As agências (Tastur, Kontrip) são externas e não têm acesso à intranet ou VPN.
O acesso funciona via **link único enviado por e-mail**, sem necessidade de login:

1. Setor pré-aprova → sistema cria um UUID por agência (finalidade `COTACAO`) e envia e-mail
2. Agência clica no botão do e-mail → `agencia.html?token=UUID`
3. Frontend detecta `?token=` e chama `GET /api/v1/agencia/token/{uuid}` sem auth
4. Mostra o formulário direto (sem tela de login)
5. Após setor escolher vencedora → sistema cria novo UUID (finalidade `VOUCHER`) e envia e-mail
6. Agência vencedora acessa link de vouchers pelo mesmo mecanismo

> Login via usuário/senha também permanece funcíonal para uso interno (quando VPN estiver disponível).

### GAS Relay — Aprovações e Cotações Externas (sem VPN)

O sistema usa um **Google Apps Script Web App** como fila pública intermediária:
- **Aprovações N1/N2:** gestores aprovam pelo celular sem precisar de intranet ou VPN
- **Cotações de Agências:** Tastur e Kontrip preenchem cotação via link público Google

```dotenv
# Habilita o relay GAS (quando configurado, substitui BASE_URL_APROVACAO e BASE_URL_AGENCIA)
GAS_RELAY_URL=https://script.google.com/macros/s/AKfycb.../exec
GAS_SECRET=vl-secret-2026          # igual ao Script Property GAS_SECRET no GAS editor
GAS_POLL_INTERVALO=60              # segundos entre polls
```

**Como funciona:**
1. FastAPI registra token no GAS via `POST {action: registrar | registrar_agencia}`
2. E-mail enviado com link `GAS_RELAY_URL?token=UUID` ou `?agencia_token=UUID`
3. Aprovador/Agência acessa o portal HTML servido pelo GAS (sem login, qualquer browser)
4. Decisão/cotação é gravada na planilha do Google Sheets
5. Scheduler Python faz polling a cada 60s → processa e avança o workflow

**Setup do GAS (uma vez por deploy):**
```javascript
// No editor do Google Apps Script:
setup()        // cria sheets 'pendentes' e 'decisoes'
setupAgencia() // cria sheets 'cotacoes_agencia' e 'respostas_agencia'
// Propriedades do script: GAS_SECRET = vl-secret-2026
```

**Fallback:** Se `GAS_RELAY_URL` não estiver configurado, o sistema usa `BASE_URL_APROVACAO` e `BASE_URL_AGENCIA` como antes (intranet). Os dois modos coexistem.

### Configuração de URL (fallback sem GAS)
```dotenv
# Quando GAS não está configurado, usa estas URLs como fallback:
BASE_URL_APROVACAO=http://viagenslabs.magazineluiza.intranet
BASE_URL_AGENCIA=http://viagenslabs.magazineluiza.intranet
```

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

### Agência (link token — sem auth)
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/agencia/login` | Login da agência (credencial bcrypt) |
| `GET` | `/api/v1/agencia/solicitacoes` | Lista solicitações (autenticado) |
| `POST` | `/api/v1/agencia/solicitacoes/{id}/cotacao` | Envia ou atualiza cotação (autenticado) |
| `GET` | `/api/v1/agencia/token/{uuid}` | Carrega solicitação pelo token do e-mail (**sem auth**) |
| `POST` | `/api/v1/agencia/token/{uuid}/cotacao` | Registra cotação pelo token do e-mail (**sem auth**) |
| `POST` | `/api/v1/agencia/token/{uuid}/voucher` | Upload de voucher pelo token de voucher (**sem auth**) |

### Setor (requer perfil `setor`)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/setor/solicitacoes` | Lista com filtros (status, período, agência, busca) |
| `GET` | `/api/v1/setor/solicitacoes/{id}` | Detalhe + cotações das duas agências |
| `POST` | `/api/v1/setor/solicitacoes/{id}/acao` | Executa ação: `PRE_APROVAR`, `PRE_REPROVAR`, `APROVAR_TASTUR`, `APROVAR_KONTRIP`, `REPROVAR`, `REENVIAR_AGENCIAS` |

### Vouchers
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/vouchers/{id}/upload` | Upload de voucher (autenticado — agência login) |

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
- **Modo token** (padrão para agências externas): detecta `?token=` na URL → carrega solicitação direto, sem tela de login
  - Token `COTACAO`: exibe formulário de cotação pré-preenchido com dados da solicitação
  - Token `VOUCHER`: exibe tela de upload de vouchers (1 PDF por tipo de serviço)
- **Modo login** (quando VPN disponível): login com usuário/senha bcrypt, lista todas as solicitações da agência
- Formulário de cotação por serviço (aéreo, hotel, rodoviário, carro)
- Suporta múltiplas cotações simultâneas de qualquer agência cadastrada e ativa
- Tela de loading e tela de erro para tokens inválidos/expirados

### Painel do Setor (`painel.html`)
- Requer perfil `setor` (verificado no `onMounted` via `localStorage`)
- **Aba Solicitações:** tabela com filtros por status, período, agência e busca livre
- **Ações rápidas por status:**
  - `PENDENTE_PRE_APROVACAO_SETOR` → Pré-Aprovar / Reprovar
  - `AGUARDANDO_COTACAO` → Reenviar e-mail para agências
  - `PENDENTE_APROVACAO_SETOR_COTACAO` → Modal comparativo de cotações (escolher Tastur ou Kontrip)
- **Modal de Detalhe:** dados completos + cotações lado a lado com highlight do vencedor
- **Aba Indicadores:** KPIs gerados dinamicamente para cada agência cadastrada + gráfico de distribuição por status + volume mensal (últimos 6 meses)

---

## 📧 Notificações por E-mail

**SMTP:** `smtpml.magazineluiza.intranet:25`  
**De:** `viagenslabs@luizalabs.com`  
**Reply-To:** `rubia.paim@luizalabs.com`

| Template | Disparado quando | Destinatário |
|---|---|---|
| Solicitação recebida | Criação da solicitação | Solicitante |
| Aprovação N1 | Solicitação criada com sucesso | Gestor N1 (BigQuery) |
| Aprovação N2 | N1 aprova | Gestor N2 (BigQuery) |
| Setor — pré-aprovação | N1 ou N2 aprova | `viagenslabs@luizalabs.com` |
| Agências — cotação | Setor pré-aprova | Tastur + Kontrip (link `?token=UUID` por agência) |
| Setor — comparativo | 2ª agência envia cotação | `viagenslabs@luizalabs.com` |
| Agência vencedora | Setor escolhe agência | Agência escolhida (link `?token=UUID` de voucher) |
| Agência perdedora | Setor escolhe agência | Agência não selecionada |
| Viajante aprovado | Setor escolhe agência | Solicitante |
| Resultado (aprovado/reprovado) | N1/N2 decide | Solicitante |
| Reprovação geral | Qualquer etapa | Solicitante |
| Vouchers emitidos | Todos vouchers enviados | Solicitante |

> **URL dos links para agências:** usam `BASE_URL_AGENCIA` (configurável no `.env`),
> independente de `BASE_URL` — permite apontar para URLs diferentes quando as agências
> tiverem VPN ou acesso público.

---

## 📊 Estado Atual e Próximos Passos

### ✅ Implementado (Fase 6)
- **Portal do Desenvolvedor (`dev.html`):** Dashboard gerencial com métricas e painel de variáveis de ambiente.
- **Redesign de Agências:** Agências agora usam um modelo unificado (CNPJ, endereço, banco) sem necessidade de login. O acesso é exclusivo via Token/GAS.

### 🔜 Próximos Passos (Fase 7 e Estabilização)
- **Correção Crítica (23/05):** Adaptar `dev.py` e `seed_agencia.py` à nova estrutura sem senhas.
- **Solicitação para Terceiros:** Novo workflow substituindo a "Delegação". Usuário abre ticket anexando PDF de autorização para solicitar viagens em nome de outros (ex: diretores).
- **Modernização UI/UX Premium:** Cotações do GAS em TailwindCSS + Glassmorphism (sem estrelas, com auto-complete do voo desejado pelo usuário). Grid responsivo no painel do setor.

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
| E-mail do sistema | ViagensLabs | viagenslabs@luizalabs.com |

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
  app/api/v1/endpoints/  → auth, viagens, aprovacao, agencia, setor, duffel, voucher
  app/services/          → viagens, aprovacao, cotacao, casamento, setor, voucher
  app/infrastructure/    → database, ldap_service, bigquery_service, email_service,
                           duffel_service, google_relay_service, aprovacao_relay_scheduler
  app/domain/models/     → schemas.py (Pydantic)
  frontend/              → index.html, portal_aprovacao.html, agencia.html, painel.html
  gas/                   → Code.gs (relay GAS), appsscript.json, .clasp.json

GAS Relay (aprovações externas + cotações de agências):
  Script ID : 1VqosNh6_Sqv8vr_210MKHp0G5anbZJDmYtIAUw1WnfbPCVWOXtwMI8lY
  Deploy v4 : https://script.google.com/macros/s/AKfycbykFk0vwKSe2tRcdcFY5Tm8Gt7udb_bcued1qwAQl4XOSpqjJySiga6lTRZ8NKrbT1xKQ/exec
  SHEET_ID  : 1o5PBNWpv9y89EVyCIXjNtuQx27Mcn0gIKPlUU_KQrrU
  GAS_SECRET: vl-secret-2026 (Script Property key: GAS_SECRET)
  Planilha  : 4 sheets: pendentes, decisoes, cotacoes_agencia, respostas_agencia
  Setup GAS : executar setup() e setupAgencia() no editor do GAS (uma vez)
  clasp     : cd gas && clasp push --force && clasp deploy --description "..."

Fluxo de status ATUAL (22/05/2026):
  AGUARDANDO_N1
    ├─ N1 férias (BQ SITUACAO contém substring 'ferias') → AGUARDANDO_N2
    ├─ N1 aprova → PENDENTE_PRE_APROVACAO_SETOR  (N2 apenas se N1 de férias)
    └─ N1 reprova → REPROVADA
  AGUARDANDO_N2
    ├─ N2 aprova → PENDENTE_PRE_APROVACAO_SETOR
    └─ N2 reprova → REPROVADA
  PENDENTE_PRE_APROVACAO_SETOR
    ├─ Setor pré-aprova → AGUARDANDO_COTACAO
    |   + cria TokenAgenciaModel(finalidade=COTACAO, TTL=7d) para Tastur e Kontrip
    |   + registra tokens no GAS relay (portal de cotação público)
    |   + e-mail com link GAS?agencia_token=UUID (um por agência)
    └─ Setor pré-reprova → REPROVADA
  AGUARDANDO_COTACAO
    ├─ 1 agência cota → COTACAO_ENVIADA
    └─ 2 agências cotam → PENDENTE_APROVACAO_SETOR_COTACAO
  PENDENTE_APROVACAO_SETOR_COTACAO
    ├─ Setor aprova Tastur/Kontrip → APROVADA_AGUARDANDO_VOUCHER
    |   + cria TokenAgenciaModel(finalidade=VOUCHER, TTL=14d) para vencedora
    |   + e-mail vencedora (link voucher), perdedora, viajante
    └─ Setor reprova → REPROVADA
  APROVADA_AGUARDANDO_VOUCHER
    └─ Todos vouchers entregues → CONCLUIDA + e-mail viajante

ACESSO DAS AGÊNCIAS (externas — via GAS relay, sem intranet/VPN):
  Agências recebem e-mail com link GAS_RELAY_URL?agencia_token=UUID
  GAS serve formulário HTML → agência preenche e submete
  Scheduler Python faz poll GAS a cada 60s → processa cotação via ViagensService
  Fallback: BASE_URL_AGENCIA/agencia.html?token=UUID (quando GAS não configurado)

ACESSO DOS APROVADORES (via GAS relay, celular/qualquer browser):
  Aprovadores recebem e-mail com link GAS_RELAY_URL?token=UUID
  GAS serve portal de aprovação HTML → aprova/reprova
  Scheduler Python faz poll GAS a cada 60s → processa decisão via AprovacaoService
  Fallback: BASE_URL_APROVACAO/portal_aprovacao.html?token=UUID

Variáveis de ambiente importantes (.env):
  GAS_RELAY_URL         = URL deploy v4 GAS (aprovações + cotações de agências)
  GAS_SECRET            = vl-secret-2026 (deve ser igual ao Script Property GAS_SECRET)
  GAS_POLL_INTERVALO    = 60 (segundos)
  AGENCIA_TASTUR_EMAIL  = e-mail definitivo da Tastur (testes: leandro.araujo@luizalabs.com)
  AGENCIA_KONTRIP_EMAIL = e-mail definitivo da Kontrip (testes: leandro.araujo@luizalabs.com)
  BASE_URL_AGENCIA      = fallback URL interna para agências
  BASE_URL_APROVACAO    = fallback URL interna para aprovadores
  QA_APROVADOR_EMAIL    = redireciona tokens de aprovação N1/N2 para testador

Tabelas ORM (app/infrastructure/orm/models.py):
  SolicitacaoModel       → solicitacoes
  TokenAprovacaoModel    → tokens_aprovacao
  TokenAgenciaModel      → tokens_agencia (finalidade: COTACAO/VOUCHER)
  CotacaoModel           → cotacoes
  VoucherModel           → vouchers
  CasamentoModel         → casamentos
  UsuarioAgenciaModel    → usuarios_agencia
  UserProfileModel       → user_profiles

setor.py — padrão atual:
  _build_setor_response() usa model_validate via sol.__table__.columns
  Novos campos são incluídos automaticamente — sem mapeamento manual

painel.html — modal de detalhe exibe 6 seções:
  1. Dados do Colaborador (viajante_*)
  2. Cadeia de Aprovação (aprovador_n1/n2_*)
  3. Preferências Aéreas (trecho, período, bagagem, assento, voo ida/volta Duffel)
  4. Preferências Rodoviárias
  5. Preferências de Hospedagem
  6. Preferências de Veículo

N1 em Férias:
  bigquery_service.buscar_situacao_por_email(email) → SITUACAO no BQ
  aprovacao_service._aprovador_esta_de_ferias() → substring 'ferias' (sem acento)

AD Groups:
  G_ACCESS_VIAGENSLABS_ADMINS   → perfil "setor"    → /painel.html
  G_ACCESS_VIAGENSLABS_USERS    → perfil "viajante" → /index.html
  G_ACCESS_VIAGENSLABS_AGENCIAS → perfil "agencia_ad" (reservado para VPN futura)

SMTP: smtpml.magazineluiza.intranet:25 | De: viagenslabs@luizalabs.com
BQ: maga-bigdata.kirk.assignee + maga-bigdata.mlpap.mag_v_funcionarios_ativos

PRÓXIMOS PASSOS:
  Fase 5B: Motor SLA (sla_scheduler.py — lembretes N1/cotacao)
  Fase 5C: Casamento completo (vincular/ignorar no painel do setor)
  Fase 6: Histórico com linha do tempo no portal do viajante
  Fase 7: GAS relay para vouchers (upload via Google Drive) OU VPN para agências

Regra crítica ao gerar código: NUNCA use '...', '# ...' ou '#existing code'.
Sempre fornecer o código completo do método/função alterado.
```

---

*Última atualização: 23/05/2026 — Estabilização geral e Dynamicização de Agências concluída: correção de ReferenceError do Vue 3 em fmtCnpj, bypass de tela preta na navegação de portais técnicos, KPI cards e filtros 100% dinâmicos por agência ativa, contagem inteligente de cotações para decisão e console terminal hacker de Logs do Sistema em tempo real.*

