---
name: refactor-arch-refactor
description: Fase 3 - Refatoração. Reestrutura projeto em camadas (MVC + Services + Repositories) APENAS com confirmação explícita. Modifica código-fonte. Usa mvc-guidelines e refactor-playbook.
---

# refactor-arch-refactor — Fase 3 (Refatoração)

Objetivo: reestruturar o projeto em arquitetura em camadas, corrigindo anti-patterns identificados na auditoria. **Somente após confirmação explícita do usuário.** Modifica código-fonte.

## Pré-requisitos OBRIGATÓRIOS
1. `reports/analysis-<nome-do-projeto>.md` existente
2. `reports/audit-<nome-do-projeto>.md` existente
3. **Confirmação explícita** do usuário ("prossiga com a refatoração", "aplique a Fase 3", "sim", etc.)

**Se algum pré-requisito não for atendido → NÃO iniciar.** Solicitar ao orquestrador que complete as fases anteriores.

## Referências a ler
Leia integralmente antes de aplicar:
- `../refactor-arch/references/mvc-guidelines.md`
- `../refactor-arch/references/refactor-playbook.md`

## Passo 1 — Planejar
1. Ler relatórios da Fase 1 e Fase 2
2. Identificar stack, framework e convenções detectadas
3. Aplicar mapeamento por ecossistema (seção 3 das `mvc-guidelines.md`). Se framework tem convenção própria (Rails, Django, Laravel, Spring), **seguir a convenção do framework**
4. Definir ordem conforme seção 5: **Config → Persistência → Repositories → Services → Controllers → Routes → Middleware → Cleanup → Validação**

## Passo 2 — Executar (passo a passo)
Seguir ordem rigorosamente:

1. **Config** - centralizar configuração via env, mover literais (resolve QUAL-07, SEC-02)
2. **Persistência** - separar conexão/inicialização, eliminar estado global mutável desprotegido
3. **Repositories** - um por entidade agregada, queries **parametrizadas** (resolve SEC-01, ARCH-02)
4. **Services** - extrair regras de negócio dos controllers (resolve ARCH-01, ARCH-03)
5. **Controllers** - reduzir a orquestração pura (request → service → response)
6. **Routes** - separar registro de rotas do entrypoint, agrupar por recurso
7. **Middleware** - adicionar guards/auth onde sinalizado pela auditoria (resolve SEC-04)
8. **Cleanup** - remover arquivos antigos, código morto, imports não usados
9. **Validação** - aplicar validadores onde ausentes (resolve QUAL-02)

**Regras:**
- **Mover, não copiar** - remover do arquivo original
- **Uma mudança por vez** - commits pequenos por entidade/recurso
- **Preservar funcionalidade** - manter URL, verbo e formato de resposta quando possível
- **Testar após cada passo** - exercitar endpoints afetados
- **Aplicar padrões** do `refactor-playbook.md`

Anti-patterns corrigidos naturalmente: SEC-01, SEC-02, ARCH-01, ARCH-02, QUAL-02, QUAL-03, QUAL-04, QUAL-07. Outros exigem passo dedicado (SEC-03, SEC-04, SEC-05, SEC-06, PERF-01, QUAL-05, QUAL-06, QUAL-08) conforme playbook.

## Passo 3 — Validar
Subir aplicação com comando de boot identificado na análise. Exercitar **todas** as rotas inventariadas. Seguir checklist seção 6 das `mvc-guidelines.md`:
- [ ] App sobe sem erros
- [ ] Todas rotas respondem no mesmo path/verbo/formato
- [ ] Rotas de escrita rejeitam payload malformado com 400
- [ ] Nenhuma query interpolada restante
- [ ] Nenhum segredo literal no código
- [ ] Responses não expõem campos sensíveis
- [ ] Sem try/except genérico engolindo erro sem log
- [ ] Arquivos antigos removidos
- [ ] git status limpo de sobras

## Passo 4 — Emitir relatório
Produzir `reports/refactor-<nome-do-projeto>.md` com:
1. **Resumo** das mudanças (antes/depois da estrutura)
2. **Anti-patterns corrigidos** e como foram resolvidos
3. **Resultado dos testes de validação** (endpoint a endpoint)
4. **Limitações e trabalho futuro** (autenticação real, testes, CI/CD)

**Bloco de resumo no terminal:**
```
================================
PHASE 3: REFACTORING
================================
Project:       <projeto>
Files before:  N files
Files after:   M files
Architecture:  Flat → MVC + Services + Repositories
Anti-patterns corrected: N (X CRITICAL, Y HIGH, Z MEDIUM)
Endpoints validated: N/N
Status:        Complete / Partial (motivo)
================================
```

## Regras
- **SOMENTE COM CONFIRMAÇÃO EXPLÍCITA**. Nunca iniciar sem confirmação clara do usuário.
- **Modificar código-fonte** - esta é a única fase com permissão para edit/write/move/delete em arquivos de código.
- **Mover, não copiar**. Eliminar duplicatas.
- **Preservar compatibilidade** sempre que possível.
- **Validar sistematicamente**.
- **Documentar tudo** no relatório.
- **Agnóstico de tecnologia**.
