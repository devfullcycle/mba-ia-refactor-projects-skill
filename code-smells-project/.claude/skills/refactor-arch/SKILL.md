# Skill: refactor-arch
## Refatoração Arquitetural Automatizada para Padrão MVC

Você é um especialista em arquitetura de software e refatoração de código legado. Sua missão é analisar uma codebase, auditar problemas arquiteturais e de segurança, e refatorar o projeto para o padrão MVC, tornando-o mais seguro, maintível e testável.

Execute as três fases a seguir **sequencialmente**. Nunca pule fases nem modifique arquivos antes da confirmação do usuário na Fase 2.

---

## FASE 1 — ANÁLISE DO PROJETO

**Objetivo:** Entender completamente o projeto antes de qualquer auditoria ou mudança.

### Passos

1. **Detectar a stack** usando as heurísticas de `project-analysis.md`:
   - Identificar linguagem principal (Python, JavaScript, TypeScript, etc.)
   - Identificar framework (Flask, Express, Django, Fastify, etc.) e versão
   - Identificar banco de dados (SQLite, PostgreSQL, MySQL, MongoDB, in-memory, etc.)
   - Identificar bibliotecas e dependências relevantes

2. **Mapear o projeto**:
   - Listar todos os arquivos de código-fonte (excluir `node_modules/`, `venv/`, `.git/`, `__pycache__/`)
   - Contar total de linhas de código
   - Identificar o domínio da aplicação (e-commerce, task manager, LMS, etc.)
   - Mapear a arquitetura atual (monolítica, MVC parcial, layered, etc.)
   - Identificar as tabelas/collections do banco de dados

3. **Imprimir o resumo** no seguinte formato exato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <principais dependências>
Domain:        <domínio da aplicação>
Architecture:  <arquitetura atual — descreva em 1 linha>
Source files:  <número> files analyzed
DB tables:     <tabelas identificadas>
================================
```

Após imprimir o resumo, confirme: "Phase 1 complete. Starting Phase 2 — Architecture Audit..."

---

## FASE 2 — AUDITORIA DE ARQUITETURA

**Objetivo:** Identificar todos os problemas arquiteturais, de segurança e qualidade de código.

### Passos

1. **Ler todos os arquivos de código-fonte** identificados na Fase 1 (incluindo arquivos de configuração como `package.json`, `requirements.txt`, `.env`).

2. **Cruzar o código contra o catálogo de anti-patterns** em `anti-patterns-catalog.md`:
   - Verificar cada anti-pattern do catálogo
   - Anotar arquivo exato e número(s) de linha(s) para cada ocorrência
   - Classificar severidade: CRITICAL, HIGH, MEDIUM, ou LOW
   - Identificar também uso de APIs deprecated

3. **Gerar o relatório de auditoria** seguindo o template em `report-template.md`. O relatório deve:
   - Ordenar findings por severidade (CRITICAL → HIGH → MEDIUM → LOW)
   - Incluir arquivo e linhas exatos para cada finding
   - Incluir impacto e recomendação para cada finding
   - Totalizar findings por severidade

4. **Imprimir o relatório completo** para o usuário revisar.

5. **PAUSAR e pedir confirmação** com a mensagem:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**IMPORTANTE:** Aguardar resposta do usuário. Se responder "n" ou qualquer coisa diferente de "y", encerrar sem modificar nenhum arquivo. Só prosseguir com "y" ou "yes".

---

## FASE 3 — REFATORAÇÃO PARA MVC

**Objetivo:** Reestruturar o projeto para o padrão MVC, eliminando todos os anti-patterns identificados.

### Passos

1. **Planejar a nova estrutura MVC** com base em `architecture-guidelines.md`:
   - Definir a estrutura de diretórios alvo
   - Mapear cada arquivo/função atual para a nova camada MVC
   - Identificar quais anti-patterns do relatório serão corrigidos

2. **Executar a refatoração** seguindo o `refactoring-playbook.md`:
   - Criar a estrutura de diretórios MVC
   - Mover/refatorar código respeitando as responsabilidades de cada camada
   - Corrigir todos os problemas de segurança identificados (prioridade máxima: CRITICAL)
   - Eliminar duplicações de código
   - Adicionar tratamento de erros adequado
   - Criar arquivo de configuração separado (sem hardcoded secrets)
   - Criar entry point limpo

3. **Mostrar a nova estrutura de arquivos** criada:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Changes Made
- <lista de mudanças principais>
================================
```

4. **Validar o resultado**:
   - Tentar inicializar a aplicação (instalar dependências se necessário)
   - Verificar que não há erros de importação ou sintaxe
   - Fazer uma chamada de teste para o endpoint mais básico (ex: `/`, `/health`, `/api/status`)
   - Reportar resultado da validação

5. **Imprimir sumário final**:

```
================================
VALIDATION RESULTS
================================
✓/✗ Application boots without errors
✓/✗ Basic endpoint responds correctly
✓/✗ No CRITICAL security issues remaining
✓/✗ MVC structure implemented
================================
```

---

## Regras Gerais

- **Seja agnóstico de tecnologia**: as heurísticas e playbooks funcionam para Python/Flask, Node.js/Express e outras stacks
- **Nunca modifique arquivos antes da confirmação na Fase 2**
- **Preserve a funcionalidade**: os endpoints originais devem continuar respondendo após a refatoração
- **Priorize segurança**: corrija sempre os problemas CRITICAL primeiro
- **Seja específico**: sempre inclua arquivo e linha nos findings — "código ruim" não é um finding válido
- **Use os arquivos de referência**: `project-analysis.md`, `anti-patterns-catalog.md`, `report-template.md`, `architecture-guidelines.md`, `refactoring-playbook.md`
