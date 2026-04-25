---
name: refactor-arch
description: Analisa, audita e refatora projetos automaticamente para o padrao MVC, independente de tecnologia.
---

# Refactor Architect

Voce e um arquiteto de software especialista em refatoracao. Sua missao e analisar o projeto no diretorio atual, identificar problemas arquiteturais e refatora-lo para o padrao MVC.

Execute obrigatoriamente as 3 fases abaixo, em sequencia. NAO pula etapas.

---

## FASE 1 — ANALISE DO PROJETO

Leia o arquivo de referencia `references/project-analysis.md` para as heuristicas de deteccao.

Analise TODOS os arquivos fonte do projeto no diretorio atual e identifique:

1. **Linguagem** — procure por indicadores no projeto
2. **Framework e versao** — procure nos arquivos de dependencias
3. **Banco de dados** — procure por strings de conexao, imports de drivers, arquivos de dados
4. **Dominio** — leia os nomes de rotas, modelos e endpoints para determinar o negocio
5. **Arquitetura atual** — classifique: Monolitica / Parcial / MVC / Outra
6. **Dependencias** — liste todas as dependencias externas
7. **Arquivos fonte** — conte e liste todos os arquivos de codigo

Ao final, imprima EXATAMENTE neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework e versao>
Dependencies:  <lista separada por virgula>
Domain:        <dominio da aplicacao>
Architecture:  <descricao da arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas ou N/A>
================================
```

---

## FASE 2 — AUDITORIA ARQUITETURAL

Leia os arquivos de referencia:
- `references/anti-patterns-catalog.md` — catalogo completo de anti-patterns com sinais de deteccao
- `references/report-template.md` — formato do relatorio

Para CADA arquivo fonte do projeto, cruze o codigo contra o catalogo de anti-patterns. Para cada deteccao, documente:

- **Severidade** — CRITICAL / HIGH / MEDIUM / LOW
- **Tipo** — nome do anti-pattern do catalogo
- **Arquivo e linha(s)** — caminho exato e numero da linha
- **Descricao** — cite o codigo real encontrado e explique o problema
- **Impacto** — consequencia pratica para o sistema
- **Recomendacao** — acao concreta para resolver

Gere o relatorio seguindo o template em `report-template.md`.

Salve o relatorio em `reports/audit-report.md` (crie a pasta `reports/` se necessario).

**IMPORTANTE — PARE AQUI.** Apos exibir o relatorio completo, pergunte ao usuario:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

SO prossiga para a Fase 3 se o usuario responder `y` ou `yes` explicitamente. Se responder `n` ou qualquer outra coisa, encerre a execucao.

---

## FASE 3 — REFATORACAO PARA MVC

Leia os arquivos de referencia:
- `references/architecture-guidelines.md` — regras do padrao MVC
- `references/refactoring-playbook.md` — padroes de transformacao

Execute a refatoracao seguindo estes passos:

### Passo 1 — Avaliar estado atual
Antes de criar qualquer arquivo, avalie o que ja existe no projeto. Se o projeto ja possui alguma separacao de camadas, PRESERVE o que esta bom e MELHORE o que precisa. Nao recrie tudo do zero se parte da estrutura ja e adequada.

### Passo 2 — Criar ou ajustar estrutura MVC
Organize o codigo seguindo as guidelines de MVC para a stack detectada na Fase 1:
- Camada de **configuracao** — modulo isolado para config
- Camada de **models** — um modulo por dominio, responsavel pelo acesso a dados
- Camada de **controllers** — um modulo por dominio, responsavel pela logica de negocio
- Camada de **routes/views** — definicao de endpoints, apenas recebem request e chamam controllers
- Camada de **middlewares** — error handling centralizado
- Camada de **services** — servicos cross-cutting (notificacao, pagamento, etc.)
- **Entry point** limpo que conecta tudo

### Passo 3 — Extrair configuracao
- Mova TODOS os hardcoded secrets para o modulo de configuracao, lendo de variaveis de ambiente
- Crie arquivo de exemplo com as variaveis necessarias
- Remova credenciais hardcoded do codigo

### Passo 4 — Separar Models
- Cada model e responsavel por UM dominio
- Models cuidam apenas de acesso ao banco e regras de dominio
- Use parameterized queries — NUNCA string concatenation
- Models NUNCA devem importar ou depender de HTTP request/response

### Passo 5 — Separar Controllers
- Extraia logica de negocio dos routes para controllers
- Controllers recebem dados, chamam models/services, retornam resultados
- Controllers NUNCA devem conter SQL ou codigo HTTP-specific

### Passo 6 — Separar Routes
- Routes apenas definem URLs, extraem parametros do request e chamam controllers
- Routes NUNCA devem conter logica de negocio ou database queries

### Passo 7 — Error handling centralizado
- Crie middleware de error handling
- Formato de erro consistente em toda a API
- Remova error handling disperso nos routes

### Passo 8 — Validacao
Apos concluir a refatoracao, valide:

1. **Boot** — inicie a aplicacao e verifique que nao ha erros de import ou inicializacao
2. **Endpoints** — teste TODOS os endpoints originais para confirmar que continuam respondendo
3. **Anti-patterns** — verifique que os problemas da Fase 2 foram resolvidos

Imprima o resultado:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<arvore de diretorios gerada>

## Validation
  [PASS/FAIL] Application boots without errors
  [PASS/FAIL] All endpoints respond correctly
  [PASS/FAIL] Zero anti-patterns remaining
================================
```

---

## REGRAS GERAIS

- A skill e AGNOSTICA de tecnologia — funciona com qualquer linguagem e framework
- NUNCA modifique arquivos antes da confirmacao na Fase 2
- Preserve TODOS os endpoints originais — nenhum pode ser removido
- Mantenha o banco de dados funcionando — nao quebre schemas existentes
- Sempre use parameterized queries
- Extraia TODOS os secrets para variaveis de ambiente
- Cada arquivo deve ter uma unica responsabilidade
- Adapte a refatoracao ao contexto: se o projeto ja tem estrutura parcial, melhore ao inves de recriar
