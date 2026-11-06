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
4. Definir ordem conforme seção 5: **Config → Persistência → Repositories → Services → Controllers → Routes → Middleware/Auth → Cleanup → Validação**

## Passo 2 — Executar (passo a passo)
Seguir ordem rigorosamente:

1. **Config** - centralizar configuração via env, mover literais (resolve QUAL-07, SEC-02)
2. **Persistência** - separar conexão/inicialização, eliminar estado global mutável desprotegido
3. **Repositories** - um por entidade agregada, queries **parametrizadas** (resolve SEC-01, ARCH-02)
4. **Services** - extrair regras de negócio dos controllers (resolve ARCH-01, ARCH-03)
5. **Controllers** - reduzir a orquestração pura (request → service → response)
6. **Routes** - separar registro de rotas do entrypoint, agrupar por recurso
7. **Middleware/Auth** - aplicar autenticação e autorização **default deny** (Padrão 9) em todas as rotas de escrita e administrativas sinalizadas pela auditoria (resolve SEC-04). Nunca deixar a proteção atrás de flag opcional
8. **Cleanup** - remover arquivos antigos, código morto, imports não usados
9. **Validação** - aplicar validadores onde ausentes (resolve QUAL-02)

**Regras:**
- **Mover, não copiar** - remover do arquivo original
- **Uma mudança por vez** - commits pequenos por entidade/recurso
- **Preservar funcionalidade** - manter URL, verbo e formato de resposta quando possível. **Exceção obrigatória:** correções de CRITICAL/HIGH não podem ser adiadas por compatibilidade; se o contrato mudar, documente no relatório e atualize os testes.
- **Testar após cada passo** - exercitar endpoints afetados
- **Aplicar padrões** do `refactor-playbook.md`
- **Segurança por padrão** - auth/autorização ativas no default do projeto; nenhuma correção pode depender de flag opcional (ex.: `AUTH_REQUIRED=true`) para existir.
- **Autorização por papel** - gestão de usuários exige `admin`; rotas de domínio exigem o papel adequado; criação em nome de terceiro só é permitida com posse derivada do token. Identidade, papel e posse vêm do token, nunca de `role`/`tipo`/`usuario_id`/`owner_id` do body.

Anti-patterns corrigidos naturalmente: SEC-01, SEC-02, ARCH-01, ARCH-02, QUAL-02, QUAL-03, QUAL-04, QUAL-07. Outros exigem passo dedicado (SEC-03, SEC-04, SEC-05, SEC-06, PERF-01, QUAL-05, QUAL-06, QUAL-08) conforme playbook.

## Passo 3 — Validar
Subir aplicação com comando de boot identificado na análise. Exercitar **todas** as rotas inventariadas. Seguir checklist seção 6 das `mvc-guidelines.md`:
- [ ] App sobe sem erros
- [ ] Todas rotas respondem no mesmo path/verbo/formato
- [ ] Rotas de escrita rejeitam payload malformado com 400
- [ ] Nenhuma query interpolada restante
- [ ] Nenhum segredo literal no código
- [ ] Responses não expõem campos sensíveis
- [ ] Rotas de escrita rejeitam anônimo por padrão (`401`)
- [ ] Rotas administrativas rejeitam não-admin (`403`)
- [ ] Identidade, papel e posse são derivados do token, nunca do body
- [ ] Nenhuma senha em texto puro em seed/banco — hash com salt em todo armazenamento
- [ ] Testes de segurança por finding executados (SEC-02, SEC-03, SEC-04, SEC-06)
- [ ] Sem try/except genérico engolindo erro sem log
- [ ] Arquivos antigos removidos
- [ ] git status limpo de sobras

### Testes obrigatórios por finding de segurança

- **SEC-04:** provar `401` sem credencial, `403` com papel insuficiente e `200/201` com o papel correto, **com a configuração padrão do projeto** (sem ligar flag especial). Gestão de usuários (`POST`/`PUT`/`DELETE` e listagem administrativa) só pode passar com `admin`.
- **SEC-03:** inspecionar o banco/seed e provar que todo armazenamento começa com prefixo de hash (`scrypt:`, `pbkdf2:` ou `$2`); provar que o login funciona e que não existe fallback de comparação em texto puro.
- **SEC-02:** grep por segredos literais + boot com a configuração padrão.
- **SEC-06:** capturar logs de uma requisição autenticada e provar que não há senha, token nem PII.

## Passo 4 — Matriz de Fechamento CRITICAL/HIGH (obrigatória)

Antes de emitir o relatório, prove que **cada** achado CRITICAL/HIGH da auditoria deixou de existir. Preencha uma linha por achado na matriz abaixo; ela deve ir no relatório final.

| ID | Severidade | Impacto descrito na auditoria | Correção aplicada | Evidência estática (arquivo:linha) | Evidência dinâmica (teste/comando/HTTP) | Status |
|---|---|---|---|---|---|---|
| SEC-04 | HIGH | ... | ... | `middleware/auth.py:...` | `POST /tasks` sem token → `401` | `RESOLVIDO` |

**Regras da matriz:**
- Os únicos status válidos são **`RESOLVIDO`** e **`BLOQUEADO`**. **`PARCIAL` não é aceito na Fase 3.**
- `RESOLVIDO` exige **evidência estática e dinâmica**. Só código alterado não fecha o achado.
- `BLOQUEADO` significa que a Fase 3 **não pode ser declarada concluída**; o relatório deve explicar o bloqueio e retornar ao usuário.
- Se qualquer CRITICAL/HIGH não puder ser resolvido, **não emita status de conclusão** e não avance para a Fase 4.

## Passo 5 — Emitir relatório
Produzir `reports/refactor-<nome-do-projeto>.md` com:
1. **Resumo** das mudanças (antes/depois da estrutura)
2. **Anti-patterns corrigidos** e como foram resolvidos
3. **Matriz de Fechamento CRITICAL/HIGH** (Passo 4)
4. **Resultado dos testes de validação** (endpoint a endpoint), incluindo os testes obrigatórios de segurança
5. **Pendências** — apenas MEDIUM/LOW; **não pode conter CRITICAL/HIGH**
6. **Limitações e trabalho futuro** (autenticação real, testes, CI/CD)

**Bloco de resumo no terminal:**
```
================================
PHASE 3: REFACTORING
================================
Project:       <projeto>
Files before:  N files
Files after:   M files
Architecture:  Flat → MVC + Services + Repositories
Critical resolved: A/A
High resolved:     B/B
Anti-patterns corrected: N (X CRITICAL, Y HIGH, Z MEDIUM)
Endpoints validated: N/N
Status:        Complete | BLOQUEADO (motivo)
================================
```

Se `A/A` ou `B/B` não estiver completo, o status **deve** ser `BLOQUEADO` — nunca `Complete / Partial`.

## Regras
- **SOMENTE COM CONFIRMAÇÃO EXPLÍCITA**. Nunca iniciar sem confirmação clara do usuário.
- **Modificar código-fonte** - esta é a única fase com permissão para edit/write/move/delete em arquivos de código.
- **Mover, não copiar**. Eliminar duplicatas.
- **Preservar compatibilidade** sempre que possível — **exceto** quando ela mantiver um CRITICAL/HIGH aberto. Nesse caso, documente a mudança de contrato e atualize os testes.
- **Fechar o impacto, não apenas aplicar o padrão** — a Fase 3 só termina com todos os CRITICAL/HIGH `RESOLVIDO` na matriz.
- **Validar sistematicamente**.
- **Documentar tudo** no relatório.
- **Agnóstico de tecnologia**.
