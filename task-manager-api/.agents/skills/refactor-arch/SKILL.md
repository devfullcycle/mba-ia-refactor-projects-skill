---
name: refactor-arch
description: Skill de refatoração arquitetural automatizada para migração de código legado para o padrão MVC. Detecta stacks tecnológicas (Python, Node.js, etc.), audita anti-patterns e vulnerabilidades (SQL Injection, secrets expostas, God classes, queries em controllers, N+1 queries, complexidade ciclomática, APIs deprecated), gera relatórios estruturados e refatora a codebase em 3 fases sequenciais com validação de boot e integridade de endpoints. Use sempre que o usuário solicitar refatoração arquitetural, auditoria de código legado, migração para MVC ou ao executar /refactor-arch.
---

# Refactor Architecture Skill (`refactor-arch`)

Esta skill automatiza a análise, auditoria de qualidade/segurança e refatoração arquitetural de projetos de software legados para o padrão **MVC (Model-View-Controller)** de forma agnóstica de linguagem ou framework (Python/Flask, Node.js/Express, etc.).

A execução é estritamente dividida em **3 Fases Sequenciais**:
1. **Fase 1 — Análise de Projeto (Project Analysis)**
2. **Fase 2 — Auditoria Arquitetural (Architecture Audit)** *(com pausa obrigatória para aprovação humana)*
3. **Fase 3 — Refatoração e Validação (Refactoring & Validation)**

---

## Recursos de Referência

Ao executar qualquer fase, consulte os arquivos de conhecimento correspondentes localizados na subpasta `references/`:
- `references/project_analysis.md`: Heurísticas de detecção de linguagem, framework, banco de dados e arquitetura.
- `references/antipatterns_catalog.md`: Catálogo completo de anti-patterns, sinais de detecção e severidades (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, APIs deprecated).
- `references/report_template.md`: Template padronizado do relatório de auditoria da Fase 2.
- `references/mvc_guidelines.md`: Princípios arquiteturais do padrão MVC, responsabilidades de camadas e estrutura de pastas.
- `references/refactoring_playbook.md`: Padrões concretos de transformação com exemplos de código antes e depois.

---

## Fluxo de Execução

```
[Início]
   │
   ▼
┌───────────────────────────────────────────────┐
│ FASE 1: Project Analysis                      │
│ - Inspecionar arquivos e manifestos           │
│ - Detectar Linguagem, Framework e DB          │
│ - Imprimir resumo formatado                   │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│ FASE 2: Architecture Audit                    │
│ - Cruzar código com catálogo de anti-patterns │
│ - Classificar achados por severidade          │
│ - Imprimir relatório seguindo o template      │
│ - Salvar em reports/audit-project-<ID>.md     │
│ - PAUSAR e solicitar confirmação do usuário   │
└──────────────────────┬────────────────────────┘
                       │ Resposta do usuário: "y"
                       ▼
┌───────────────────────────────────────────────┐
│ FASE 3: Refactoring & Validation              │
│ - Aplicar padrões do Playbook de Refatoração  │
│ - Reestruturar diretórios em MVC limpo        │
│ - Extrair config e centralizar error handling │
│ - Validar boot e execução de endpoints        │
│ - Exibir resumo da refatoração e checklist    │
└───────────────────────────────────────────────┘
```

---

### Fase 1 — Análise do Projeto

1. Inspecione o diretório do projeto e seus arquivos de configuração (`requirements.txt`, `package.json`, etc.) de acordo com as heurísticas de `references/project_analysis.md`.
2. Identifique:
   - Linguagem de programação e gerenciador de dependências.
   - Framework web utilizado e bibliotecas de persistência/banco de dados.
   - Domínio da aplicação e principais entidades/recursos.
   - Classificação arquitetural atual (ex: monolito não-estruturado, camadas parciais, etc.).
   - Contagem exata de arquivos de código-fonte analisados.
3. Imprima no terminal o resumo padronizado:
   ```
   ================================
   PHASE 1: PROJECT ANALYSIS
   ================================
   Language:      <Linguagem detectada>
   Framework:     <Framework detectado>
   Dependencies:  <Principais dependências>
   Domain:        <Domínio da aplicação>
   Architecture:  <Diagnóstico arquitetural>
   Source files:  <Quantidade de arquivos analisados>
   DB tables:     <Tabelas encontradas>
   ================================
   ```

---

### Fase 2 — Auditoria Arquitetural

1. Realize uma varredura minuciosa em todos os arquivos de código-fonte, confrontando cada trecho contra o catálogo em `references/antipatterns_catalog.md`.
2. Para cada problema detectado, registre:
   - **Severidade**: `CRITICAL`, `HIGH`, `MEDIUM` ou `LOW`.
   - **Anti-Pattern**: Nome e identificador.
   - **File**: Caminho do arquivo e intervalo exato de linhas.
   - **Description**: Explicação clara do problema.
   - **Impact**: Consequência para segurança, manutenibilidade ou desempenho.
   - **Recommendation**: Ação recomendada para correção.
3. Ordene **obrigatoriamente** todos os achados em ordem decrescente de severidade (`CRITICAL` → `HIGH` → `MEDIUM` → `LOW`).
4. Garanta a identificação de **no mínimo 5 findings**, com pelo menos 1 de severidade `CRITICAL` ou `HIGH`.
5. Apresente o relatório estruturado na tela conforme `references/report_template.md`.
6. Salve o relatório no diretório `reports/` correspondente (`audit-project-1.md`, `audit-project-2.md`, ou `audit-project-3.md`).
7. **PAUSA OBRIGATÓRIA**:
   - Finalize a Fase 2 emitindo estritamente a pergunta de confirmação:
     `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`
   - **NÃO** modifique nenhum arquivo do projeto antes de receber a confirmação explícita do usuário.

---

### Fase 3 — Refatoração e Validação

Após a confirmação positiva do usuário (`y` ou `sim`):
1. Crie a estrutura de diretórios do padrão MVC conforme as diretrizes de `references/mvc_guidelines.md`:
   - `config/`: Extração de parâmetros de ambiente e segredos hardcoded.
   - `models/`: Entidades e persistência encapsulada com queries parametrizadas (eliminando SQL Injection e N+1).
   - `controllers/`: Orquestração de regras e fluxo de negócio (sem código SQL direto).
   - `views/` ou `routes/`: Roteamento explícito com métodos HTTP declarados.
   - `middlewares/`: Tratamento centralizado de erros e exceções não tratadas.
   - Entry point limpo (`app.py` ou `src/app.js`).
2. Aplique as transformações recomendadas em `references/refactoring_playbook.md`:
   - Corrigir todas as vulnerabilidades `CRITICAL` (SQL Injection, chaves hardcoded, endpoints arbitrários).
   - Corrigir todas as violações `HIGH` (remoção de queries de controllers, hashing seguro de senhas, remoção de senhas de DTOs, eliminação de estado global mutável, integridade referencial).
   - Corrigir violações `MEDIUM` (eliminar N+1 via JOINs, simplificar condicionais aninhadas, remover falhas silenciosas, otimizar health checks pesados para validação atômica de conectividade, validar e desvincular registros dependentes antes de excluir entidades com relacionamentos opcionais).
   - Corrigir violações `LOW` (atualizar APIs deprecated como `datetime.utcnow()`, declarar verbos HTTP explícitos, limpar dead code e imports não utilizados).
3. **Validação da Aplicação**:
   - Execute o boot da aplicação refatorada em ambiente local para garantir que inicializa sem erros de sintaxe ou dependência.
   - Execute chamadas de teste aos endpoints principais para certificar que os contratos de API e retornos continuam respondendo corretamente.
4. Imprima o resumo final de conclusão da Fase 3 com a nova estrutura de pastas e o checklist de validação.
