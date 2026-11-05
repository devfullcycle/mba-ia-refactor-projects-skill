# 06 — Protocolo de validação e evidências (Fase 3)

Define **como provar** que a aplicação continua funcionando e **como mostrar ao usuário** que a prova é real. Complementa `07-politica-comandos-aprovacoes.md` (quem pode rodar o quê).

## 1. Princípios

1. **Só recursos do projeto** (decisão D5): testes, scripts, targets, configs, CI e coleções/exemplos de requisição que **já existem**. Não crie scripts, coleções ou helpers no projeto. Não adicione ferramenta de teste que o projeto não declare. **Única exceção:** na **Opção 2** de contrato (`07`, seção 4.1, P3) a skill adiciona/atualiza testes, no framework e no diretório de testes que o projeto já usa, **apenas para comprovar** as mudanças de contrato aprovadas (seção 8.9).
2. **Comparar com o baseline**: tudo que for medido depois é comparado ao que foi medido **antes** de editar, com o mesmo comando.
3. **Evidência real ou nada**: cada ✓ aponta um `E-nn` produzido por chamada de ferramenta desta sessão. Execução pulada = `NÃO EXECUTADO`. Nunca preencha resultado por inferência.
4. **Compilar, subir, testar rodam sempre**, sem confirmação (classe B), em qualquer modo. Só instalação/ambiente (C) e destrutivos (D) dependem de aprovação.
5. **Testes podem ser adaptados, nunca "para passar"**: a refatoração e os contratos aprovados exigem atualizar testes; o que é proibido é editar, remover, enfraquecer ou pular um teste só para ele passar. O teste alterado deve manter a intenção e continuar validando de forma equivalente ou mais forte. Política completa na seção 8.
6. **Segredos mascarados** em toda evidência.

## 2. Plano de validação (montado na Fase 2, executado na Fase 3)

Tabela do relatório (seção "Plano de validação"), a partir do inventário da Fase 1:

| Degrau | Disponível? | Comando (origem, classe) | Observação |
|---|---|---|---|
| V1 Testes do projeto | sim/não | `<cmd>` (arquivo:linha, B) | tipo(s), nº aproximado |
| V2 Script de verificação do projeto | sim/não | `<cmd>` | lint/check/CI |
| V3 Boot + requisições existentes | sim/não | boot `<cmd>` + coleção/curl `<arquivo>` | rotas cobertas |
| V4 Sondagem ad hoc | depende de P4 | — | só se a rodada 1 permitir |
| V5 Estático | sempre | compilar/importar (B) | — |
| Pré-requisitos | | `<cmd instalação>` (C) | se ausentes |
| Testes afetados previstos | | testes que dependem de módulos movidos, autenticação, seed ou campos alterados | classe T1/T2/T4 (seção 8) |
| Prova prevista por `CT-xx` (Opção 2) | | teste novo / sondagem ad hoc / não comprovável | seção 8.9 |
| Não exercitável | | rotas/fluxos e motivo | admin/destrutivas, banco externo, etc. |

## 3. Escada de validação

Tente **sempre o degrau mais alto disponível** e, quando útil, vários (V1 e V3 juntos dão mais confiança). Declare o degrau alcançado e por que não foi mais alto.

| Degrau | O que é | Fonte | Força |
|---|---|---|---|
| **V1** | Suíte de testes automatizados do projeto (unidade/integração/e2e) | comando do projeto (manifesto/config/CI) | Alta |
| **V2** | Script/target de verificação do projeto (`check`, `verify`, `lint`, etapas de CI) | idem | Média-alta |
| **V3** | Boot por comando documentado + coleção/exemplos **existentes** (`.http`, Postman, OpenAPI, `curl` de scripts/CI/README) executados | recursos do projeto | Média |
| **V4** | Boot + sondagem ad hoc (`curl` criado por você) das rotas da Superfície de ataque | efêmero; **só** se P4 = Sim | Baixa-média |
| **V5** | Estática: o código compila/importa; rotas registram | toolchain da stack (classe B) | Baixa |

**Veredito:**
- `VALIDADO (V1)` / `VALIDADO (V1+V3)`: testes passaram **e** (quando aplicável) o boot e as rotas responderam como no baseline.
- `VALIDADO PARCIALMENTE (<degraus>; não exercitado: <lista>)`.
- `NÃO VALIDADO (<motivo>)`.
Abaixo de V3, nunca escreva "a aplicação continua funcionando" sem o qualificador "validação limitada (V4/V5)".

## 4. Protocolo (ordem fixa)

```
Passo 0   Pré-voo
          - A: git status; registrar Run id (relógio do sistema); descobrir SO/shell
          - verificar dependências instaladas (A: pip show/ls node_modules/--version)
          - C (conforme modo): checkpoint (K-00) e instalação de dependências ausentes
          - pasta de evidências: reports/evidence/project-{N}/{Run id}/
Passo 0b  BASELINE (código ORIGINAL, antes da primeira edição) — classe B
          - rodar V1/V2 → E-01...
          - rodar V3 (boot + requisições existentes) → E-0x; registrar status + chaves de cada rota
          - V4 só se permitido
          - baseline vermelho (testes já falham) ⇒ avisar o usuário, registrar "falhas pré-existentes"
            e continuar só se o usuário concordar; a comparação passa a ser "não piorou"
Passos 1..n  aplicar padrões do playbook na ordem canônica; após cada bloco: V5 (compila/importa)
Passo V   VALIDAÇÃO FINAL: repetir exatamente os mesmos comandos → E-nn; montar tabelas antes/depois
Passo R   REAUDITORIA: reaplicar o catálogo ao código novo; "No anti-patterns remaining" só se zero residuais
          (senão listar residuais com o motivo)
Falha     até 2 tentativas de correção por problema; persistindo ⇒ reverter ao checkpoint e relatar
Limpeza   encerrar processos iniciados; liberar portas; registrar arquivos criados fora do código-fonte
```

Reversão: com git, volte ao estado do checkpoint apenas por meios **seguros** (branch/stash do checkpoint criado por você; `git reset --hard`/`clean` são classe X). Sem git, restaure da cópia de checkpoint. Se não houver como reverter com segurança, **pare e pergunte**.

## 5. Subir e parar a aplicação (V3/V4)

1. Use o comando de boot **descoberto** na Fase 1 (README/script/CI/entry point), em **segundo plano** (run in background), com timeout. Nunca presuma a porta: leia-a do código/config/coleção.
2. **Prontidão**: aguarde até (a) o log mostrar linha de "listening/running/Started" **ou** (b) a porta responder à rota de saúde/raiz, com tentativas curtas (ex.: 20 × 0,5 s). Capture as primeiras linhas do log como prova de boot.
3. Execute a bateria (coleção/exemplos existentes; ou sondagem V4 se permitida).
4. **Sempre encerre o processo que você iniciou**, inclusive em falha, e confirme que a porta foi liberada. Porta já ocupada ⇒ reporte e use outra porta **somente** se o projeto permitir configurá-la por ambiente/argumento; **nunca** mate processo que você não iniciou.
5. Windows × Unix: detecte o shell; use a sintaxe correta (variáveis de ambiente, encerrar processo, redirecionamento). Não presuma bash.
6. Banco local do projeto: se subir a aplicação alterar arquivos de dados existentes (seed que apaga), é classe D — trate antes (copie o banco para fora ou pergunte).

## 6. Regras de segurança da bateria de requisições

- Baseline e validação usam **as mesmas** requisições, na mesma ordem.
- Rotas marcadas administrativas/destrutivas e qualquer `DELETE` **não** entram automaticamente. Se um recurso do projeto (script/coleção) as contém, trate a requisição como classe D (pergunta individual) ou marque `NÃO EXERCITADA (rota destrutiva)`.
- Escritas (POST/PUT) vindas de recursos do projeto: só se o banco for local/descartável; senão `NÃO EXERCITADA (motivo)`.
- Registre por rota: método, caminho, status, **chaves** do JSON de resposta (não o conteúdo sensível), tempo.
- Rotas com mudança de contrato aprovada aparecem como `ALTERADO (aprovado)`; qualquer outra diferença é `DIVERGENTE` e **conta como falha**.

## 7. Formato de evidência (`E-nn`)

Cada execução vira um bloco no relatório **e** um arquivo bruto em `reports/evidence/project-{N}/{Run id}/E-nn-<slug>.log` (escreva a saída capturada, com segredos mascarados, usando a ferramenta de escrita; não crie nada dentro do projeto).

```
### E-02 · <descrição> (<baseline|após refatoração>)
Comando:      <literal>                         Diretório: <cwd>
Origem:       <K-nn · arquivo:linha onde foi descoberto> · Classe <B> · Autorização: <automática (classe B)|lote aprovado|individual aprovada>
Início/Fim:   <ISO 8601> → <ISO 8601> (duração <s>)        Exit code: <n>
Ambiente:     <runtime e versões relevantes>
Resultado:    <passed X | failed Y | skipped Z>   (baseline E-01: <...>)
Saída (início e fim; segredos mascarados):
  <~15 primeiras linhas>
  [... N linhas omitidas ...]
  <~15 últimas linhas>
Bruto:        reports/evidence/project-{N}/{Run id}/E-02-<slug>.log
Artefatos:    <junit.xml, cobertura, screenshots, vídeos, traces — somente os gerados pelo projeto/runner>
Integridade:  testes alterados/adicionados: <0 | n — ver "Alterações em testes" / "Testes adicionados">  (verificado por: <git diff, ou snapshots em tests-before/ se não versionados>)
```

**E-00 — evidência da Fase 1.** Na Fase 2 (passo 9 do `SKILL.md`), junto do relatório, grave `reports/evidence/project-{N}/{Run id}/E-00-fase1-analise.txt` com: o bloco `PHASE 1: PROJECT ANALYSIS` **literal**; a lista dos arquivos-fonte contados (caminho e linhas) e o método de contagem; as rotas encontradas (método, caminho, arquivo:linha); o inventário de validação; os comandos descobertos (com classe). Segredos mascarados. O checklist da Fase 1 cita `E-00`. Não altera o formato do relatório.

Artefatos adicionais, quando houver ajuste/criação de testes: `tests-before/<caminho>` (cópia do original), `E-nn-diff-testes.patch` (diff unificado) e as execuções vermelha/verde da seção 8.9.

Para o usuário **ver e crer** que rodou:
1. Comando literal, diretório, horários, duração, exit code.
2. Contagens do próprio runner e comparação com o baseline: o **nº de testes não pode cair** e `skipped` não pode subir sem explicação.
3. Saída bruta salva em arquivo (não só resumo).
4. Artefatos que o projeto já gera (relatório HTML, junit, cobertura, screenshots/vídeos/traces de Playwright/Cypress se configurados) são **coletados e referenciados**; não force a geração instalando algo novo.
5. **Screenshot (opcional)**: se o projeto serve UI web e o agente tem ferramenta de navegador, capture a página principal servida (classe B, host local); salve em `E-nn-<slug>.png` na pasta de evidências. Para APIs puras, o equivalente é a transcrição do terminal (item 3) e a tabela de rotas.
6. **Anti-fabricação**: cada ✓ do bloco `Validation` e do checklist cita um `E-nn`; evidência só existe se saiu de uma chamada de ferramenta real; comando não executado aparece como `NÃO EXECUTADO (motivo)`.
7. Ao final, imprima um resumo compacto (`Resumo da validação`) e o caminho da pasta de evidências.

## 8. Política de alteração de testes

**8.1 Princípio.** Testes podem e, muitas vezes, devem mudar numa refatoração. O que é proibido é alterá-los **só para passar**. Um teste alterado precisa continuar fazendo sentido e validando corretamente a mesma intenção.

**8.2 Quando é permitido alterar:** (a) a refatoração moveu módulos, funções, imports ou fixtures que o teste usa; (b) uma mudança de contrato **aprovada** (`CT-xx`) alterou o comportamento que o teste afirma; (c) é necessária mudança de configuração/ambiente de teste (variável de ambiente, banco temporário, credencial de seed vinda do ambiente).

**8.3 Classes**

| Classe | O que é | Regra |
|---|---|---|
| **T1 mecânica** | imports, caminhos, fixture/setup, credencial de teste, autenticação necessária | asserções **idênticas** |
| **T2 contrato** | a asserção muda porque o contrato aprovado mudou | a nova asserção expressa o novo contrato **de forma explícita** (ex.: com token ⇒ 200 e sem token ⇒ 401), preferindo manter a asserção original no cenário válido |
| **T3 proibida** | remover ou comentar teste/asserção; `skip`/`xfail`/`skipif`; afrouxar o esperado (200 → "200 ou 500"); `assert True`; engolir exceção; mockar o objeto sob teste; reduzir os dados que exercitam a regra; mudar o esperado sem `CT-xx` correspondente | **nunca**, nem sob pedido |
| **T4 novo** | teste adicionado para provar comportamento novo/alterado (**só Opção 2**) | seção 8.9 |

**8.4 "Continua fazendo sentido" — verifique por teste alterado:** mesmo nome/cenário/intenção; nº de asserções ≥ o original; cada asserção original mantida ou substituída por equivalente/mais forte (justifique); o teste ainda **pode falhar** se o comportamento sob teste regredir (depende do código real, não de um valor copiado da nova saída sem análise); o esperado vem do contrato aprovado, não do que o código passou a retornar.

**8.5 Procedimento**
1. **Regressão primeiro:** se um teste falha após refatorar, investigue se é regressão (corrija o código) ou consequência de `CT-xx` aprovado. Só então adapte o teste.
2. **Snapshot** do arquivo original em `reports/evidence/project-{N}/{Run id}/tests-before/<caminho>` **antes** de editar (permite diff mesmo sem git ou com testes não versionados).
3. Edite o mínimo necessário.
4. Gere o diff unificado e grave `E-nn-diff-testes.patch`.
5. Reexecute o teste alterado **e** a suíte completa; compare com o baseline (nº de testes **não cai**; `skipped` **não sobe** sem explicação).
6. Registre em "Alterações em testes" (`03`, seção 4).

**8.6 Aprovação.** Ajustes T1/T2/T4 **rastreáveis** a `C-xx`/`CT-xx` já aprovados não geram pergunta extra (a aprovação do escopo/contrato os cobre; os previstos aparecem em "Testes afetados" na Fase 2). **Pergunte** (`Ajustar o teste` · `Manter e registrar a falha`) apenas se: (i) o ajuste não é rastreável a mudança aprovada; (ii) exigiria reescrever a maior parte das asserções do teste; (iii) o teste parece ter bug próprio. T3 nunca.

**8.7 Integridade final.** A lista de testes alterados/adicionados deve ser **igual** à registrada (com git: `git diff` nos caminhos de teste; sem git ou não versionados: compare com `tests-before/`). Divergência ⇒ reverta o ajuste não registrado e refaça a validação.

**8.8 Opção 1 (manter contrato).** Não há ajuste de contrato em testes; só T1 mecânico se a refatoração mover módulos/fixtures.

**8.9 Comprovação das mudanças de contrato (Opção 2).** Cada `CT-xx` aplicado precisa de evidência produzida pela própria refatoração:
1. **Teste novo ou atualizado** (T2/T4) no framework e no diretório de testes existentes, sem nova dependência, rastreado a `CT-xx`/`F-xxx`. Exemplos: sem credencial ⇒ 401; credencial inválida ⇒ 401; sem perfil ⇒ 403; credencial válida ⇒ comportamento esperado; rota removida ⇒ 404/405; campo ausente na resposta; entrada inválida ⇒ 400/404/409.
2. **Execução verde** no código refatorado (`E-nn`).
3. **Prova de sensibilidade quando viável:** executar o teste novo contra o **checkpoint do código original** (cópia fora do projeto ou worktree do checkpoint, classe B na cópia); ele deve **falhar** lá. Registre a execução vermelha (`E-nn`). Sem checkpoint utilizável, declare "sensibilidade não verificada".
4. **Sem framework de testes:** comprove por sondagem ad hoc (exige P4 = Sim): chamada sem credencial ⇒ 401, com credencial ⇒ sucesso, etc., com `E-nn`. Sem ambos, o item fica `NÃO VALIDADO` (declarado, e avisado ao usuário antes de aplicar — `07`, seção 4.1).
5. Preencha a tabela antes/depois com a coluna **"Prova"** (`E-nn`) e a seção "Testes adicionados" do anexo.

## 9. Casos especiais

- **Sem nenhum teste/coleção:** V1–V3 indisponíveis ⇒ perguntar P4 (ad hoc) na rodada 1; sem permissão, validação em V5 com veredito `VALIDADO PARCIALMENTE (V5)` ou `NÃO VALIDADO`; reforce TST-01 como recomendação. Na Opção 1 **não crie testes**; na Opção 2 sem framework de testes, comprove por sondagem ad hoc (seção 8.9, item 4).
- **Projeto não-HTTP** (CLI, biblioteca, worker): "boot" = executar o ponto de entrada com argumento de ajuda/versão ou o exemplo do README; "endpoints" = funções/comandos públicos exercitados por testes existentes. Marque o item do checklist "Endpoints originais respondem" como `N/A (não é serviço HTTP)` com motivo.
- **Dependência externa** (banco/serviço que não é local): não conecte; valide estaticamente e por testes que usem mocks/containers locais já definidos no projeto; registre o limite.
- **Dependências ausentes:** classe C; sem aprovação, a validação cai para V5 e isso é declarado.
- **Aplicação com seed que sobrescreve dados:** copie/aponte para banco descartável antes (se o projeto permitir por variável) ou trate como D.
- **Testes lentos/travados:** aplique timeout; registre `TIMEOUT` com a saída parcial como evidência; não ignore silenciosamente.

## 10. Checklist de saída da Fase 3

- [ ] Baseline registrado antes da primeira edição (E-01…).
- [ ] Validação final com os **mesmos** comandos (E-nn…).
- [ ] Tabela antes/depois de rotas e de testes.
- [ ] Testes alterados/adicionados somente os registrados (T1/T2/T4), com snapshot, diff, justificativa, reexecução e, na Opção 2, prova de sensibilidade (ou "não verificada" declarada).
- [ ] `E-00` gravado na Fase 2 e citado no checklist da Fase 1.
- [ ] Processos encerrados e portas liberadas.
- [ ] Reauditoria executada; residuais listados.
- [ ] Todos os ✓ do checklist e do bloco `Validation` referenciam `E-nn`.
