---
name: refactor-arch
description: >-
  Audita e refatora qualquer codebase de backend para o padrão MVC, de forma agnóstica de
  tecnologia (Python/Flask, Node.js/Express, e outras stacks). Executa em 3 fases sequenciais —
  Análise (detecta stack, banco, domínio e arquitetura), Auditoria (pente-fino de engenheiro
  sênior que classifica problemas de arquitetura, segurança, SOLID, concorrência e aderência a
  MVC por severidade CRITICAL/HIGH/MEDIUM/LOW, gera relatório e pede confirmação) e Refatoração
  (reestrutura para MVC em loop auto-corretivo e valida subindo a aplicação). Use esta skill
  SEMPRE que o usuário pedir para refatorar, auditar, reestruturar, "arrumar a arquitetura",
  aplicar MVC, achar code smells / anti-patterns, avaliar qualidade de código ou modernizar um
  projeto legado — mesmo que ele não diga "MVC" ou "auditoria" explicitamente. Também dispara
  com o comando /refactor-arch.
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você atua como **engenheiro de software com mais de 30 anos de mercado**, especialista em
arquitetura, segurança e qualidade. Seu trabalho tem 3 fases sequenciais. Execute-as **em ordem**
e **nunca modifique arquivos antes de o usuário confirmar** (gate entre Fase 2 e Fase 3).

Esta skill é **agnóstica de tecnologia e de localização**: ela roda no diretório de trabalho
atual (o projeto), qualquer que seja a stack. Não assuma nomes de arquivos, framework ou estrutura
— **detecte** tudo lendo o projeto.

## Arquivos de referência

Carregue cada um **no início da fase correspondente** (não tente segurar tudo em memória de uma vez):

| Arquivo | Quando ler | Para quê |
|---|---|---|
| `references/01-project-analysis.md` | Fase 1 | Heurísticas de detecção de stack, banco, domínio e arquitetura |
| `references/02-antipattern-catalog.md` | Fase 2 | Catálogo de anti-patterns com sinais de detecção e severidade (inclui APIs deprecated) |
| `references/03-report-templates.md` | Fases 1, 2, 3 | Templates de saída **a serem seguidos à risca** |
| `references/04-mvc-guidelines.md` | Fases 2 e 3 | Regras do MVC-alvo (camadas e responsabilidades) |
| `references/05-refactoring-playbook.md` | Fase 3 | Transformações antes/depois + loop de correção + validação |

Os templates de saída não são opcionais nem "aproximados": reproduza a estrutura, os rótulos, a
ordem das seções e os separadores (`====`) **exatamente** como em `03-report-templates.md`.

---

## Fase 1 — Análise

**Objetivo:** detectar a stack, mapear a arquitetura atual e imprimir um resumo.

1. Leia `references/01-project-analysis.md` e siga as heurísticas.
2. Explore o projeto: manifestos de dependências, arquivos-fonte, definição de rotas, camada de
   dados/schema. Leia de verdade os arquivos principais — não infira só pelos nomes.
3. Determine: linguagem (+runtime), framework (+versão), dependências diretas principais, banco
   (engine + forma de acesso + nuances como *in-memory*), domínio (entidades principais),
   arquitetura atual (resumo de 1 linha), nº de arquivos-fonte, tabelas do banco.
4. Imprima o bloco **`PHASE 1: PROJECT ANALYSIS`** exatamente como o template.
   Campos sem valor no projeto são **omitidos** (não imprima "N/A").

Depois de imprimir, siga direto para a Fase 2.

---

## Fase 2 — Auditoria

**Objetivo:** passar um pente-fino no projeto, classificar todos os problemas por severidade,
avaliar aderência a MVC, gerar o relatório e **pedir confirmação**.

1. Leia `references/02-antipattern-catalog.md` e `references/04-mvc-guidelines.md`.
2. Audite o projeto inteiro procurando: falhas de arquitetura, falhas de segurança, problemas de
   qualidade, concorrência, bugs, anti-patterns, violações de SOLID **e violações de MVC**.
3. Para cada problema, produza um finding com **arquivo e linhas exatas**, descrição, impacto e
   recomendação, classificado como CRITICAL / HIGH / MEDIUM / LOW (critérios em
   `02-antipattern-catalog.md`).
4. Avalie a **aderência a MVC** e produza a seção `MVC Adherence` (score + checklist por camada).
   As violações de MVC também entram como findings individuais com localização exata.
5. Ordene os findings por severidade decrescente (CRITICAL → LOW).
6. Monte o relatório no formato **`ARCHITECTURE AUDIT REPORT`** (com `Summary`, `MVC Adherence`,
   `Findings` e o rodapé `Total: N findings`). Este relatório deve ser:
   - **impresso no console**, e
   - **salvo em arquivo**. Determine o caminho assim:
     - Ache a raiz do repositório git (suba diretórios até encontrar `.git`).
     - Grave em `<raiz>/reports/audit-project-<N>.md`, onde `<N>` é o próximo número livre
       olhando os `audit-project-*.md` já existentes em `reports/` (começa em 1).
     - Se não houver repositório git acima, use `./reports/` no próprio projeto.
     - Crie a pasta `reports/` se não existir.
7. **PARE e peça confirmação** antes de tocar em qualquer arquivo:

   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

   Prossiga para a Fase 3 **apenas** se o usuário responder afirmativamente. Se disser não, encerre
   sem modificar nada.

---

## Fase 3 — Refatoração

**Objetivo:** reestruturar o projeto para MVC e corrigir os findings, validando que a aplicação
continua funcionando. **Só execute após a confirmação do usuário.**

1. Leia `references/05-refactoring-playbook.md` e revisite `references/04-mvc-guidelines.md`.
2. Use como **input o relatório salvo na Fase 2** (`reports/audit-project-<N>.md`). Cada finding
   listado ali precisa ser endereçado.
3. Reestruture para as camadas MVC-alvo (config, models, views/routes, controllers, middlewares,
   entrypoint), adaptando o **layout à convenção da linguagem** (ver `04-mvc-guidelines.md`).
   **Preserve os contratos externos** — mesmos paths, métodos HTTP, formato de resposta e schema
   de dados. As mudanças são internas.
4. **Loop de correção controlado (máximo de 3 iterações):**
   1. Aplique as correções pendentes (MVC + findings).
   2. **Re-audite internamente** com os mesmos critérios da Fase 2 para verificar se (a) todos os
      problemas foram resolvidos e (b) nenhum problema novo foi introduzido. Esta re-auditoria é
      **silenciosa** — não imprima os findings; use-a só para decidir se continua.
   3. Se ainda houver problemas → nova iteração. Se resolveu tudo → saia do loop com sucesso.
   4. Pare ao resolver tudo **ou** ao completar 3 iterações (o que vier primeiro).
5. **Valide subindo a aplicação de verdade** (obrigatório — a app não pode quebrar):
   - Instale dependências (`pip install` / `npm install`).
   - Inicie o servidor num processo em background.
   - Faça requisições HTTP reais a **todos os endpoints originais** e confirme que respondem.
   - Encerre o servidor.
   - Detalhes e comandos por stack em `references/05-refactoring-playbook.md`.
6. Imprima o bloco **`PHASE 3: REFACTORING COMPLETE`** com a nova estrutura de diretórios e o bloco
   `Validation`. A linha de anti-patterns deve **refletir o estado real**:
   - `✓ Zero anti-patterns remaining` se o loop resolveu tudo, ou
   - `⚠ <N> findings remaining after 3 loops:` com a lista, se sobrou algo.
   `Application boots without errors` e `All endpoints respond correctly` **têm que passar** em
   qualquer caso — não marque como concluído com a aplicação quebrada.

---

## Regras gerais

- **Fidelidade aos templates:** siga `03-report-templates.md` à risca em todas as fases.
- **Gate humano obrigatório:** nunca modifique arquivos antes do `y` na Fase 2.
- **Agnóstica:** detecte a stack; não hardcode nomes de arquivos ou frameworks.
- **Honestidade:** o relatório de validação reflete o resultado real, não o ideal.
- **Preservação de comportamento:** a refatoração não muda o contrato externo da API.
