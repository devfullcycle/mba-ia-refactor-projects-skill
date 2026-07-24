---
name: refactor-arch
description: Audita e refatora uma codebase para o padrão MVC, de forma agnóstica de linguagem e framework. Executa 3 fases — análise da stack, relatório de auditoria com anti-patterns classificados por severidade (arquivo:linha), e refatoração validada. Use quando o pedido envolver auditoria de arquitetura, code smells, dívida técnica, violação de MVC/SOLID, "refatorar para MVC", "organizar em camadas" ou revisão de projeto legado.
---

# Auditoria e Refatoração Arquitetural (MVC)

Transforma um projeto legado em uma aplicação MVC em camadas, sem quebrar o comportamento
externo. Funciona em qualquer linguagem/framework: toda detecção parte de evidências do
próprio repositório (manifestos, imports, padrões de rota), nunca de nomes de arquivo
específicos de um projeto.

## Regras invioláveis

1. **Nada é modificado antes da aprovação humana.** As Fases 1 e 2 são somente leitura.
   A Fase 3 só começa após o usuário responder afirmativamente ao gate da Fase 2.
2. **O contrato externo é preservado.** Mesmas rotas, mesmos métodos HTTP, mesmos códigos de
   status e mesma forma de payload. Refatoração não é redesign de API. Exceção: falha de
   segurança que *exige* mudança de payload (ex.: hash de senha exposto na resposta) — nesse
   caso, remova o campo e registre a mudança explicitamente no relatório final.
3. **Baseline antes de tocar em código.** Capture o comportamento atual dos endpoints
   (Fase 3, passo 0) para poder provar que a refatoração não regrediu nada.
4. **Nenhum finding sem `arquivo:linha`.** Se você não consegue apontar a linha, o achado não
   entra no relatório.
5. **Não invente severidade.** Use a escala de `references/antipatterns.md`.
6. **Não apague dados do usuário.** Banco, `.env` e arquivos não versionados ficam intactos.

## Fase 1 — Análise do Projeto (somente leitura)

Leia `references/project-analysis.md` e siga as heurísticas de detecção. Resumo do fluxo:

1. Identifique linguagem e gerenciador de pacotes pelo manifesto na raiz.
2. Extraia framework e versão do manifesto/lockfile; confirme pelos imports do código.
3. Localize o entry point e inventarie **todas** as rotas (método + caminho + handler).
4. Detecte a camada de dados: driver, ORM, e as tabelas/coleções (DDL, models, migrations).
5. Classifique cada arquivo-fonte em uma camada e aponte onde as responsabilidades se misturam.
6. Infira o domínio a partir de tabelas, rotas e dados de seed.
7. Conte arquivos-fonte e linhas (exclua dependências, lockfiles, build e a própria skill).

Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão detectada>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes>
Domain:        <domínio da aplicação em uma linha>
Architecture:  <arquitetura atual — quantos arquivos, quais camadas existem ou faltam>
Source files:  <N> files analyzed | ~<N> lines of code
Entry point:   <arquivo:linha>
Routes:        <N> endpoints
DB tables:     <lista>
================================
```

Não peça confirmação aqui. Siga direto para a Fase 2.

## Fase 2 — Auditoria (somente leitura)

1. Leia `references/antipatterns.md` (catálogo completo) e `references/report-template.md`
   (formato de saída).
2. Para cada anti-pattern do catálogo, aplique os sinais de detecção ao código. Trabalhe
   arquivo por arquivo para não perder ocorrência — e confirme cada suspeita abrindo o
   trecho antes de registrar.
3. Verifique **APIs deprecated** contra a seção correspondente do catálogo — é item
   obrigatório do relatório quando aplicável.
4. Monte o relatório seguindo o template: sumário por severidade, findings ordenados de
   CRITICAL para LOW, cada um com arquivo:linha, descrição, impacto e recomendação.
5. Salve em `reports/audit-<nome-do-projeto>.md` (crie o diretório se não existir). Se o
   usuário indicou outro caminho, use o dele.
6. Imprima o relatório e **pare**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Aguarde a resposta. Qualquer coisa diferente de uma confirmação afirmativa encerra a skill
sem modificar arquivo algum. Se o usuário pedir para revisar ou contestar um finding,
ajuste o relatório e pergunte de novo.

## Fase 3 — Refatoração (modifica arquivos)

Leia `references/mvc-guidelines.md` (estrutura-alvo) e `references/refactor-playbook.md`
(transformação por anti-pattern) antes de editar qualquer coisa.

**Passo 0 — Baseline.** Siga `references/validation.md`: instale dependências, suba a
aplicação, exercite todos os endpoints inventariados na Fase 1 e salve status + corpo de
cada resposta. Sem baseline não há como validar depois. Se a aplicação não sobe nem antes da
refatoração, registre isso e valide por boot + import, deixando claro no relatório final.

**Passo 1 — Plano.** Derive a estrutura-alvo do domínio real do projeto (um model e um
controller por agregado — não por arquivo existente). Liste os arquivos que serão criados,
movidos e removidos.

**Passo 2 — Execução.** Aplique as transformações do playbook, na ordem:
config e segredos → camada de dados/models → services (se houver regra que não pertence ao
controller) → controllers → views/routes → middlewares (erro, auth, log) → composition root.
Depois remova os arquivos legados que ficaram sem uso.

Regras de execução:
- Cada anti-pattern CRITICAL ou HIGH do relatório tem que ser resolvido ou justificado.
- Segredos saem do código para configuração por ambiente. Crie `.env.example` com as chaves
  (sem valores reais) e garanta que `.env` está no `.gitignore`.
- Não introduza dependência nova sem necessidade; se precisar (ex.: biblioteca de hash),
  adicione ao manifesto e diga por quê.
- Preserve os dados de seed/demo — se o boot original populava o banco, o novo também deve.

**Passo 3 — Validação.** Rode o protocolo de `references/validation.md`: boot limpo, todos
os endpoints do baseline reexecutados, respostas comparadas. Corrija e repita até passar.
Se um endpoint mudou de propósito (ex.: rota que executava SQL arbitrário foi removida por
segurança), isso não é regressão — é resultado esperado, e precisa aparecer na saída.

**Passo 4 — Relatório final.** Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore da estrutura criada>

Anti-patterns resolved: <N>/<total> (<lista dos não resolvidos + motivo>)

Validation
  <✓|✗> Application boots without errors
  <✓|✗> <N>/<N> endpoints respond as before
  <✓|✗> No hardcoded secrets remaining
  <✓|✗> Layer boundaries respected
================================
```

Nunca declare `✓` em item que você não executou de fato.

## Arquivos de referência

| Arquivo | Quando ler |
|---|---|
| `references/project-analysis.md` | Início da Fase 1 — heurísticas de detecção de stack, rotas, banco e camadas |
| `references/antipatterns.md` | Início da Fase 2 — catálogo, sinais de detecção e severidades (inclui APIs deprecated) |
| `references/report-template.md` | Ao escrever o relatório da Fase 2 |
| `references/mvc-guidelines.md` | Início da Fase 3 — estrutura-alvo, responsabilidade de cada camada, regras de dependência |
| `references/refactor-playbook.md` | Durante a Fase 3 — transformação concreta (antes/depois) de cada anti-pattern |
| `references/validation.md` | Passo 0 e Passo 3 da Fase 3 — baseline, boot e smoke test dos endpoints |
