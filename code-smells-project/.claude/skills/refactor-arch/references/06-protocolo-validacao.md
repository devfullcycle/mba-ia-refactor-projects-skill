# 06 — Protocolo de validação e evidências (Fase 3)

Define **como provar** que a aplicação continua funcionando e **como mostrar ao usuário** que a prova é real. Complementa `07-politica-comandos-aprovacoes.md` (quem pode rodar o quê).

## 1. Princípios

1. **Só recursos do projeto** (decisão D5): testes, scripts, targets, configs, CI e coleções/exemplos de requisição que **já existem**. Não crie testes, scripts, coleções ou helpers no projeto. Não adicione ferramenta de teste que o projeto não declare.
2. **Comparar com o baseline**: tudo que for medido depois é comparado ao que foi medido **antes** de editar, com o mesmo comando.
3. **Evidência real ou nada**: cada ✓ aponta um `E-nn` produzido por chamada de ferramenta desta sessão. Execução pulada = `NÃO EXECUTADO`. Nunca preencha resultado por inferência.
4. **Compilar, subir, testar rodam sempre**, sem confirmação (classe B), em qualquer modo. Só instalação/ambiente (C) e destrutivos (D) dependem de aprovação.
5. **Testes são imutáveis**: é proibido editar, remover ou marcar `skip` em teste existente para fazê-lo passar. Se uma mudança de contrato aprovada exigir ajuste de teste, pergunte (ver `07`, seção 4.3) e liste a alteração à parte.
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
Integridade:  testes alterados pela skill: <0 | lista>  (verificado por: <git diff --name-only nos caminhos de teste>)
```

Para o usuário **ver e crer** que rodou:
1. Comando literal, diretório, horários, duração, exit code.
2. Contagens do próprio runner e comparação com o baseline: o **nº de testes não pode cair** e `skipped` não pode subir sem explicação.
3. Saída bruta salva em arquivo (não só resumo).
4. Artefatos que o projeto já gera (relatório HTML, junit, cobertura, screenshots/vídeos/traces de Playwright/Cypress se configurados) são **coletados e referenciados**; não force a geração instalando algo novo.
5. **Screenshot (opcional)**: se o projeto serve UI web e o agente tem ferramenta de navegador, capture a página principal servida (classe B, host local); salve em `E-nn-<slug>.png` na pasta de evidências. Para APIs puras, o equivalente é a transcrição do terminal (item 3) e a tabela de rotas.
6. **Anti-fabricação**: cada ✓ do bloco `Validation` e do checklist cita um `E-nn`; evidência só existe se saiu de uma chamada de ferramenta real; comando não executado aparece como `NÃO EXECUTADO (motivo)`.
7. Ao final, imprima um resumo compacto (`Resumo da validação`) e o caminho da pasta de evidências.

## 8. Verificação de integridade dos testes

Após a validação final: (a) `git diff --name-only` (classe A) restrito aos caminhos de teste; (b) comparar contagem de testes/skips com o baseline; (c) sem git, compare contra a cópia de checkpoint. Qualquer teste modificado sem aprovação ⇒ reverta a modificação e refaça a validação.

## 9. Casos especiais

- **Sem nenhum teste/coleção:** V1–V3 indisponíveis ⇒ perguntar P4 (ad hoc) na rodada 1; sem permissão, validação em V5 com veredito `VALIDADO PARCIALMENTE (V5)` ou `NÃO VALIDADO`; reforce TST-01 como recomendação. **Não crie testes.**
- **Projeto não-HTTP** (CLI, biblioteca, worker): "boot" = executar o ponto de entrada com argumento de ajuda/versão ou o exemplo do README; "endpoints" = funções/comandos públicos exercitados por testes existentes. Marque o item do checklist "Endpoints originais respondem" como `N/A (não é serviço HTTP)` com motivo.
- **Dependência externa** (banco/serviço que não é local): não conecte; valide estaticamente e por testes que usem mocks/containers locais já definidos no projeto; registre o limite.
- **Dependências ausentes:** classe C; sem aprovação, a validação cai para V5 e isso é declarado.
- **Aplicação com seed que sobrescreve dados:** copie/aponte para banco descartável antes (se o projeto permitir por variável) ou trate como D.
- **Testes lentos/travados:** aplique timeout; registre `TIMEOUT` com a saída parcial como evidência; não ignore silenciosamente.

## 10. Checklist de saída da Fase 3

- [ ] Baseline registrado antes da primeira edição (E-01…).
- [ ] Validação final com os **mesmos** comandos (E-nn…).
- [ ] Tabela antes/depois de rotas e de testes.
- [ ] Nenhum teste alterado (ou alteração aprovada e listada).
- [ ] Processos encerrados e portas liberadas.
- [ ] Reauditoria executada; residuais listados.
- [ ] Todos os ✓ do checklist e do bloco `Validation` referenciam `E-nn`.
