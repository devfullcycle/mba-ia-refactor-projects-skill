# Checklist de Validação por Fase (auto-verificação interna)

Ao final de **cada fase**, execute o checklist correspondente como uma **auto-verificação interna**.

**Regra de manifestação (importante):**
- A validação é **silenciosa por padrão**: se todos os itens da fase passarem, **não imprima** o
  checklist nem qualquer mensagem — apenas siga para a próxima fase.
- A validação só se **manifesta quando algo está fora do padrão**: se algum item falhar, informe
  qual item falhou e **corrija antes de prosseguir** (refaça a parte da fase que falhou). Só avance
  quando todos os itens passarem.

Ou seja: o console permanece limpo no caminho feliz; o checklist só aparece para sinalizar e
resolver um desvio.

---

## Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

Se algum falhar: releia os manifestos/fontes e refaça a detecção antes de seguir para a Fase 2.

## Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

Se "mínimo de 5 findings" falhar: **re-audite com mais profundidade** — os projetos-alvo têm vários
problemas; menos de 5 quase sempre indica auditoria rasa, não projeto limpo. Reveja o catálogo
inteiro (`02-antipattern-catalog.md`) e a aderência a MVC (`04-mvc-guidelines.md`).
Se qualquer outro item falhar: ajuste o relatório antes de exibir o gate de confirmação.

## Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

Lembre do layout por linguagem (`04-mvc-guidelines.md`): **Python sem `src/`** (camadas na raiz),
**Node com `src/`**. Se "aplicação inicia sem erros" ou "endpoints respondem" falharem, **não
finalize** — corrija e revalide (subir app + bater endpoints) até passar.
