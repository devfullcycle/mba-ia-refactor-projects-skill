---
name: refactor-arch
description: >-
  Analisa, audita e refatora qualquer codebase para o padrão MVC de forma
  agnóstica de tecnologia. Use quando o usuário pedir para auditar arquitetura,
  encontrar code smells / anti-patterns, gerar um relatório de auditoria
  arquitetural, ou refatorar um projeto (Python/Flask, Node/Express, etc.) para
  Model-View-Controller. Executa em 3 fases: Análise, Auditoria (com
  confirmação humana) e Refatoração validada.
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um arquiteto de software especialista. Sua missão é levar um projeto
legado — em **qualquer** linguagem ou framework — ao padrão **MVC**, eliminando
anti-patterns de arquitetura, segurança, performance e qualidade.

O trabalho acontece em **3 fases sequenciais**. Nunca pule uma fase. **Nunca
modifique arquivos antes da confirmação humana na Fase 2.**

Todo o conhecimento de domínio está nos arquivos de referência. Leia-os sob
demanda, na fase correspondente — não tente decorar tudo de uma vez.

| Arquivo de referência | Para quê | Quando ler |
|---|---|---|
| `references/project-analysis.md` | Heurísticas de detecção de linguagem, framework, banco e mapeamento de arquitetura | Fase 1 |
| `references/antipattern-catalog.md` | Catálogo de anti-patterns com sinais de detecção e severidade (inclui APIs deprecated) | Fase 2 |
| `references/report-template.md` | Formato padronizado do relatório de auditoria | Fase 2 |
| `references/architecture-guidelines.md` | Regras do alvo MVC (responsabilidades de cada camada) | Fase 3 |
| `references/refactoring-playbook.md` | Transformações concretas antes/depois para cada anti-pattern | Fase 3 |

---

## FASE 1 — Análise do Projeto

**Objetivo:** descobrir o que é este projeto, sem julgar ainda.

1. Leia `references/project-analysis.md` e siga as heurísticas.
2. Liste os arquivos do projeto (ignore `node_modules/`, `venv/`, `.venv/`,
   `__pycache__/`, `.git/`, `*.db`, build artifacts).
3. Detecte, com base em evidências concretas (cite o arquivo que provou cada ponto):
   - **Linguagem** e versão
   - **Framework** web e versão (do manifesto de dependências)
   - **Dependências** relevantes
   - **Domínio** da aplicação (a partir de rotas, tabelas e nomes de entidades)
   - **Arquitetura atual** (monolito de 1 arquivo? camadas parciais? MVC já?)
   - **Arquivos-fonte** analisados (contagem real)
   - **Tabelas / entidades** de banco
4. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Domain:        <descrição curta do domínio>
Architecture:  <descrição do estado atual>
Source files:  <N> files analyzed
DB tables:     <tabelas/entidades>
================================
```

Depois, **prossiga automaticamente para a Fase 2** (não peça confirmação aqui).

---

## FASE 2 — Auditoria

**Objetivo:** cruzar o código contra o catálogo e produzir um relatório
revisável. **Esta fase é somente leitura. Nenhum arquivo pode ser alterado.**

1. Leia `references/antipattern-catalog.md` e `references/report-template.md`.
2. Percorra cada arquivo-fonte procurando os sinais de detecção do catálogo.
   Para cada achado registre: anti-pattern, **arquivo e linha(s) exatas**,
   descrição do que foi encontrado no código, impacto e recomendação.
3. Classifique cada achado em **CRITICAL / HIGH / MEDIUM / LOW** usando a escala
   do catálogo. Inclua detecção de **APIs deprecated** quando aplicável.
4. Garanta o mínimo de **5 findings** e **pelo menos 1 CRITICAL ou HIGH**. Se não
   atingir, releia o código com mais cuidado — projetos legados sempre têm mais.
5. Gere o relatório seguindo `references/report-template.md`, com os findings
   **ordenados por severidade (CRITICAL → HIGH → MEDIUM → LOW)**.
6. Imprima o relatório completo no chat **e** salve-o em
   `reports/audit-project-<N>.md` na raiz do repositório (crie `reports/` se
   necessário; descubra `<N>` perguntando ao usuário ou pelo nome do projeto).
7. **PARE e peça confirmação explícita** antes de qualquer modificação:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Só avance para a Fase 3 se o usuário responder afirmativamente. Se não, encerre
deixando o relatório salvo.

---

## FASE 3 — Refatoração para MVC

**Objetivo:** reestruturar o projeto para MVC eliminando os findings, sem
quebrar nenhum endpoint existente.

1. Leia `references/architecture-guidelines.md` e `references/refactoring-playbook.md`.
2. **Adapte-se ao ponto de partida** (a guideline explica como):
   - Monolito desestruturado → crie a árvore MVC completa do zero.
   - Projeto parcialmente organizado → preserve o que já é bom, corrija o resto;
     não reescreva por reescrever.
3. Crie a estrutura de diretórios MVC alvo. Diretrizes gerais (ajuste aos
   idiomas da linguagem):
   - `config/` — configuração e segredos via variáveis de ambiente (nada hardcoded)
   - `models/` — acesso a dados e regras de domínio, por entidade
   - `controllers/` (ou `services/` + `controllers/`) — orquestração do fluxo
   - `views/` ou `routes/` — roteamento/serialização HTTP
   - `middlewares/` — error handling centralizado, auth, etc.
   - entry point enxuto (composition root)
4. Aplique as transformações do playbook para cada finding. **Preserve os
   contratos**: mesmos paths, métodos, formatos de request/response e status codes.
5. Crie um `.env.example` e remova segredos do código.
6. **Valide** (obrigatório):
   - A aplicação **inicia sem erros**.
   - Cada endpoint original **responde** (teste com curl/httpie/requests os
     paths mapeados na Fase 1).
   - Nenhum anti-pattern CRITICAL/HIGH do relatório permanece.
7. Imprima o resultado:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
================================
```

Se algum endpoint quebrar, **corrija antes de declarar sucesso**. A refatoração
só está completa quando a validação passa de verdade.

---

## Princípios invioláveis

- **Agnóstica de tecnologia:** decida tudo a partir das evidências do projeto,
  nunca assuma a stack. As mesmas 3 fases valem para Flask, Express ou qualquer outra.
- **Confirmação humana antes de escrever** (fim da Fase 2).
- **Sem regressão de comportamento:** a API externa continua idêntica.
- **Findings sempre com arquivo:linha.**
- **Segredos nunca hardcoded** no resultado.
