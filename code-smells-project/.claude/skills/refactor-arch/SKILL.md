---
name: refactor-arch
description: Audita e refatora a arquitetura de um projeto backend para o padrão MVC em 3 fases (Análise, Auditoria, Refatoração), de forma agnóstica de linguagem/framework. Use SEMPRE que o usuário pedir para analisar a arquitetura, achar code smells/anti-patterns, auditar código legado, detectar APIs deprecated, reorganizar em MVC (Models, Views/Routes, Controllers), ou "refatorar" um projeto — mesmo que não cite "MVC" ou o nome da skill.
---

# refactor-arch

Skill de auditoria e refatoração arquitetural. Funciona em qualquer stack (Python, Node.js, Java, PHP, Go, Ruby, C#...) porque trabalha por **heurísticas e princípios**, não por receitas de um framework específico. O alvo é sempre o padrão MVC descrito em `references/mvc-guidelines.md`, traduzido para as convenções idiomáticas da stack detectada.

Execute as 3 fases **em ordem**. Não pule fases e não modifique nenhum arquivo antes da confirmação do usuário ao final da Fase 2 (modificar sem consentimento num código legado desconhecido é arriscado e difícil de reverter).

## Arquivos de referência (leia sob demanda)

| Arquivo | Quando ler |
|---|---|
| `references/project-analysis.md` | Fase 1 — detectar linguagem, framework, banco e mapear arquitetura |
| `references/anti-patterns-catalog.md` | Fase 2 — catálogo de anti-patterns, sinais de detecção, severidade, APIs deprecated |
| `references/report-template.md` | Fase 2 — formato exato do relatório |
| `references/mvc-guidelines.md` | Fases 2 e 3 — regras da arquitetura alvo |
| `references/refactoring-playbook.md` | Fase 3 — transformações com exemplos antes/depois |

---

## Fase 1 — Análise

Objetivo: entender o projeto antes de julgá-lo.

1. Leia `references/project-analysis.md`.
2. Detecte: **linguagem**, **framework**, **banco de dados** (e como é acessado), **ponto de entrada**, **gerenciador de dependências**, como o app é iniciado.
3. Mapeie a **arquitetura atual**: liste os arquivos-fonte, classifique cada um em camada (rota, controller, model, config, util, misto) e identifique o nível de organização (tudo num arquivo / parcialmente separado / já em camadas).
4. Liste os **endpoints/rotas** existentes e o **domínio** (entidades principais). Isso será a base para validar a Fase 3.
5. Imprima um resumo neste formato:

```
================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:      <x>
Framework:      <x> (versão)
Dependências:   <principais>
Domínio:        <entidades>
Arquitetura:    <descrição curta do estado atual>
Arquivos:       <N> arquivos analisados
Banco de dados: <x> (acesso: ORM / SQL cru / driver)
Endpoints:      <N> (lista resumida)
Como executar:  <comando>
================================
```

Prossiga automaticamente para a Fase 2.

## Fase 2 — Auditoria

Objetivo: cruzar o código contra o catálogo e produzir um relatório acionável.

1. Leia `references/anti-patterns-catalog.md` e `references/mvc-guidelines.md`.
2. Percorra **todos** os arquivos-fonte aplicando os sinais de detecção do catálogo. Inclua a checagem de **APIs deprecated** (seção própria do catálogo) comparando com a versão do framework/linguagem detectada na Fase 1; em caso de dúvida sobre depreciação, consulte a documentação oficial (ex.: Context7 MCP, se disponível).
3. Para cada achado registre: ID, nome, **severidade** (CRITICAL/HIGH/MEDIUM/LOW), **arquivo e linhas exatas**, descrição, impacto e recomendação (apontando o padrão do playbook).
4. Ordene do mais grave para o menos grave e gere o relatório conforme `references/report-template.md`. Exiba-o no chat e salve em `reports/audit-project-<nome>.md` (crie a pasta se necessário — esse é o único arquivo permitido nesta fase).
5. **PAUSE.** Termine com:

```
Fase 2 concluída. Encontrados N achados (C critical, H high, M medium, L low).
Deseja prosseguir com a refatoração (Fase 3)? [s/n]
```

Aguarde a resposta. **Não altere nenhum arquivo do projeto** sem um "sim" explícito. Se o usuário recusar ou quiser restringir o escopo, respeite isso.

## Fase 3 — Refatoração

Só execute após a confirmação.

1. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. Antes de mexer: registre o **comportamento de referência** (suba a app, chame os endpoints da Fase 1 e guarde status/formato das respostas) e, se for git, garanta que há um ponto de retorno (commit ou branch).
3. Defina a estrutura alvo de pastas adaptada à stack (ex.: `config/`, `models/`, `controllers/` ou `routes/`, `views/` ou serializers, `middlewares/`, ponto de entrada enxuto/composition root).
4. Aplique as transformações do playbook, priorizando CRITICAL → HIGH → MEDIUM → LOW, preservando contratos públicos (URLs, métodos, formato de resposta) — refatorar é mudar a estrutura, não o comportamento. Correções de segurança que alterem comportamento inseguro (ex.: parar de expor senha) devem ser listadas explicitamente no resumo.
5. Mova segredos para variáveis de ambiente/config, centralize tratamento de erros, substitua APIs deprecated.
6. **Valide**:
   - A aplicação **sobe** sem erros (instale dependências se preciso, rode o comando de execução da Fase 1).
   - Os **endpoints respondem** como antes: repita as chamadas do passo 2 e compare status e formato. Teste ao menos um caminho de sucesso e um de erro por recurso.
   - Releia o catálogo e confirme que os achados tratados não aparecem mais.
   - Se algo falhar, corrija e revalide; não declare sucesso sem evidência.
7. Imprima o resumo:

```
================================
FASE 3: REFATORAÇÃO CONCLUÍDA
================================
Nova estrutura: <árvore de pastas>
Achados tratados: <lista por ID>
Não tratados / pendentes: <lista e motivo>
Validação:
  [OK/FALHA] Aplicação inicia
  [OK/FALHA] Endpoints: <n>/<n> respondendo conforme baseline
Mudanças de comportamento intencionais: <lista ou "nenhuma">
================================
```

## Princípios

- **Agnóstico de stack**: traduza os conceitos (Model, Controller, Route, Config) para o idioma da tecnologia detectada; não force uma estrutura estrangeira ao ecossistema.
- **Evidência**: todo achado cita arquivo e linhas reais; nunca invente.
- **Mudança mínima segura**: preserve contratos e comportamento observável.
- **Projetos já organizados**: se o projeto já tem camadas, não reestruture por reestruturar — foque nos desvios reais (ex.: lógica de negócio no controller, APIs deprecated).
