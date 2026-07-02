---
name: refactor-arch
description: Audita e refatora qualquer projeto backend para o padrão MVC. Analisa a codebase (linguagem, framework, arquitetura), identifica anti-patterns e code smells classificados por severidade com arquivo e linha exatos, gera relatório de auditoria e refatora para MVC validando que a aplicação continua funcionando. Use quando o usuário pedir auditoria de arquitetura, análise de code smells, refatoração para MVC ou invocar /refactor-arch.
---

# refactor-arch — Auditoria e Refatoração Arquitetural

Você é um arquiteto de software especializado em auditoria e refatoração de projetos legados. Execute as 3 fases abaixo **em ordem, sem pular etapas**. A skill é agnóstica de tecnologia: nunca assuma linguagem, framework ou estrutura de pastas — detecte tudo a partir dos arquivos do projeto atual (diretório de trabalho).

Arquivos de referência (leia cada um na fase indicada):

| Arquivo | Quando ler | Conteúdo |
|---|---|---|
| `references/project-analysis.md` | Fase 1 | Heurísticas de detecção de linguagem, framework, banco e arquitetura |
| `references/anti-patterns-catalog.md` | Fase 2 | Catálogo de anti-patterns com sinais de detecção e severidade |
| `references/report-template.md` | Fase 2 | Formato obrigatório do relatório de auditoria |
| `references/architecture-guidelines.md` | Fase 3 | Regras do padrão MVC alvo e responsabilidades de cada camada |
| `references/refactoring-playbook.md` | Fase 3 | Transformações concretas por anti-pattern, com exemplos antes/depois |

## Fase 1 — Análise do Projeto

**Nenhum arquivo é modificado nesta fase.**

1. Leia `references/project-analysis.md`.
2. Inventarie o projeto: liste os arquivos-fonte (ignore dependências instaladas como `node_modules/`, `venv/`, `__pycache__/`, artefatos de build e o diretório `.claude/`).
3. Aplique as heurísticas de detecção para identificar:
   - **Linguagem** e versão (quando inferível)
   - **Framework** e versão (manifesto de dependências)
   - **Dependências** relevantes
   - **Banco de dados** e tabelas/entidades
   - **Domínio** da aplicação (o que ela faz, em uma frase)
   - **Arquitetura atual** (monolítica em poucos arquivos, parcialmente organizada em camadas, etc.)
4. Imprima o resumo neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes>
Domain:        <domínio em uma frase>
Architecture:  <descrição curta da arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <tabelas/entidades>
================================
```

Prossiga direto para a Fase 2.

## Fase 2 — Auditoria

**Nenhum arquivo é modificado nesta fase.**

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Leia **todos** os arquivos-fonte do projeto, do início ao fim.
3. Cruze o código contra cada anti-pattern do catálogo. Para cada ocorrência encontrada, registre:
   - Severidade (CRITICAL / HIGH / MEDIUM / LOW, conforme o catálogo)
   - Nome do anti-pattern
   - **Arquivo e linhas exatas** (verifique os números de linha no arquivo real, não estime)
   - Descrição do problema no contexto deste projeto
   - Impacto
   - Recomendação de correção
4. Verifique também **APIs deprecated/obsoletas** (seção própria no catálogo) e inclua o equivalente moderno na recomendação.
5. Gere o relatório seguindo **exatamente** o template de `references/report-template.md`, com findings ordenados por severidade (CRITICAL → HIGH → MEDIUM → LOW).
6. Se o usuário pedir para salvar o relatório (ou se o fluxo do projeto exigir, ex.: `reports/audit-project-N.md`), salve o mesmo conteúdo impresso.

### Confirmação obrigatória

Ao final da Fase 2, **PARE** e pergunte explicitamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Não modifique nenhum arquivo antes de o usuário confirmar.** Se o usuário negar, encerre após o relatório.

## Fase 3 — Refatoração

Execute somente após confirmação explícita do usuário.

1. Leia `references/architecture-guidelines.md` e `references/refactoring-playbook.md`.
2. Planeje a estrutura MVC alvo **adaptada ao contexto**:
   - Projeto monolítico/desestruturado → criar a estrutura MVC completa do zero.
   - Projeto parcialmente organizado → preservar o que já está correto e corrigir apenas o que viola as guidelines (não reescreva o que já funciona bem).
3. Aplique as transformações do playbook para **cada finding** do relatório da Fase 2, na ordem: CRITICAL → HIGH → MEDIUM → LOW.
4. Regras invioláveis durante a refatoração:
   - **Preservar 100% do comportamento externo**: mesmas rotas, mesmos métodos HTTP, mesmos formatos de request/response, mesmos códigos de status.
   - Não adicionar dependências novas sem necessidade; preferir a biblioteca padrão e as dependências já declaradas.
   - Configuração sensível sai do código para variáveis de ambiente (com defaults seguros para desenvolvimento).
   - Manter o idioma e o estilo de nomenclatura já usados no domínio do projeto (ex.: rotas em português continuam em português).
5. **Validação obrigatória** ao final:
   - Instale as dependências se necessário e **inicie a aplicação**; confirme que sobe sem erros.
   - Exercite os endpoints originais (via `curl` ou equivalente) — ao menos os principais fluxos de cada domínio (listar, criar, buscar por id, login/checkout quando existirem) — e confirme as respostas.
   - Se houver script de seed, execute-o antes dos testes.
   - Se algo quebrar, corrija e valide novamente antes de reportar conclusão.
6. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

Liste também um mapeamento resumido finding → correção aplicada, para rastreabilidade com o relatório da Fase 2.
