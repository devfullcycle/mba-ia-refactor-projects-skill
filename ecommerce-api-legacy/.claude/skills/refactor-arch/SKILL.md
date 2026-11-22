---
name: refactor-arch
description: Audita e refatora qualquer codebase backend para o padrão MVC, independente de linguagem ou framework. Detecta a stack, pesquisa as boas práticas e APIs obsoletas dessa stack e executa 3 fases (análise, auditoria com relatório e confirmação, refatoração com validação). Use quando o usuário pedir "/refactor-arch", "refatorar para MVC", "auditar arquitetura", "achar code smells", "anti-patterns", "analisar projeto legado" ou "melhorar a arquitetura desta API". Não use para features novas, bugs pontuais ou projetos de front-end.
disable-model-invocation: true
metadata:
  version: 2.0.0
---

# refactor-arch: Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior. Executa **3 fases sequenciais** sobre o projeto no diretório atual: **Análise → Auditoria → Refatoração**.

## Princípio de agnosticismo

Esta skill **não contém conhecimento fixo de nenhuma linguagem ou framework**. As referências descrevem **princípios, sinais conceituais e padrões em pseudocódigo**. Todo conhecimento específico da stack (convenções de estrutura, APIs obsoletas, práticas de segurança, comandos de build/execução) é **descoberto e pesquisado na Fase 1** e registrado em um **Stack Profile**, que as Fases 2 e 3 usam. Nunca presuma uma tecnologia: prove-a com evidência do projeto e confirme as boas práticas em fonte confiável.

## Regras inviolantes (leia primeiro)

1. **Nenhum arquivo do projeto é criado, alterado ou movido antes da confirmação explícita do usuário ao final da Fase 2.** As Fases 1 e 2 são somente leitura (artefatos temporários vão para o diretório temporário do sistema, nunca para o projeto).
2. **Todo finding tem arquivo e linhas exatos** (`arquivo:linha` ou `arquivo:inicio-fim`), obtidos lendo o código. Nunca estime nem invente.
3. **Preserve o contrato externo**: rotas/operações, métodos, status e formato das respostas continuam iguais. Exceção: correções de segurança que exigem mudança (ex.: parar de devolver senha); registre cada uma em "Deviations".
4. **Nunca declare sucesso sem ter iniciado a aplicação e exercitado os endpoints.** Se não conseguiu validar, diga isso.
5. **Se não houver código-fonte ou ponto de entrada identificável, pare e informe o motivo.**
6. Adapte-se ao nível de organização: monolito desestruturado exige criar camadas; projeto já em camadas exige corrigir violações e lacunas, **sem reescrever o que já está adequado**.
7. **Mascare segredos** encontrados no relatório (`'minh****'`).
8. **Privacidade na pesquisa**: consultas externas contêm **apenas nome e versão da tecnologia e o tema** (ex.: "<framework> <versão> deprecated APIs"). Nunca envie nome do projeto, domínio de negócio, trechos de código, caminhos ou segredos.
9. **Saída enxuta e no formato exato**: as saídas das Fases 1 e 2 seguem **apenas** os formatos definidos aqui e no template. Todo o conhecimento intermediário (Stack Profile, baseline, fontes, plano) fica interno e só é impresso se o usuário pedir.
10. **Conhecimento não verificado é marcado como tal**: se não conseguir confirmar uma prática ou deprecation em fonte, escreva "a verificar"; não afirme.

## Referências (leia sob demanda, só quando a fase exigir)

| Arquivo | Fase | Conteúdo |
|---|---|---|
| [project-analysis.md](references/project-analysis.md) | 1 | Método de detecção de linguagem, framework, banco, domínio e arquitetura |
| [stack-research.md](references/stack-research.md) | 1 | Como pesquisar boas práticas da stack e montar o Stack Profile |
| [anti-patterns-catalog.md](references/anti-patterns-catalog.md) | 2 | Catálogo AP-01..AP-16, sinais conceituais, severidade, detecção de APIs deprecated |
| [assets/report-template.md](assets/report-template.md) | 2 | Template do relatório (asset de saída, não é conhecimento de referência) |
| [mvc-guidelines.md](references/mvc-guidelines.md) | 3 | Camadas-alvo, responsabilidades, regras de dependência, adaptação à stack |
| [refactoring-playbook.md](references/refactoring-playbook.md) | 3 | Transformações antes/depois (pseudocódigo) por anti-pattern |

Script auxiliar (heurístico, **não é gate**): `bash ${CLAUDE_SKILL_DIR}/scripts/scan.sh [diretório] [arquivo-de-padrões-extra]` lista arquivos, linhas e candidatos `AP-XX|arquivo:linha|trecho` usando padrões neutros de linguagem; o arquivo opcional de padrões extras (gerado a partir do Stack Profile, ver stack-research.md) o torna específico da stack **sem alterar a skill**. Sem `bash`, faça o equivalente com Glob/Grep.

---

## FASE 1: Análise do projeto (somente leitura)

Leia [project-analysis.md](references/project-analysis.md) e execute:

1. Rode `scan.sh` para o inventário inicial.
2. **Detecte** linguagem, framework + versão, dependências relevantes, banco/ORM, tabelas/entidades e domínio, **por evidência** (manifestos, imports, extensões, configuração).
3. **Pesquise o conhecimento da stack** (obrigatório): leia [stack-research.md](references/stack-research.md), consulte fontes confiáveis e monte o **Stack Profile** (estrutura idiomática, APIs obsoletas da versão detectada, práticas de segurança, comandos de build/execução/teste, convenções de DI, erro, validação e logging). Time-box: no máximo ~8 consultas.
4. Leia o ponto de entrada e **todos os arquivos-fonte** (projetos grandes: priorize entrada, rotas, acesso a dados e config; declare o que não leu).
5. Mapeie a **arquitetura atual** e onde cada responsabilidade vive.
6. **Levante o baseline de endpoints**: método + caminho + resposta esperada de cada rota (do código, de documentação ou coleções de requisições). Será a régua da Fase 3. **Guarde internamente; não imprima.**
7. Imprima **somente** o bloco abaixo (nada antes, nada depois):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se conhecida>
Framework:     <framework + versão>
Dependencies:  <principais>
Domain:        <domínio em uma linha>
Architecture:  <descrição objetiva da arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <tabelas/entidades>
Entry point:   <arquivo>
Run command:   <comando de execução>
Endpoints:     <N> mapped
Stack profile: <N> sources consulted (<verified | partially verified | unverified>)
================================
```

**Não imprima** o Stack Profile, a tabela de endpoints, fontes consultadas, tabelas de APIs obsoletas nem comentários adicionais: eles ficam **internos** e alimentam as Fases 2 e 3. A linha `Stack profile` do bloco já resume a pesquisa. Cada campo ocupa **uma linha**, exceto quando o valor for naturalmente uma lista curta na mesma linha.

Se a stack for desconhecida ou rara: diga o que detectou, pesquise a documentação oficial dela e siga com os princípios gerais; não trave.

## FASE 2: Auditoria (somente leitura)

Leia [anti-patterns-catalog.md](references/anti-patterns-catalog.md) e [report-template.md](assets/report-template.md).

1. Cruze **cada arquivo-fonte** contra o catálogo. Use os sinais conceituais, os candidatos do `scan.sh` (com padrões extras do Stack Profile, se gerou) e a leitura direta; **confirme cada achado lendo o trecho** e descarte falsos positivos.
2. Inclua **APIs deprecated/obsoletas** (base: Stack Profile + versão usada) **como findings AP-13 dentro de "Findings"**, citando na Description o obsoleto, o substituto e a fonte (ou "a verificar"). Sem seção separada; se não houver, simplesmente não há finding AP-13.
3. Classifique: CRITICAL, HIGH, MEDIUM, LOW (definições no catálogo). Agrupe ocorrências repetidas do mesmo problema em um finding.
4. Ordene **CRITICAL → LOW**. Para cada finding: título com ID, arquivo:linhas, descrição, impacto, recomendação (apontando o padrão do playbook).
5. Imprima o relatório **exatamente** no formato do template: cabeçalho, Summary, Findings, Total e a pergunta de confirmação. **Nada além disso**: sem seções extras (APIs deprecated separadas, fontes, observações positivas, plano de refatoração), sem tabelas, sem perguntas ou comentários antes da confirmação.
6. **PARE e peça confirmação**, com esta linha exata ao final:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Decisões pendentes (ex.: desvios de segurança, migração de senhas) **não são perguntadas aqui**: aplique o padrão do playbook na Fase 3 e registre em "Deviations" / "Needs Human". O plano da estrutura-alvo aparece só na Fase 3.

Aguarde a resposta. Em `n`, encerre sem tocar em nada. Em outra resposta (ex.: "só os CRITICAL"), ajuste o escopo e confirme o entendimento antes de seguir.

## FASE 3: Refatoração e validação

Execute **somente após confirmação**. Leia [mvc-guidelines.md](references/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md). **Traduza os padrões em pseudocódigo para a forma idiomática da stack**, conforme o Stack Profile.

### 3.1 Preparação
- Salve o relatório da Fase 2 em `reports/audit-<nome-do-projeto>.md` (crie `reports/`).
- Se for repositório git, verifique a árvore de trabalho e sugira commit/branch de checkpoint. Não faça commit sem o usuário pedir.
- Defina a estrutura-alvo usando as convenções do Stack Profile e liste o que será criado/movido.

### 3.2 Transformação (incremental, nesta ordem)
1. **Config**: segredos e constantes fora do código (ambiente/arquivo de configuração externo); documente com um arquivo de exemplo sem valores reais.
2. **Models/acesso a dados**: isolar queries; parametrizar; resolver N+1.
3. **Controllers**: regra de negócio e orquestração; validação de entrada.
4. **Views/Routes**: só mapeamento de entrada → controller e serialização.
5. **Error handling** centralizado; sem vazar detalhes internos.
6. **Entry point / composition root**: monta dependências, registra rotas e middlewares.
7. Substitua APIs deprecated e trate LOW por último.
- Aplique o padrão do playbook de cada finding e rastreie finding → arquivo novo.
- Mantenha o app executável a cada etapa significativa; use a verificação de compilação/sintaxe do Stack Profile.
- Atualize manifestos/scripts se o ponto de entrada mudar e **preserve o comando de execução original** sempre que possível.

### 3.3 Validação (obrigatória)
1. **Build/boot**: execute os comandos de build e execução do Stack Profile (ou do README/manifesto), em background com timeout; capture os logs. Falha → diagnostique e corrija; no máximo **3 tentativas** por problema, depois reporte como falha.
2. **Endpoints**: exercite cada rota do baseline e compare status e formato. Use dados de seed; em rotas mutáveis use dados de teste sem destruir dados reais.
3. **Testes existentes**: se o projeto tiver suíte, rode-a e compare com o estado anterior (falhas já existentes são "pre-existing").
4. **Re-scan**: rode `scan.sh` e releia os trechos para confirmar que os anti-patterns tratados sumiram. Não afirme "zero anti-patterns" sem isso.
5. Encerre os processos que você iniciou.
6. Divergências: corrija ou liste em "Deviations" com justificativa.

### 3.4 Saída final

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Findings Resolved
<ID do finding → como foi resolvido → arquivo(s)>

## Validation
  ✓/✗ Application builds/boots without errors
  ✓/✗ All endpoints respond correctly (<ok>/<total>)
  ✓/✗ Existing tests: <resultado ou "none">
  ✓/✗ Anti-patterns re-scanned: <N remaining, quais>

## Deviations
<mudanças de comportamento deliberadas ou "none">

## Not Done / Needs Human
<itens pulados, não validados ou que exigem decisão>
================================
```

Use ✓ só para o que foi **de fato verificado**.

## Casos de borda

- **Sem acesso à internet/ferramentas de pesquisa**: use o conhecimento próprio, rotule o Stack Profile como `unverified` e marque deprecations como "a verificar".
- **Sem testes e sem README**: derive build/execução do manifesto e do Stack Profile; se não achar, pergunte.
- **Banco inexistente ou externo**: valide o que for possível e registre o limite.
- **Dependência externa/credencial ausente**: continue, registre como limitação da validação, não como sucesso.
- **Projeto já em camadas**: foque em violações reais e lacunas.
- **Stack em que "MVC" não é idiomático**: preserve as **responsabilidades** do MVC com o vocabulário idiomático da stack (ver mvc-guidelines.md) e declare o mapeamento.
- **Monorepo**: pergunte qual pacote auditar se não for óbvio.
- **Falha pré-existente**: registre como pré-existente, não como regressão.

## Recap

- Nenhuma tecnologia é presumida: detectar → pesquisar → registrar o Stack Profile → só então auditar.
- Fases 1 e 2 não modificam o projeto; Fase 3 só após `y`.
- Finding sem arquivo:linha exato não entra no relatório; conhecimento não verificado vira "a verificar".
- Contrato externo preservado; desvios declarados.
- Sem build/boot e sem exercitar endpoints, não há "sucesso".
