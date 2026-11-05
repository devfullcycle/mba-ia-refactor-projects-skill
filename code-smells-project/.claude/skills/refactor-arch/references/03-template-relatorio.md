# 03 — Template de relatório e mensagens de saída

Use este arquivo na **Fase 2** (montar o relatório) e na **Fase 3** (anexar resultados). Os textos entre `<...>` são valores a preencher; todo o resto é literal. Cabeçalhos de seção e mensagens-chave ficam exatamente como aqui, para que as execuções sejam comparáveis.

## 1. Convenções

- Idioma do conteúdo: PT-BR. Cabeçalhos de bloco (`PHASE 1: PROJECT ANALYSIS`, `ARCHITECTURE AUDIT REPORT`, `PHASE 3: REFACTORING COMPLETE`) e a linha de confirmação ficam em inglês, como no enunciado do desafio.
- **Segredos nunca por completo**: mascare para os 4 primeiros caracteres + `***` (`pk_live_1234***`, `minha-chav***`). Vale para relatório, evidências e mensagens ao usuário.
- **Arquivo e linhas exatos**: `arquivo.ext:12` ou `arquivo.ext:12-30`; várias ocorrências do mesmo achado: `arquivo.ext:12, 40-44; outro.ext:7`. Releia o trecho antes de escrever o número (ver `02-catalogo-antipatterns.md`, seção 2).
- **Ordenação**: severidade (CRITICAL → HIGH → MEDIUM → LOW); dentro da severidade, categoria (Segurança, Arquitetura, Deprecated, Testes, Qualidade, Outro); depois arquivo (ordem alfabética) e linha. Os IDs `F-001…` são atribuídos **depois** de ordenar.
- **Contagem**: `Summary` conta *findings* (um por anti-pattern com todas as suas ocorrências). O total de ocorrências aparece à parte.
- **Run / Run id**: obtenha a data/hora do relógio do sistema (comando de leitura, classe A). Nunca invente. `Run` = ISO 8601 com offset (`2026-11-04T14:32:10-03:00`); `Run id` = `AAAAMMDD-HHMMSS` (`20261104-143210`).

## 2. Mensagem da Fase 1 (impressa no terminal; não vira arquivo)

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão do runtime, se detectável>
Framework:     <framework + versão> (confiança: alta|média|baixa)
Dependencies:  <principais dependências declaradas>
Domain:        <domínio da aplicação em uma frase>
Architecture:  <rótulo> — <descrição curta>
Source files:  <n> files analyzed (~<loc> lines)
DB tables:     <tabelas/coleções ou "n/a">
Entry point:   <arquivo e comando de execução>
Routes found:  <n> (<k> administrativas/destrutivas)
Validation:    tests: unit=<sim|não|?> integration=<sim|não|?> e2e=<sim|não|?> | run-docs=<sim|não> | scripts=<sim|não> | api-collection=<sim|não>
================================
```

`Source files` conta apenas código-fonte do projeto (exclua dependências, build, caches, bancos, lockfiles, binários). Se um campo não puder ser determinado, escreva `não determinado` e diga o motivo na linha seguinte.

## 3. Relatório da Fase 2 (impresso **e** salvo)

Salve em `reports/audit-project-{N}.md` (regras de local, `{N}` e histórico no `SKILL.md`, Fase 2, passo 9). Estrutura completa, nesta ordem:

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Path:    <caminho relativo à raiz do repositório, ou "." >
Run:     <ISO 8601>          Run id: <AAAAMMDD-HHMMSS>
Stack:   <linguagem> + <framework> <versão> (confiança: <alta|média|baixa>)
Files:   <n> analyzed | ~<loc> lines of code
Architecture: <rótulo>
Skill:   refactor-arch 1.0 | Catalog 1.0

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>
Total: <n> findings (<m> ocorrências) 
Por categoria: Segurança <n> | Arquitetura <n> | Deprecated <n> | Testes <n> | Qualidade <n> | Outro <n>
Cobertura: <arquivos lidos integralmente>/<arquivos-fonte> lidos; <demais> inspecionados por busca

## Estrutura ANTES
<árvore de diretórios do código-fonte (sem dependências/caches), até 3 níveis>

| Métrica | Valor |
|---|---|
| Arquivos-fonte | <n> |
| Linhas de código (aprox.) | <loc> |
| Camadas presentes (papéis) | <config, rotas, controllers, models, services, middleware...> |
| Maior arquivo | <arquivo> (<linhas>) |
| Arquivos com 3+ papéis | <n> (<lista>) |

## Superfície de ataque
| Método | Rota | Handler (arquivo:linha) | Autenticação | Administrativa/destrutiva |
|---|---|---|---|---|
| <GET> | </x> | <arq:12> | <sim|não> | <sim|não> |

## Findings

### [CRITICAL] F-001 · <ID do catálogo> <Nome>
File: <arquivo:linhas>
Ocorrências: <n> · Confiança: <CONFIRMED|LIKELY|SUSPECTED> · Categoria: <categoria>
CWE/OWASP: <CWE-xx / Axx:2021 | n/a>
Evidência: `<trecho curto e literal, segredos mascarados>`
Description: <o que é, em termos do código real>
Impact: <consequência concreta>
Recommendation: <o que fazer> (Playbook <P-xx>)

### [HIGH] F-00x · ...
(repita até LOW)

## Descartados / falsos positivos
- <ID> em <arquivo:linha> — descartado porque <motivo>
(ou "Nenhum")

## Mudanças de contrato propostas
| ID | Rota/campo | Mudança | Motivo (Finding) | Alternativa compatível |
|---|---|---|---|---|
| CT-01 | <POST /admin/x> | <remover|proteger|omitir campo> | <F-001> | <proteger por flag/autenticação> |
(ou "Nenhuma")

## Plano de mudanças
| ID | Mudança | Sev. | Resolve | Arquivos | Padrão | Afeta contrato | Depende de |
|---|---|---|---|---|---|---|---|
| C-01 | <descrição> | <maior severidade entre os findings resolvidos> | <F-001, F-004> | <arquivos> | <P-01> | <não|CT-01> | <—|C-xx> |

Agrupe as mudanças pelo **padrão do playbook** (uma `C-xx` por padrão e escopo coerente) e ordene pela ordem canônica de aplicação (`05-playbook-refatoracao.md`, seção 0). Findings sem transformação automática (TST-xx, recomendações) não geram `C-xx`: listam-se em "Recomendações manuais" logo abaixo da tabela.

## Plano de comandos
| ID | Comando | Finalidade | Origem | Classe | Efeitos colaterais |
|---|---|---|---|---|---|
| K-01 | `<comando>` | <para quê> | <arquivo:linha onde foi descoberto> | <A|B|C|D> | <nenhum|escreve .venv|...> |

## Plano de validação
<tabela de capacidades do projeto (testes, scripts, CI, coleções) + degrau da escada que será tentado + o que não poderá ser exercitado e por quê. Formato em 06-protocolo-validacao.md, seção 2>

## Decisões do usuário
(preenchido após a pausa; até lá: "Aguardando confirmação")

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

Regras:
- Cada finding tem **todos** os campos. Sem `File:` verificado, o achado vira `SUSPECTED` e é marcado como tal, ou é descartado.
- Findings de ausência (ex.: TST-01, SEC-09) usam `File:` do ponto de referência (ex.: o arquivo de entrada ou o diretório) e dizem isso na `Description`.
- Se o total de findings for menor que 5, repita a varredura pelas categorias menos cobertas antes de fechar; se continuar menor, diga o motivo na `Description` do rodapé (projeto pequeno, bem protegido).
- A linha final `Phase 2 complete...` é literal e vem **depois** da gravação do arquivo.

## 4. Anexo da Fase 3 (adicionado ao mesmo arquivo, após um separador)

Nunca reescreva a parte da Fase 2; só acrescente abaixo de:

```
---
# ANEXO — FASE 3 (Run id: <AAAAMMDD-HHMMSS>)
```

Seções, nesta ordem:

````markdown
## Decisões do usuário (registro)
- Escopo: <todas | rejeitadas: C-xx, C-yy>
- Modo de comandos: <Equilibrado|Completo|Passo a passo|Sem alterar ambiente>
- Contrato: <aprovadas: CT-xx | nenhuma | revisão individual: CT-01 sim, CT-02 não>
- Sondagem ad hoc: <somente leitura|incluindo escrita|não|não aplicável>

## Estrutura DEPOIS
<árvore>

| Métrica | ANTES | DEPOIS |
|---|---|---|
| Arquivos-fonte | | |
| Linhas de código (aprox.) | | |
| Camadas presentes | | |
| Maior arquivo | | |
| Arquivos com 3+ papéis | | |

### Mapa antigo → novo
| Arquivo original | Destino(s) |
|---|---|
| <models.py> | <models/produto_model.py, models/usuario_model.py> |

## Mudanças aplicadas
| ID | Status | Observação |
|---|---|---|
| C-01 | aplicada / rejeitada pelo usuário / revertida / não aplicável | <detalhe> |

## Evidências de execução
<um bloco E-nn por execução; formato em 06-protocolo-validacao.md, seção 7>

### Comparação antes/depois (rotas)
| Método | Rota | ANTES | DEPOIS | Resultado |
|---|---|---|---|---|
| GET | /x | 200 {chaves} | 200 {chaves} | igual |
| POST | /admin/x | 200 | removida (CT-01 aprovada) | ALTERADO (aprovado) |
(status possíveis: igual, ALTERADO (aprovado), DIVERGENTE, NÃO EXERCITADA (motivo))

### Resumo da validação
| Degrau | Comando | Resultado | Evidência |
|---|---|---|---|
| V1 | `<comando>` | passed 41 / failed 0 / skipped 0 | E-02 |
Veredito: <VALIDADO (V1) | VALIDADO PARCIALMENTE (...) | NÃO VALIDADO (motivo)>

## Checklist de Validação
(Cada item recebe [x] ou [ ] e uma referência. [x] exige evidência real E-nn ou arquivo:linha; sem evidência fica [ ] com o motivo.)

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente — <evidência>
- [ ] Framework detectado corretamente — <evidência>
- [ ] Domínio da aplicação descrito corretamente — <evidência>
- [ ] Número de arquivos analisados condiz com a realidade — <evidência: contagem independente>

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência — <evidência>
- [ ] Cada finding tem arquivo e linhas exatos — <evidência: verificação por releitura>
- [ ] Findings ordenados por severidade (CRITICAL → LOW) — <evidência>
- [ ] Mínimo de 5 findings identificados — <n>
- [ ] Detecção de APIs deprecated incluída (se aplicável) — <findings DEP-xx ou "não aplicável: motivo">
- [ ] Skill pausa e pede confirmação antes da Fase 3 — <evidência: pergunta e resposta registradas>

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC — <evidência>
- [ ] Configuração extraída para módulo de config (sem hardcoded) — <evidência>
- [ ] Models criados para abstrair dados — <evidência>
- [ ] Views/Routes separadas para visualização ou roteamento — <evidência>
- [ ] Controllers concentram o fluxo da aplicação — <evidência>
- [ ] Error handling centralizado — <evidência>
- [ ] Entry point claro — <evidência>
- [ ] Aplicação inicia sem erros — <E-nn>
- [ ] Endpoints originais respondem corretamente — <E-nn; exceções aprovadas listadas>

## Itens residuais (reauditoria)
<findings que continuam presentes, com o motivo (rejeitado pelo usuário, risco de contrato, fora de escopo) ou "Nenhum">

## Observações da execução
- Stack detectada e confiança: <...>
- Dicas específicas usadas × derivadas do sinal abstrato: <lista; "derivado" = não havia dica para a stack>
- Nível de organização encontrado e como a Fase 3 se adaptou: <...>
- Falsos positivos descartados: <n e exemplos>
- Limitações da validação (degrau alcançado, o que ficou não exercitado e por quê): <...>
- Tentativas/iterações na Fase 3 e reversões: <...>
- Arquivos criados pela execução fora do código-fonte (ex.: venv, caches): <...>
````

## 5. Mensagem final da Fase 3 (impressa no terminal)

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore resumida>

## Validation
  <✓|✗|~> Application boots without errors            [E-nn]
  <✓|✗|~> Original endpoints respond correctly        [E-nn]   (exceções aprovadas: <lista>)
  <✓|✗|~> Existing tests pass (<passed>/<total>)      [E-nn]
  <✓|✗|~> No anti-patterns remaining                  [reauditoria: <n> residuais]

Veredito: <VALIDADO (V1) | VALIDADO PARCIALMENTE | NÃO VALIDADO>
Relatório: <caminho> | Evidências: <pasta>
================================
```

Símbolos: `✓` somente com evidência `E-nn` real; `✗` falhou; `~` parcial/não exercitado (explique abaixo). **Nunca** marque `✓` em "No anti-patterns remaining" sem ter reexecutado a varredura do catálogo.

## 6. Exemplo mínimo (stack fictícia) — só como molde de formato

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: demo-api
Path:    .
Run:     2026-11-04T14:32:10-03:00          Run id: 20261104-143210
Stack:   Ruby + Sinatra 4.0 (confiança: média)
Files:   3 analyzed | ~210 lines of code
Architecture: monolito-sem-camadas
Skill:   refactor-arch 1.0 | Catalog 1.0

## Summary
CRITICAL: 1 | HIGH: 1 | MEDIUM: 1 | LOW: 1
Total: 4 findings (7 ocorrências)
...

### [CRITICAL] F-001 · SEC-01 SQL Injection
File: app.rb:22, 41
Ocorrências: 2 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-89 / A03:2021
Evidência: `DB.execute("SELECT * FROM users WHERE id = #{params[:id]}")`
Description: parâmetro de rota interpolado diretamente na consulta.
Impact: leitura e alteração arbitrária de dados por qualquer cliente.
Recommendation: usar placeholders na consulta (Playbook P-02).
````
