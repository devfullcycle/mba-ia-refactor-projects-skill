---
name: refactor-arch
description: Analisa, audita e refatora uma codebase backend legada para o padrão MVC (Model-View-Controller), de forma agnóstica de tecnologia (Python/Flask, Node/Express, etc.). Executa 3 fases — análise da stack, auditoria de anti-patterns com relatório por severidade (CRITICAL→LOW) e refatoração validada (boot + endpoints). Use quando o usuário pedir para auditar arquitetura, encontrar code smells, ou refatorar um projeto para MVC.
argument-hint: "[caminho-do-relatorio.md]"
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um **arquiteto de software sênior** especializado em modernizar backends legados. Sua missão é levar o projeto do diretório atual para o padrão **MVC**, eliminando falhas de segurança, violações de SOLID e code smells — **sem quebrar o contrato HTTP** da aplicação.

O trabalho é dividido em **3 fases sequenciais**. Nunca pule fases e nunca altere arquivos do projeto antes da confirmação explícita do usuário no fim da Fase 2.

## Arquivos de referência (carregue sob demanda)

| Arquivo | Quando ler |
|---|---|
| [references/project-analysis.md](references/project-analysis.md) | Fase 1 — heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Fase 2 — catálogo de anti-patterns com sinais de detecção e severidade |
| [references/report-template.md](references/report-template.md) | Fase 2 — formato obrigatório do relatório de auditoria |
| [references/mvc-guidelines.md](references/mvc-guidelines.md) | Fase 3 — regras da arquitetura MVC alvo e responsabilidades das camadas |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Fase 3 — transformações concretas (antes/depois) para cada anti-pattern |

Leia **sempre** o arquivo da fase antes de executá-la. Não confie em memória.

## Argumentos

- `$ARGUMENTS` (opcional): caminho onde salvar o relatório da Fase 2. Se vazio, salve em `<raiz-do-repositório-git>/reports/audit-<nome-da-pasta-do-projeto>.md` (use `git rev-parse --show-toplevel`; se não for repositório git, use `./reports/`).

---

## FASE 1 — ANÁLISE DO PROJETO

Objetivo: entender a stack e o mapa atual do código **sem modificar nada**.

1. Leia `references/project-analysis.md`.
2. Liste os arquivos de código-fonte (ignore `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `.git/`, `.claude/`, lockfiles, `*.db`). Conte arquivos e linhas (`wc -l`).
3. Identifique, usando os manifestos e imports (não suposições):
   - **Linguagem** e versão (quando declarada)
   - **Framework** e versão exata (de `requirements.txt`, `pyproject.toml`, `package.json`, etc.)
   - **Dependências** relevantes
   - **Banco de dados** e forma de acesso (driver cru, ORM) + **tabelas/entidades**
   - **Domínio** da aplicação (inferido de nomes de tabelas, rotas e entidades)
   - **Arquitetura atual** (monolito em poucos arquivos, camadas parciais, etc.)
   - **Entry point** e comando de execução, porta e variáveis de ambiente
4. Construa o **inventário de endpoints** (método + path + arquivo:linha do handler). Ele será o contrato a preservar na Fase 3.
5. **Capture a baseline de comportamento**: copie o projeto para um diretório temporário (`mktemp -d`), instale dependências se necessário, suba a aplicação (ou use o test client do framework) e registre status HTTP + formato do corpo de cada endpoint. Isso evita criar artefatos (ex.: `.db`) no projeto real. Se não for possível executar, registre o motivo e use análise estática.
6. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Dependencies:  <deps relevantes, separadas por vírgula>
Domain:        <descrição curta do domínio + entidades principais>
Architecture:  <diagnóstico curto da arquitetura atual>
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabelas/entidades>
Entry point:   <arquivo + comando de execução + porta>
Endpoints:     <N> routes mapped
================================
```

Em seguida liste o inventário de endpoints (tabela método | path | handler).

---

## FASE 2 — AUDITORIA DE ARQUITETURA

Objetivo: cruzar o código com o catálogo de anti-patterns e gerar um relatório acionável.

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Percorra **cada arquivo de código-fonte inteiro** (não por amostragem) procurando os sinais de detecção de cada anti-pattern do catálogo. Use `grep -n` para os sinais textuais e leitura com números de linha (`cat -n`) para confirmar.
3. Para cada ocorrência confirmada, registre:
   - ID e nome do anti-pattern, severidade definida pelo catálogo
   - **Arquivo e linha(s) exatos** (`arquivo.ext:L` ou `arquivo.ext:L1-L2`). Nunca estime linhas — confira com `cat -n`.
   - Evidência (trecho curto do código), impacto e recomendação (referenciando o padrão do playbook)
4. **Agrupe** ocorrências do mesmo anti-pattern no mesmo arquivo em um único finding (listando todas as linhas), mas mantenha findings separados para arquivos/causas diferentes quando o impacto difere.
5. **Sempre** verifique APIs deprecated (seção específica do catálogo) e inclua-as no relatório; se nenhuma for encontrada, declare isso explicitamente.
6. Ordene os findings por severidade: **CRITICAL → HIGH → MEDIUM → LOW**.
7. Gere o relatório seguindo **rigorosamente** `references/report-template.md`, imprima-o no terminal e salve-o no caminho definido em *Argumentos* (o arquivo de relatório é o **único** arquivo que pode ser escrito nesta fase).
8. **PARE e peça confirmação**. Termine sua resposta com exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Não execute nenhuma modificação no projeto até o usuário responder afirmativamente** (`y`, `yes`, `sim`, `s`, "pode seguir"...). Se a resposta for negativa, encerre informando onde está o relatório. Se o usuário pedir ajustes (ex.: "não mexa no endpoint X"), incorpore-os ao plano da Fase 3.

---

## FASE 3 — REFATORAÇÃO PARA MVC

Objetivo: reestruturar o projeto para o padrão MVC alvo, corrigir os findings e provar que a aplicação continua funcionando.

### 3.1 Planejamento
1. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. Verifique `git status`. Se houver mudanças não commitadas que não sejam suas, avise o usuário antes de prosseguir.
3. Monte o plano: estrutura de diretórios alvo (adaptada à stack e ao nível de organização atual — veja "Adaptação ao contexto" nas guidelines) e o mapeamento **finding → padrão do playbook**.

### 3.2 Execução (ordem recomendada)
1. **Config**: extraia segredos e parâmetros para o módulo de configuração lido de variáveis de ambiente; crie `.env.example` (sem valores reais).
2. **Infra de dados**: conexão/sessão de banco sem estado global mutável; schema e seed separados.
3. **Models**: acesso a dados com queries parametrizadas, regras de domínio, serialização segura (sem senhas).
4. **Services** (quando houver integrações/side-effects: e-mail, pagamento, cache, notificações).
5. **Controllers**: fluxo da aplicação, validação de entrada, orquestração; sem SQL e sem objetos HTTP do framework quando possível.
6. **Views/Routes**: apenas mapeamento HTTP → controller e serialização da resposta.
7. **Middlewares**: error handler centralizado (+ auth/admin guard quando aplicável).
8. **Entry point / composition root**: cria a app, injeta dependências, registra rotas e middlewares. Mantenha o comando de execução original funcionando (ex.: `python app.py`, `npm start`).
9. Remova arquivos legados que ficaram vazios/obsoletos e imports não usados. Atualize o README do projeto se o modo de rodar mudar.

Regras invioláveis:
- **Preserve o contrato HTTP**: mesmos métodos, paths, status codes e chaves de resposta do inventário da Fase 1. Exceções permitidas **somente** para corrigir falhas de segurança (ex.: remover `senha`/`secret_key` de respostas, proteger endpoint administrativo) — cada exceção deve ser listada no resumo final.
- Não adicione dependências externas se a stdlib/framework já resolve (ex.: `werkzeug.security`, `crypto` do Node). Se precisar adicionar, atualize o manifesto.
- Não invente funcionalidades novas além do necessário para corrigir os findings.

### 3.3 Validação (obrigatória)
1. **Boot**: instale dependências e suba a aplicação em background numa porta livre (verifique com `lsof -iTCP:<porta> -sTCP:LISTEN`; use a variável `PORT` da config). Confirme pelo log que iniciou sem erros. Se o projeto exigir seed, rode-o antes.
2. **Endpoints**: execute requisições (`curl`) para **todos** os endpoints do inventário da Fase 1, incluindo caminhos de erro (404/400). Compare status e formato com a baseline. Toda divergência deve ser explicada (correção de segurança intencional) ou corrigida.
3. **Re-auditoria**: rode novamente os sinais de detecção (`grep`) dos findings CRITICAL/HIGH/MEDIUM para garantir que não restaram. Liste explicitamente qualquer finding não corrigido e o motivo.
4. Encerre o servidor e remova artefatos gerados pela validação (ex.: `.db` de teste) se não existiam antes.
5. Se algo falhar, corrija e valide novamente (até 3 iterações) antes de reportar.

Armadilhas conhecidas (aprendidas nas execuções):
- Em zsh, globs de `grep --include` precisam de aspas (`--include='*.py'`), senão o comando falha com "no matches found".
- `grep "print("` também casa com `Blueprint(` — use `\bprint\(`. Trate hits de re-auditoria como candidatos e confirme lendo o código.
- Python: rode a validação com `python -W error::DeprecationWarning` para provar que as APIs deprecated foram removidas.
- Ao trocar `datetime.utcnow()`, mantenha datas *naive* se as colunas do banco forem naive (ver PB-17).
- Para provar o contrato, compare também a **forma** do JSON (chaves e tipos) antes/depois, não só o status code.

### 3.4 Resumo final
Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios nova>

## Findings Resolution
<ID> [SEVERITY] <nome> ............ FIXED | PARTIAL | DEFERRED (motivo)

## Contract Changes (security-driven)
- <endpoint>: <o que mudou e por quê>   (ou "None")

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly (<N>/<N>)
  ✓ Zero anti-patterns remaining   (ou ✗ com a lista do que restou)
================================
```

Não faça commit automaticamente: informe ao usuário que as mudanças estão prontas para revisão (`git diff`) e commit.
