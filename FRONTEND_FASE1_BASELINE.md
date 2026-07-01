# Fase 1 — Diagnóstico Frontend (ViagensLabs)

Data: 2026-06-25  
Escopo analisado: `frontend/**` (HTML, JS, CSS do projeto)

## 1) Baseline atual (métricas objetivas)

- **Total de arquivos frontend**: 17
- **Total de linhas frontend**: **10.649**
- **Concentração de código**: 4 arquivos concentram a maior parte da complexidade

### Maiores arquivos (hotspots)
1. `frontend/setor.html` — **2.447** linhas
2. `frontend/index.html` — **2.128** linhas
3. `frontend/dev.html` — **2.042** linhas
4. `frontend/agencia.html` — **954** linhas

> Observação: há arquivos de biblioteca vendorizados em `frontend/js/lib/*` que não devem ser foco de refatoração de domínio.

---

## 2) Inventário de duplicação e acoplamento

## 2.1 Sessão/autenticação duplicada
Evidências de leitura/escrita de sessão espalhadas em múltiplas telas:
- `localStorage.getItem/setItem/clear` em `index.html`, `setor.html`, `dev.html`, `dashboard.html`, `app.js`, `index - Copy.html`.
- Estruturas de login/logout e persistência de token repetidas.

## 2.2 Headers de autorização repetidos
- Múltiplas ocorrências de montagem manual de `Authorization: Bearer ...`.
- Presente em `index.html`, `setor.html`, `dev.html`, `agencia.html`, `app.js`.

## 2.3 Chamada HTTP sem client central
- Alto volume de `fetch(...)` direto em páginas:
  - `dev.html`: ~27 chamadas
  - `index.html`: ~20 chamadas
  - `setor.html`: ~20 chamadas
  - `agencia.html`: ~6 chamadas
- Não há camada única de retry/timeout/tratamento de 401/403 e parsing de erro.

## 2.4 Mistura de responsabilidades (HTML + lógica + regras + estado)
- Páginas monolíticas com UI, estado, integração HTTP e regras de negócio no mesmo arquivo.
- Dificulta teste, manutenção e reaproveitamento.

## 2.5 Dívida técnica explícita
- `frontend/index - Copy.html` (cópia de tela) indica duplicação estrutural e risco de divergência.

---

## 3) Mapa de criticidade por arquivo

## Criticidade Alta
- `frontend/setor.html`
- `frontend/index.html`
- `frontend/dev.html`

## Criticidade Média
- `frontend/agencia.html`
- `frontend/portal_aprovacao.html`
- `frontend/dashboard.html`

## Criticidade Baixa
- `frontend/app.js`
- `frontend/js/transition.js`
- `frontend/estilos.css`

---

## 4) Top 20 refactors priorizados (backlog Fase 1→2)

## P0 — Fundação (reaproveitamento imediato)
1. Criar `frontend/services/api-client.js` (wrapper único de `fetch`).
2. Criar `frontend/services/auth-session.js` (get/set/clear token, usuário, perfil).
3. Criar `frontend/services/http-errors.js` (normalização de erros de API).
4. Substituir headers manuais por `apiClient.authHeaders()`.
5. Remover `index - Copy.html` do fluxo ativo (arquivar/retirar referência).

## P1 — Quebra de páginas gigantes
6. Extrair módulo `setor-api.js` de `setor.html`.
7. Extrair módulo `setor-state.js` de `setor.html`.
8. Extrair módulo `index-api.js` de `index.html`.
9. Extrair módulo `index-state.js` de `index.html`.
10. Extrair módulo `dev-api.js` de `dev.html`.
11. Extrair módulo `dev-state.js` de `dev.html`.

## P1 — UI reutilizável
12. Componente reutilizável de `Modal`.
13. Componente reutilizável de `Toast/Alert`.
14. Componente reutilizável de `Loading/Empty/Error state`.
15. Componente reutilizável de `StatusBadge`.

## P2 — Padronização de formulários e validações
16. Módulo único `validators.js` (CPF, CNPJ, CEP, datas, campos obrigatórios).
17. Módulo `formatters.js` (datas, moeda, textos).
18. Padronizar mensagens de erro de formulário e API.

## P2 — Governança técnica
19. Definir limite inicial por arquivo de página (meta: <= 400 linhas por módulo funcional).
20. Adicionar checklist de PR frontend (sem novo fetch direto em página; sem novo localStorage espalhado).

---

## 5) Plano de execução da Fase 1 (prático)

### Sprint 1 (curto, baixo risco)
- Entregar `api-client.js`, `auth-session.js`, `http-errors.js`.
- Migrar `dev.html` para usar esses 3 módulos.

### Status Sprint 1 (executado)
- ✅ `frontend/js/services/api-client.js` criado e integrado.
- ✅ `frontend/js/services/auth-session.js` criado e integrado.
- ✅ `frontend/js/services/http-errors.js` criado.
- ✅ `dev.html` migrou para sessão centralizada (sem uso direto de `localStorage`).
- ✅ Principais blocos do `dev.html` migrados para `apiClient`:
  - login/sessão
  - QA suites/jobs
  - stats/atividade
  - solicitações/agências/config
  - consultas SQL
  - delegações AD
  - testadores QA
  - serviços (recarregar/reiniciar)
  - logs e logs de acesso
  - exclusão cascade

Métrica de evolução no `dev.html`:
- Antes do Sprint 1: ~27 `fetch(...)` diretos
- Após Sprint 1: **0 `fetch(...)` diretos** (uso de `apiClient.request(...)`)

### Sprint 2
- Migrar `index.html` para os mesmos serviços.
- Extrair `validators.js` e `formatters.js`.

### Status Sprint 2 (iniciado)
- ✅ Criado `frontend/js/services/validators.js` com funções reutilizáveis:
  - `maskDateBR`, `parseDateBR`, `toISODateTime`, `isoToDisplay`, `maskPhoneBR`.
- ✅ Criado `frontend/js/services/formatters.js` com funções reutilizáveis:
  - `formatCPF`, `formatHourFromIso`.
- ✅ `index.html` integrado com serviços compartilhados:
  - `http-errors.js`, `auth-session.js`, `api-client.js`, `validators.js`, `formatters.js`.
- ✅ Migração parcial/majoritária de endpoints internos de `index.html` para `apiClient.request(...)`.
- ✅ Removidos headers manuais de `Authorization` nos fluxos migrados.

Métrica parcial do Sprint 2 (`index.html`):
- Antes: ~20 `fetch(...)` diretos
- Agora: **3 `fetch(...)` diretos** (todos externos: Nominatim/OSRM para cálculo de distância)
- `Authorization` manual: **0** ocorrências

### Sprint 3
- Migrar `setor.html` para os serviços.
- Extrair componentes visuais reutilizáveis.

### Status Sprint 3 (iniciado)
- ✅ `setor.html` agora carrega os serviços compartilhados (`http-errors`, `auth-session`, `api-client`).
- ✅ Sessão do setor preparada com namespace (`VLAuthSession.createNamespace('portal')`) e `apiClient` central.
- ✅ Migração inicial no `setor.html` para `apiClient.request(...)` nos fluxos:
  - consentimento LGPD gestor
  - listagem de solicitações
  - detalhe da solicitação
- ✅ logout do setor atualizado para limpeza explícita de chaves de sessão (sem `localStorage.clear()`).

Métrica atual do Sprint 3 (`setor.html`):
- Antes: ~20 `fetch(...)` diretos
- Agora: **1 `fetch(...)` direto**

Blocos já migrados no `setor.html`:
- consentimento LGPD gestor
- solicitações (lista, detalhe e ações)
- stats e alertas de acesso
- casamentos (lista e decisão)
- tickets de terceiros (lista e decisão)
- proxies (CNPJ/CEP/Banco)
- agências (listar/criar/editar/ativar/desativar/excluir)

Pendência técnica intencional no `setor.html`:
- `fetch` para abertura de PDF assinado (fluxo com `blob` + `window.open`) mantido por requisito funcional.

### Snapshot consolidado (frontend atual)
Top arquivos por `fetch(...)` direto:
- `frontend/index.html`: 3 *(externos Nominatim/OSRM)*
- `frontend/setor.html`: 1 *(exceção técnica de PDF autenticado via blob)*

Decisão de escopo:
- `frontend/index - Copy.html` **pulado por decisão do usuário** (arquivo cópia/legado fora da trilha principal).

Próximos alvos (sem `index - Copy.html`):
- reduzir acoplamento residual em `index.html` (sessão/localStorage legado)
- manter `setor.html` com única exceção técnica de PDF autenticado via blob

### Próximo passo executado (pós-Sprint 3)
- ✅ `frontend/agencia.html` migrou chamadas para `VLApiClient`.
- ✅ `frontend/agencia.html` passou a carregar serviços compartilhados (`http-errors`, `auth-session`, `api-client`).
- ✅ `frontend/agencia.html`: **0 `fetch(...)` direto** e **0 `Authorization` manual**.

### Próximo passo executado (continuação)
- ✅ `frontend/portal_aprovacao.html` migrou validação/processamento para `VLApiClient`.
- ✅ `frontend/portal_aprovacao.html` passou a carregar serviços compartilhados (`http-errors`, `auth-session`, `api-client`).
- ✅ `frontend/portal_aprovacao.html`: **0 `fetch(...)` direto** e **0 `Authorization` manual**.

### Próximo passo executado (continuação 2)
- ✅ `frontend/dashboard.html` migrou criação de solicitação para `VLApiClient`.
- ✅ `frontend/dashboard.html` passou a usar namespace de sessão (`VLAuthSession.createNamespace('portal')`) com fallback legado controlado.
- ✅ `frontend/dashboard.html`: **0 `fetch(...)` direto** e **0 `Authorization` manual**.
- ✅ `frontend/app.js` migrou `runServer(...)` para `VLApiClient.requestJson(...)` (sem `fetch`/`Authorization` manual).
- ✅ `frontend/app.js` removeu `localStorage.clear()` e adotou limpeza explícita de chaves de autenticação.

### Próximo passo executado (continuação 3)
- ✅ `frontend/index.html` reduziu acoplamento de sessão, removendo referências diretas a `localStorage.*` no fluxo principal (uso centralizado via `storage` + `portalSession`).
- ✅ Persistência de LGPD preservada com o mesmo comportamento funcional no logout/login.
- ✅ `frontend/index.html` mantém apenas **3 `fetch(...)` diretos intencionais** (Nominatim/OSRM).

### Próximo passo executado (continuação 4)
- ✅ `frontend/setor.html` consolidou sessão com `VLAuthSession` + `hydrateSessionFromLegacyStorage()` (migração legacy pontual).
- ✅ `frontend/setor.html` removeu fallback contínuo de leitura direta em `localStorage` para token/nome/perfil no estado inicial.
- ✅ `frontend/setor.html` ficou com **0 referências diretas `localStorage.*`** no código (uso via `storage`).
- ✅ `frontend/setor.html` mantém apenas **1 `fetch(...)` direto intencional** (download/abertura de PDF binário via blob).

### Próximo passo executado (continuação 5)
- ✅ `frontend/dashboard.html` consolidou sessão com `VLAuthSession` + `hydrateSessionFromLegacyStorage()`.
- ✅ `frontend/dashboard.html` removeu acessos diretos a `localStorage.*` (uso via `storage`).
- ✅ `frontend/dashboard.html` mantém **0 `fetch(...)` direto** e **0 `Authorization` manual**.

### Próximo passo executado (continuação 6)
- ✅ Criado `frontend/css/shared-ui.css` para reutilização visual inicial.
- ✅ Regras compartilhadas extraídas: `[v-cloak]`, `fade-in` (com keyframes) e utilitário de tipografia `.vl-font-inter`.
- ✅ `frontend/agencia.html` passou a consumir `shared-ui.css` e removeu duplicação local dessas regras.
- ✅ `frontend/portal_aprovacao.html` passou a consumir `shared-ui.css` e removeu duplicação local dessas regras.

### Próximo passo executado (continuação 7)
- ✅ `frontend/index.html` passou a consumir `shared-ui.css` e removeu duplicação local de `[v-cloak]`.
- ✅ `frontend/setor.html` passou a consumir `shared-ui.css` e removeu duplicação local de `[v-cloak]`.
- ✅ `frontend/dev.html` passou a consumir `shared-ui.css` e removeu duplicações locais de `[v-cloak]` e `font-family: 'Inter'`.
- ✅ Validação após migração: sem erros (`get_errors`) nas telas alteradas e no CSS compartilhado.

### Próximo passo executado (continuação 8)
- ✅ `frontend/css/shared-ui.css` recebeu extração adicional de regra comum de transição Vue: `.fade-enter-from` / `.fade-leave-to`.
- ✅ `frontend/index.html`, `frontend/setor.html` e `frontend/agencia.html` removeram duplicações locais dessa regra.
- ✅ Durações específicas por tela foram preservadas (`.fade-enter-active` / `.fade-leave-active` permanecem locais).
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem resíduos fora do arquivo excluído de escopo (`index - Copy.html`).

### Próximo passo executado (continuação 9)
- ✅ `frontend/css/shared-ui.css` recebeu regra padrão compartilhada de transição Vue: `.fade-enter-active` / `.fade-leave-active` com duração base `.3s`.
- ✅ `frontend/setor.html` e `frontend/agencia.html` removeram duplicações locais dessa regra.
- ✅ `frontend/index.html` manteve override local de `.4s` para preservar o comportamento atual da tela.
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem resíduos fora do arquivo excluído de escopo (`index - Copy.html`).

### Próximo passo executado (continuação 10)
- ✅ `frontend/css/shared-ui.css` recebeu utilitário compartilhado para backgrounds recorrentes: `.bg-viagens`, `.bg-setor`, `.bg-aprovacao` com `background-size`, `background-position` e `background-attachment` centralizados.
- ✅ `frontend/index.html`, `frontend/agencia.html`, `frontend/setor.html` e `frontend/portal_aprovacao.html` removeram duplicações locais dessas propriedades.
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem resíduos fora do arquivo excluído de escopo (`index - Copy.html`).

### Próximo passo executado (continuação 11)
- ✅ `frontend/css/shared-ui.css` recebeu utilitário de fundo base `.vl-bg-labs-dark` para padronizar o fallback escuro de páginas com tema labs.
- ✅ `frontend/index.html` e `frontend/agencia.html` removeram regra local `body { background: #0f172a; }` e passaram a usar classe compartilhada no `<body>`.
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem resíduos dessa regra duplicada nos HTMLs de escopo.

### Próximo passo executado (continuação 12)
- ✅ `frontend/css/shared-ui.css` recebeu variável compartilhada `--vl-bg-aviao` para centralizar a URL da imagem de fundo.
- ✅ `frontend/index.html`, `frontend/agencia.html`, `frontend/setor.html` e `frontend/portal_aprovacao.html` passaram a consumir `var(--vl-bg-aviao)` mantendo seus gradientes locais.
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem uso remanescente de `url('/img/bg-aviao.jpg')` nos HTMLs de escopo.

---

## 6) Fechamento consolidado — Migração para React (atualização 2026-07-01)

### 6.1 Resultado técnico (estado atual)
- ✅ Frontend principal operando em **React + Vite** com rotas ativas:
  - `/`, `/setor`, `/agencia`, `/dashboard`, `/aprovacao`, `/dev`, `/politica-privacidade`.
- ✅ Runtime Vue legado removido do `src` (páginas e estrutura antigas descontinuadas).
- ✅ Serviços React consolidados em `frontend/src/services/*` com `createApiClient` e tratamento de erro padronizado.
- ✅ Assets legados órfãos removidos (`frontend/js/**`, `frontend/app.js`, arquivos estáticos antigos não utilizados).
- ✅ Warning de asset de fundo resolvido com migração da imagem para `src/assets/images`.
- ✅ Melhorias de A11y aplicadas em formulários, modais e feedback de status dinâmico.

### 6.2 Checklist de conclusão (Fase 1 → baseline React)
- ✅ Bootstrap React/Vite estabilizado.
- ✅ Migração das rotas críticas concluída.
- ✅ Limpeza de legados HTML/CSS/JS órfãos concluída.
- ✅ Padronização de estilo em services concluída.
- ✅ Ajustes A11y iniciais concluídos (labels, `aria-live`, `aria-pressed`, botões de fechar com `aria-label`).
- ✅ Build de produção validado nas etapas finais.

### 6.3 Evidências (commits recentes)
- `a5720f5` — migração rota dashboard para React
- `d56d15d` — migração rota aprovação para React
- `b7f1c50` — migração rota dev para React
- `3cb9aae` — migração política de privacidade para React
- `e49b9cf` — remoção de placeholders e legados HTML/CSS
- `206aa31` — remoção de assets legados órfãos
- `70672cf` — correção do warning de asset de fundo (`bg-aviao`)
- `9053a16` — remoção de resquícios de legado Vue
- `43cf701` — padronização de estilo dos services
- `2bba23d` — melhoria de acessibilidade em formulários e modais
- `065b9ee` — melhoria de feedback A11y em setor e agência

### 6.4 Pendências recomendadas (próxima fase)
- 🔜 Expandir cobertura de testes automatizados de frontend (fluxos críticos de login/solicitação/aprovação).
- 🔜 Definir baseline de lint/format para React (`biome` ou stack equivalente) como gate de CI.
- 🔜 Revisão A11y complementar com foco em navegação por teclado ponta-a-ponta e foco em diálogos.

### Próximo passo executado (continuação 13)
- ✅ `frontend/css/shared-ui.css` recebeu utilitário compartilhado `.vl-shell-dark-card` para a casca visual de cards escuros (estrutura, blur, borda e sombra).
- ✅ `frontend/index.html` migrou o card principal do login para `vl-shell-dark-card` mantendo modificadores locais (`transition-*`).
- ✅ `frontend/agencia.html` migrou os cards de estados de token (carregando/erro) para `vl-shell-dark-card`, mantendo modificadores locais (`text-center`).
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem a string extensa duplicada nos arquivos de escopo alterados.

### Próximo passo executado (continuação 14)
- ✅ `frontend/css/shared-ui.css` recebeu utilitário `.vl-approval-state-card` para os cards brancos de estado no portal de aprovação.
- ✅ `frontend/portal_aprovacao.html` migrou os 4 estados (`erro`, `ja_respondido`, `expirado`, `concluido`) para `vl-approval-state-card`.
- ✅ Ajustado alinhamento dos blocos no HTML após aplicação parcial automática de patch (sem alteração de comportamento).
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem repetição remanescente da classe longa nesses estados.

### Próximo passo executado (continuação 15)
- ✅ `frontend/css/shared-ui.css` recebeu utilitários `.vl-approval-panel` e `.vl-approval-action-btn` para composição de blocos do fluxo de aprovação.
- ✅ `frontend/portal_aprovacao.html` migrou os dois painéis brancos principais (dados da viagem e observação) para `vl-approval-panel`.
- ✅ `frontend/portal_aprovacao.html` migrou os dois botões de ação (aprovar/reprovar) para `vl-approval-action-btn`, mantendo classes de cor locais.
- ✅ Validação pós-extração: sem erros (`get_errors`) e sem regressão visual funcional esperada.

### Próximo passo executado (continuação 16)
- ✅ `frontend/css/shared-ui.css` recebeu design token de alerta âmbar (`--vl-alert-amber-bg`, `--vl-alert-amber-border`) e utilitário `.vl-amber-alert-surface`.
- ✅ `frontend/index.html`, `frontend/portal_aprovacao.html`, `frontend/setor.html` e `frontend/politica-privacidade.html` migraram superfícies âmbar para composição via `vl-amber-alert-surface`.
- ✅ Removida duplicação de `bg-amber-50 border border-amber-200 rounded-lg` em pontos de UI repetidos entre páginas.
- ✅ Validação pós-extração: sem erros (`get_errors`) e 8 ocorrências confirmadas do novo utilitário (incluindo definição CSS).

### Próximo passo executado (continuação 17)
- ✅ `frontend/css/shared-ui.css` recebeu design token de superfície informativa azul (`--vl-info-blue-bg`, `--vl-info-blue-border`) e utilitário `.vl-blue-info-surface`.
- ✅ `frontend/index.html`, `frontend/setor.html` e `frontend/politica-privacidade.html` migraram blocos de informação azul para composição via `vl-blue-info-surface`.
- ✅ Removida duplicação de `bg-blue-50 border border-blue-200 rounded-lg` nos pontos de escopo da extração.
- ✅ Validação pós-extração: sem erros (`get_errors`) e 5 ocorrências confirmadas de `vl-blue-info-surface` (incluindo definição CSS).

### Próximo passo executado (continuação 18)
- ✅ `frontend/css/shared-ui.css` recebeu design token de superfície de erro vermelha (`--vl-error-red-bg`, `--vl-error-red-border`) e utilitário `.vl-red-error-surface`.
- ✅ `frontend/index.html` e `frontend/setor.html` migraram blocos de feedback de erro com `red-200` para composição via `vl-red-error-surface`.
- ✅ Removida duplicação de `bg-red-50 border border-red-200 rounded-lg` no escopo da extração.
- ✅ Variante específica `bg-red-50 border border-red-300 rounded-lg` foi preservada intencionalmente (contexto de responsabilidade LGPD).
- ✅ Validação pós-extração: sem erros (`get_errors`) e 6 ocorrências confirmadas de `vl-red-error-surface` (incluindo definição CSS).

### Próximo passo executado (continuação 19)
- ✅ `frontend/css/shared-ui.css` recebeu design token de superfície de sucesso verde (`--vl-success-green-bg`, `--vl-success-green-border`) e utilitário `.vl-green-success-surface`.
- ✅ `frontend/index.html` e `frontend/portal_aprovacao.html` migraram blocos de feedback de sucesso com `green-200` para composição via `vl-green-success-surface`.
- ✅ Removida duplicação de `bg-green-50 border border-green-200 rounded-lg` no escopo da extração.
- ✅ Validação pós-extração: sem erros (`get_errors`) e 3 ocorrências confirmadas de `vl-green-success-surface` (incluindo definição CSS).

### Próximo passo executado (continuação 20)
- ✅ `frontend/css/shared-ui.css` recebeu utilitário `.vl-link-primary` para links de ação textual recorrentes.
- ✅ `frontend/index.html`, `frontend/setor.html` e `frontend/politica-privacidade.html` migraram links com `text-blue-600 hover:underline font-semibold` para `vl-link-primary`.
- ✅ Removida duplicação do trio de classes de link no escopo da extração.
- ✅ Validação pós-extração: sem erros (`get_errors`) e 5 ocorrências confirmadas de `vl-link-primary` (3 usos + 2 regras CSS).

Observação:
- O alvo principal da Fase 1 (reduzir acoplamento por `fetch` e `Authorization` manual em hotspots críticos) está cumprido em `dev.html` e majoritariamente cumprido em `index.html` e `setor.html`.

### Próximo passo executado (continuação 21)
- ✅ `frontend/css/shared-ui.css` recebeu utilitário `.vl-btn-logout` para o padrão de botão de logout recorrente nos headers.
- ✅ `frontend/index.html` migrou botão "Sair" do header para `vl-btn-logout` (removida classe inline longa).
- ✅ `frontend/setor.html` migrou botão "Sair" do header para `vl-btn-logout` (removida classe inline longa).
- ✅ `frontend/dashboard.html` passou a importar `shared-ui.css` (último arquivo sem a folha compartilhada).
- ✅ `frontend/politica-privacidade.html` passou a importar `shared-ui.css` + Google Fonts Inter, removeu `<style>` local com `font-family` e adotou `vl-font-inter` no `<body>`.
- ✅ Validação pós-extração: sem resíduos do padrão antigo (`ml-2 text-xs font-semibold text-red-500...`).
- ✅ `shared-ui.css` agora importado por **todas as 7 telas ativas** do escopo: `index`, `setor`, `dev`, `agencia`, `portal_aprovacao`, `dashboard`, `politica-privacidade`.
- ✅ `vl-btn-logout`: 4 ocorrências (2 usos nos HTMLs + 2 regras CSS).

Próximo alvo técnico imediato:
- avaliar fechamento da Fase 1 com revisão final de padrões residuais e checklist de aceite (sem novas unificações agressivas).

---

## 6) Critérios de aceite da Fase 1 (Concluído)

- [x] Baseline documentado (este arquivo).
- [x] Hotspots e duplicações mapeados com evidências.
- [x] Top 20 backlog priorizado e sequenciado.
- [x] Ordem de implementação aprovada para início da execução.
- [x] Fase 1 finalizada com sucesso.

### Métricas Finais da Fase 1 (Fechamento)
- **agencia.html**: 1.202 linhas
- **dashboard.html**: 169 linhas
- **dev.html**: 2.344 linhas
- **index.html**: 2.708 linhas
- **politica-privacidade.html**: 351 linhas
- **portal_aprovacao.html**: 260 linhas
- **setor.html**: 2.608 linhas
- **Módulos extraídos**: `api-client.js`, `auth-session.js`, `http-errors.js`, `validators.js`, `formatters.js`, `shared-ui.css`.
- **Fetch Direto e Auth Manual**: Eliminados dos hotspots principais (exceto justificativas técnicas como PDF via blob e geocoding externo).

---

## 7) Risco e mitigação

- **Risco**: quebra de comportamento por refatoração em arquivo monolítico.
- **Mitigação**: migração incremental por módulo, feature flags simples, smoke test manual por tela ao final de cada etapa.
