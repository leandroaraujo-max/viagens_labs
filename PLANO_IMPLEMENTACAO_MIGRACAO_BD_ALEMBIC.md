# Plano de Implementação Completo
## Migração de Auto-DDL no Startup para Migrações Versionadas com Alembic

Data: 26/06/2026  
Status: Planejamento aprovado para execução faseada  
Escopo: Backend FastAPI + PostgreSQL + Operação CI/CD

---

## 1. Contexto e Problema Atual

Hoje a aplicação executa evolução de schema no startup da API (create_all + DDL incremental), o que acopla inicialização do servidor web à administração estrutural do banco de dados.

Principais pontos identificados no cenário atual:

- Startup da API executa DDL automaticamente.
- Múltiplos processos/workers podem disputar alterações no banco em paralelo.
- Jobs de scheduler também são inicializados no mesmo ciclo de vida da API, podendo duplicar execução em escala horizontal.
- Uso de credencial de alto privilégio como padrão em documentação e configuração.

Consequências operacionais:

- Risco de lock e corrida em deploy.
- Startup não determinístico.
- Dificuldade de rollback e rastreabilidade de alterações.
- Superexposição de privilégio no runtime.

---

## 2. Objetivo da Migração

Separar definitivamente:

1. Evolução de schema (DDL), que deve ocorrer por pipeline controlado.
2. Runtime da API, que deve somente consumir schema já provisionado.

Com isso, a API deixa de modificar estrutura do banco no boot e passa a depender de migrações versionadas e auditáveis com Alembic.

---

## 3. Escopo da Implementação

Inclui:

- Introdução do Alembic no projeto.
- Baseline do schema atual por ambiente.
- Pipeline CI/CD para aplicar migrações antes do rollout da API.
- Separação de usuários de banco por privilégio (migrator x app).
- Remoção progressiva do Auto-DDL no startup.
- Atualização de documentação operacional.

Não inclui neste ciclo:

- Refatorações amplas de domínio fora do tema de migração.
- Reescrita dos schedulers para outro orquestrador (será tratado como melhoria posterior).

---

## 4. Ganhos Esperados da Migração

### 4.1 Ganhos de Confiabilidade

- Deploy previsível: migração acontece em etapa explícita e controlada.
- Redução de falha de startup por lock/concorrência de DDL.
- Menor risco de inconsistência entre ambientes.

### 4.2 Ganhos de Escalabilidade

- Possibilidade de subir múltiplos workers sem risco de colisão em DDL.
- Separação clara entre operação de banco e operação de aplicação.
- Preparação para estratégia de autoscaling sem efeitos colaterais no schema.

### 4.3 Ganhos de Segurança

- Aplicação deixa de usar superusuário do banco.
- Princípio do menor privilégio com usuário de runtime restrito.
- Redução do impacto de eventual comprometimento da API.

### 4.4 Ganhos de Governança e Auditoria

- Histórico versionado de mudanças de schema.
- Rastreabilidade completa de quem mudou o quê e quando.
- Melhor suporte a auditorias internas e conformidade LGPD.

### 4.5 Ganhos de Operação e SRE

- Rollback mais claro via revisão de migração.
- Menor MTTR em incidentes de deploy ligados a banco.
- Runbooks mais simples e reproduzíveis.

### 4.6 Ganhos de Produtividade do Time

- Mudanças estruturais padronizadas.
- Menos retrabalho por divergência entre dev/hml/prod.
- Revisão de PR mais objetiva para alterações de banco.

---

## 5. Princípios de Arquitetura que Guiam a Mudança

- Banco como recurso externo com contrato explícito de versão.
- API sem responsabilidade de administração estrutural.
- Migração sempre versionada, revisada e executada fora do ciclo de boot da aplicação.
- Deploy fail-fast: se migração falhar, nova versão da API não sobe.

---

## 6. Estratégia Faseada de Implementação

## Fase 0 - Preparação e Congelamento de Mudanças Estruturais

Objetivo:
- Evitar criação de novo débito técnico enquanto a base de migração é montada.

Atividades:
1. Congelar novas mudanças de schema fora de arquivo de migração versionado.
2. Levantar inventário de DDL atualmente aplicado no startup.
3. Definir janela de mudança e plano de comunicação.

Entregáveis:
- Inventário DDL atual.
- Janela operacional aprovada.

Critério de aceite:
- Nenhuma alteração de schema sendo introduzida fora de plano.

---

## Fase 1 - Introdução do Alembic e Baseline

Objetivo:
- Implantar mecanismo oficial de versionamento de schema.

Atividades:
1. Instalar Alembic e inicializar estrutura de migração.
2. Configurar alembic.ini e env.py para apontar ao metadata da aplicação.
3. Criar revisão baseline refletindo schema real atual.
4. Aplicar stamp para alinhar ambientes existentes sem recriar objetos.

Entregáveis:
- Estrutura Alembic no repositório.
- Revisão baseline publicada.

Critério de aceite:
- Comando upgrade head executa com sucesso em ambiente de homologação.

Risco principal:
- Divergência entre schema real e metadata.

Mitigação:
- Validação por introspecção antes do baseline final.

---

## Fase 2 - Separação de Privilégios de Banco

Objetivo:
- Eliminar uso de superusuário no runtime da API.

Atividades:
1. Criar usuário db_migrator com privilégios DDL controlados.
2. Criar usuário db_app com privilégios mínimos para runtime.
3. Atualizar secrets por ambiente para cada contexto de uso.
4. Validar que API funciona 100% com db_app sem DDL.

Entregáveis:
- Modelo de privilégios definido e aplicado.
- Matriz de permissões por usuário.

Critério de aceite:
- API executa fluxos principais sem qualquer permissão de DDL.

Risco principal:
- Permissão faltante em runtime.

Mitigação:
- Teste de regressão transacional e ajuste incremental de grants.

---

## Fase 3 - Pipeline CI/CD com Gate de Migração

Objetivo:
- Garantir ordem correta: migrar banco antes de publicar nova versão da API.

Atividades:
1. Adicionar etapa de migração no pipeline (upgrade head).
2. Definir bloqueio de rollout se migração falhar.
3. Implementar validação pós-migração (sanity checks).
4. Publicar logs e evidências de execução para auditoria.

Entregáveis:
- Pipeline com gate de migração ativo.
- Checklist de validação automática pós-migração.

Critério de aceite:
- Deploy é interrompido automaticamente em erro de migração.

---

## Fase 4 - Desativação Progressiva do Auto-DDL no Startup

Objetivo:
- Remover acoplamento da API com evolução estrutural do banco.

Atividades:
1. Introduzir flag temporária para desligar Auto-DDL por ambiente.
2. Desligar primeiro em homologação e executar bateria de testes.
3. Desligar em produção após ciclo estável em homologação.
4. Remover código legado de create_all/migrações no startup.

Entregáveis:
- Runtime da API sem execução de DDL.
- Documentação de startup atualizada.

Critério de aceite:
- API sobe estável sem executar migração estrutural no boot.

---

## Fase 5 - Hardening Operacional e Pós-Migração

Objetivo:
- Consolidar segurança e confiabilidade do novo modelo.

Atividades:
1. Revisão final de privilégios efetivos no banco.
2. Auditoria de credenciais e rotação planejada.
3. Teste de escala com múltiplos workers.
4. Revisão de jobs/schedulers para evitar duplicidade em multi-worker.

Entregáveis:
- Relatório de hardening.
- Plano de evolução dos schedulers (processo dedicado ou lock distribuído).

Critério de aceite:
- Operação validada com carga e sem efeitos colaterais de concorrência.

---

## 7. Plano de Rollback

Princípios:

- Rollback de aplicação e rollback de schema devem ser controlados separadamente.
- Em caso de falha de migração, impedir rollout da API nova.

Procedimento:

1. Falha na migração antes do deploy:
   - Aborta pipeline.
   - Mantém versão anterior da API em execução.

2. Falha após migração parcial:
   - Executar rollback para revisão anterior (quando seguro).
   - Se downgrade não for possível, aplicar migração corretiva imediata.

3. Falha funcional pós-deploy:
   - Rollback da aplicação para versão anterior compatível.
   - Preservar estado do banco sob revisão atual e abrir incidente.

---

## 8. Riscos, Impactos e Mitigações

1. Divergência entre banco real e modelos ORM.
- Mitigação: baseline validado por introspecção e revisão técnica.

2. Lock prolongado em alterações grandes.
- Mitigação: migrations pequenas, janela de baixa demanda e estratégia expand/contract.

3. Quebra de compatibilidade entre versão antiga da API e schema novo.
- Mitigação: migrations backward-compatible por pelo menos um ciclo.

4. Erro de permissão ao retirar superusuário.
- Mitigação: matriz de grants com testes E2E antes de produção.

5. Duplicidade de schedulers em múltiplos workers.
- Mitigação: processo dedicado de scheduler ou lock distribuído.

---

## 9. Critérios de Pronto (Definition of Done)

A migração será considerada concluída quando:

1. Alembic estiver ativo e obrigatório para qualquer mudança de schema.
2. API subir sem create_all e sem DDL incremental no startup.
3. Pipeline aplicar migração antes do rollout e bloquear em falha.
4. Runtime usar usuário db_app sem privilégio DDL.
5. Documentação operacional e de handoff estiver atualizada.
6. Testes de regressão e smoke em homologação e produção passarem.

---

## 10. Cronograma Sugerido

Semana 1:
- Fase 0 e Fase 1 (inventário + baseline Alembic)

Semana 2:
- Fase 2 (privilégios) + Fase 3 (pipeline)

Semana 3:
- Fase 4 (desligamento progressivo) + início Fase 5

Semana 4:
- Fase 5 completa + fechamento operacional

Observação:
- Pode ser acelerado se houver janela dedicada de infraestrutura.

---

## 11. Responsáveis Sugeridos

- Backend: desenho de migrations, compatibilidade e remoção de Auto-DDL.
- DevOps/SRE: pipeline, secrets, estratégia de rollback e observabilidade.
- DBA/Infra: grants, governança de privilégios, validação de lock e performance.
- Segurança/Compliance: validação de menor privilégio e trilha de auditoria.

---

## 12. KPIs de Sucesso

1. Taxa de deploy sem falha por migração.
2. Tempo médio de deploy (antes x depois).
3. Incidentes por lock/DDL em startup.
4. Percentual de serviços runtime sem superusuário.
5. Tempo de recuperação em incidente de release (MTTR).

Metas iniciais:
- Reduzir a zero incidentes de DDL concorrente no startup.
- 100% dos ambientes com usuário de runtime sem DDL.
- 100% das mudanças de schema rastreadas por revisão Alembic.

---

## 13. Decisões de Arquitetura Registradas

1. Evolução de schema passa a ser responsabilidade exclusiva de migrações versionadas.
2. Startup da API não executará DDL em produção.
3. Menor privilégio é obrigatório para runtime.
4. Pipeline de deploy passa a ter gate de banco como pré-condição.

---

## 14. Próximos Passos Imediatos

1. Aprovar este plano com Backend, DevOps e DBA.
2. Abrir épico técnico: Migração de Auto-DDL para Alembic.
3. Criar tarefas por fase com dono e prazo.
4. Agendar janela de homologação para baseline e teste de rollback.

---

## 15. Resultado Esperado Final

Ao final da execução:

- O sistema terá deploy previsível, seguro e auditável.
- O banco deixará de sofrer mudanças estruturais em runtime.
- A operação ficará apta a escalar workers sem risco de corrida em schema.
- O ambiente atenderá melhor requisitos de segurança e conformidade.

Este plano substitui o modelo atual de evolução estrutural automática no startup e estabelece padrão operacional sustentável para produção.
