# code-smells-project

API de E-commerce em Python/Flask (produtos, usuários, pedidos e relatórios de vendas), refatorada para MVC em camadas pela skill `refactor-arch` (`.claude/skills/refactor-arch/`).

> Status: skill executada neste projeto (3 fases concluídas e validadas).

---

## A) Análise Manual

Li o código original inteiro (`app.py`, `controllers.py`, `models.py` e `database.py`, uns 780 linhas) antes de rodar a skill e anotei o que mais me chamou atenção. Usei estes critérios de severidade:

- **CRITICAL:** falha grave de segurança ou arquitetura, como SQL Injection e credencial hardcoded.
- **HIGH:** violação forte de MVC ou SOLID que complica a manutenção e os testes, como regra de negócio presa no controller, acoplamento sem injeção de dependência e estado global mutável.
- **MEDIUM:** problemas de padronização, duplicação e performance moderada, como queries N+1.
- **LOW:** legibilidade, nomes ruins e magic numbers.

| # | Severidade | O que encontrei | Onde | Por que incomoda |
|---|---|---|---|---|
| 1 | CRITICAL | **SQL Injection.** Todas as queries são montadas concatenando strings com o que vem da requisição. | `models.py` (28, 49, 58, 110, 291...) | O login cai com `' OR '1'='1`, e dá para ler ou alterar qualquer dado do banco. |
| 2 | CRITICAL | **Chave secreta hardcoded.** A `SECRET_KEY` está escrita direto no código (e ainda aparece no `/health`). | `app.py:7` | Quem vê o repositório já tem o segredo, e não dá para trocá-lo sem mexer no código. |
| 3 | HIGH | **Regra de negócio dentro do controller.** Ele valida categorias, preço e estoque, dispara as notificações (email/SMS/push) e decide o que fazer em cada status do pedido. | `controllers.py` 24-50, 208-210, 242-250 | A regra fica presa na camada HTTP e não dá para testar sozinha. Para piorar, cancelar um pedido só imprime "Devolver estoque" e não devolve nada. |
| 4 | HIGH | **Camadas misturadas.** `app.py` e o `health_check` rodam SQL direto, e o model carrega regra de negócio (desconto por faturamento). | `app.py` 47-69, `controllers.py` 264-273, `models.py` 256-262 | Ninguém sabe onde termina a rota, o controller e o model. Mudar o banco mexe em tudo. |
| 5 | HIGH | **Acoplamento forte e estado global.** Controllers chamam `models` e `get_db()` direto, e a conexão SQLite é uma variável global mutável compartilhada entre requisições. | `database.py` 4-11, `models.py:1`, `controllers.py:3` | Não dá para trocar o banco nem isolar nos testes, e ainda há risco de condição de corrida. |
| 6 | MEDIUM | **Código duplicado.** A conversão de produto para dicionário aparece 3 vezes, a de usuário 2 vezes, e a validação de criar produto foi copiada para atualizar (e já divergiu). | `models.py` 12-21, 31-40, 304-313 | Qualquer correção precisa ser repetida em vários lugares. |
| 7 | MEDIUM | **Tratamento de erro espalhado.** Cada handler do controller repete o mesmo `try/except Exception` e devolve `str(e)` com status 500. Não existe um tratador de erros global, e o formato da resposta varia (uns com `sucesso: False`, outros só com `erro`). | `controllers.py` 10-12, 21-22, 60-62, 95-96, 108-109 (e mais 11 ocorrências) | Repetição em todo handler, contrato de erro inconsistente e detalhes internos vazando para o cliente. |
| 8 | LOW | **Magic numbers.** As faixas e percentuais de desconto (10000/0.1, 5000/0.05, 1000/0.02), os status e os limites do nome estão soltos no código. | `models.py` 256-262, `controllers.py:52` | Fica difícil achar e mudar essas regras. |
| 9 | LOW | **Nomes ruins.** O parâmetro `id` sombreia o builtin do Python, e há `cursor2` e `cursor3` sem significado. | `models.py` 24, 187-191 | Atrapalha a leitura e pode gerar bug. |
| 10 | LOW | **`print()` no lugar de log.** Inclusive imprimindo o e-mail do usuário no login. | `controllers.py` 8, 57, 161, 208-210 | Sem níveis de log e com dado pessoal na saída padrão. |

No total são 10 problemas: 2 CRITICAL, 3 HIGH, 2 MEDIUM e 3 LOW.

---

## B) Construção da Skill

### Processo

1. **Estudo da base.** Li os resumos das aulas do MBA e a documentação oficial: [Skills no Claude Code](https://code.claude.com/docs/en/skills), o [Complete Guide to Building Skills](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) e o artigo [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills). Desse estudo saiu um guia próprio (`como-construir-uma-skill.md`) e um template de skill.
2. **Decisões de design a partir do guia.**
   - Divisão em `SKILL.md` enxuto + `references/` + `assets/` + `scripts/`, com *progressive disclosure*: o `SKILL.md` traz o fluxo e as regras, e os detalhes só são lidos quando a fase precisa deles.
   - `disable-model-invocation: true`, porque a skill altera o projeto e só deve rodar quando invocada com `/refactor-arch`.
   - Um script (`scan.sh`) só para o que é determinístico e barato (inventário, arquivos grandes, padrões textuais). O julgamento fica com o modelo.
   - A pausa da Fase 2 é regra inviolável: Fases 1 e 2 são somente leitura e a Fase 3 só começa após `y`.
3. **Primeira versão.** Estrutura em 3 fases (análise, auditoria com relatório e confirmação, refatoração MVC com validação), catálogo de 16 anti-patterns (AP-01 a AP-16, incluindo APIs deprecated), playbook com 12 padrões antes/depois (PB-01 a PB-12), diretrizes de MVC e template de relatório.
4. **Refatoração para agnosticismo de tecnologia.** A primeira versão tinha exemplos presos a linguagens específicas. Reescrevi o catálogo, o playbook e o `scan.sh` com sinais conceituais e pseudocódigo neutro. Depois de detectar a stack por evidência (manifesto, extensões, imports), a skill pesquisa as boas práticas e as APIs deprecated daquela linguagem e versão e monta um Stack Profile interno. Esse perfil alimenta a auditoria e a tradução dos padrões para a forma idiomática da stack. O que não tem fonte é marcado como "a verificar". A pesquisa usa só tecnologia, versão e tema, nunca dados do projeto.
5. **Organização conforme a documentação.** O template do relatório saiu de `references/` e foi para `assets/`, já que é um arquivo usado na saída e não material de consulta.
6. **Ajuste do formato de saída.** Nos testes, as Fases 1 e 2 imprimiam informação extra (Stack Profile, tabela de endpoints, seções de deprecated, plano de refatoração, perguntas antes da confirmação). Passei a tratar esse conteúdo como interno e a exigir a saída exatamente no formato esperado, sem seções adicionais. Decisões pendentes (ex.: migração de senhas) ficam para a Fase 3, registradas em "Deviations" e "Needs Human".

### Estrutura final da skill

```
.claude/skills/refactor-arch/
├── SKILL.md                         # fluxo das 3 fases + regras inviolantes
├── references/
│   ├── project-analysis.md          # como detectar stack, banco, domínio e arquitetura
│   ├── stack-research.md            # pesquisa de boas práticas da stack (Stack Profile)
│   ├── anti-patterns-catalog.md     # AP-01..AP-16 com severidade e sinais
│   ├── mvc-guidelines.md            # camadas, regra de dependência, estrutura-alvo
│   └── refactoring-playbook.md      # PB-01..PB-12 antes/depois em pseudocódigo
├── assets/
│   └── report-template.md           # template do relatório da Fase 2
└── scripts/
    └── scan.sh                      # inventário e candidatos a anti-patterns
```

### Principais regras de projeto da skill

- Nenhum arquivo é alterado antes da confirmação da Fase 2.
- Todo finding cita arquivo e linha exatos, e segredos aparecem mascarados.
- O contrato externo (rotas, status, formato) é preservado, e mudanças deliberadas são registradas como Deviations.
- Não há sucesso declarado sem build/boot e comparação dos endpoints com o baseline, com no máximo 3 tentativas de correção.
- Afirmações sobre deprecations ou práticas sem fonte são marcadas como "a verificar".

---

## C) Resultados

Relatório de auditoria (saída da Fase 2): [audit-project-1.md](../reports/audit-project-1.md).

### Resumo do relatório de auditoria

| CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| 6 | 3 | 4 | 3 | **16** |

Nenhum finding AP-13 (API deprecated) foi encontrado. A pesquisa da stack ficou "partially verified" (3 fontes consultadas), e a lista de APIs removidas/deprecated do Flask 3.1 não apontou uso no código.

### Comparação antes/depois da estrutura

Antes (monolítico, 4 arquivos, ~780 linhas):

```
code-smells-project/
├── app.py            # rotas + endpoints /admin com SQL direto + SECRET_KEY hardcoded
├── controllers.py    # handlers com validação, notificações (print) e acesso ao banco
├── models.py         # 314 linhas: 4 domínios, queries concatenadas, regra, serialização
├── database.py       # conexão global mutável + schema + seed
└── requirements.txt
```

Depois (MVC em camadas):

```
code-smells-project/
├── app.py                  # composition root: create_app() + `python app.py`
├── database.py             # conexão por requisição, schema, seed (senhas em hash)
├── validators.py           # validação de entrada
├── config/                 # settings.py (env) + constants.py
├── models/                 # produto, usuario, pedido, manutencao (queries parametrizadas)
├── services/               # pedido, relatorio, usuario, senha, notificacao
├── controllers/            # produto, usuario, pedido, relatorio, sistema
├── routes/                 # blueprints por domínio
├── middlewares/            # error_handler.py (erros centralizados), auth.py (token admin)
├── .env.example  .gitignore  README.md  requirements.txt
```

Mapeamento MVC: Model → `models/`, Controller → `controllers/` (com regras em `services/`), View/Routes → `routes/` (Blueprints).

### Mudanças deliberadas de comportamento (Deviations)

- Removido `POST /admin/query` (SQL arbitrário). Por isso são 18 endpoints no total, contra 19 originais.
- `POST /admin/reset-db` retorna 403 se `ADMIN_TOKEN` não estiver definido e 401 sem o token correto.
- `GET /usuarios` e `/usuarios/<id>` não devolvem mais o campo `senha`.
- `GET /health` não devolve mais `secret_key`, `debug` e `db_path`.
- `SECRET_KEY` agora é obrigatória: sem ela `python app.py` falha com mensagem clara.
- Debug desligado e host `127.0.0.1` por padrão (antes `debug=True`, `0.0.0.0`), configuráveis via `APP_DEBUG` e `HOST`.
- Erros 500 devolvem `{"erro": "Erro interno do servidor"}` em vez da mensagem da exceção. Rotas inexistentes e JSON inválido retornam JSON.
- Mais validação, que muda alguns 500 para 400: tipos de preço e estoque, filtros `preco_min`/`preco_max` inválidos, itens de pedido sem `produto_id` ou com quantidade ≤ 0, corpos nulos em login e status. A atualização de produto passa a validar nome e categoria como a criação.
- Efeito da correção de SQL Injection: o login com `' OR '1'='1` retorna 401 e a busca com esse termo retorna vazio.
- `GET /pedidos` e `/pedidos/usuario/<id>` ordenam por id.

### Pendências que exigem decisão humana

- Defina `SECRET_KEY` (e `ADMIN_TOKEN`, se quiser os endpoints admin) no ambiente. O valor antigo estava versionado: considere-o comprometido e rotacione.
- Senhas de bancos existentes seguem em texto puro até o próximo login de cada usuário (migração lazy).
- As demais rotas continuam sem autenticação (o login não emite token) e o CORS continua `*` por padrão.
- Cancelar um pedido ainda não devolve estoque, só registra no log (igual ao original).
- O projeto não tem suíte de testes automatizados.

### Checklist de validação

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (e-commerce: produtos, usuários, pedidos, relatórios)
- [x] Número de arquivos analisados condiz com a realidade (4)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (16)
- [x] Detecção de APIs deprecated incluída (verificada; nenhum uso encontrado, logo nenhum finding AP-13)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação (regras em services/)
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (18/19; o 19º, /admin/query, foi removido de propósito)
```

### Logs da aplicação rodando após a refatoração

Boot (`SECRET_KEY` e `ADMIN_TOKEN` definidos, banco temporário):

```
2026-11-21 18:53:48,604 INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

As mesmas 40 chamadas foram feitas no app original (baseline) e no refatorado, e as respostas foram comparadas. Resultado do app refatorado:

```
GET  /                                  -> 200      POST /login (credenciais válidas)  -> 200
GET  /health                            -> 200      POST /login (senha errada)         -> 401
GET  /produtos                          -> 200      POST /login (' OR '1'='1)          -> 401  (antes: 200, SQL Injection)
GET  /produtos/1                        -> 200      POST /pedidos (válido)             -> 201
GET  /produtos/999                      -> 404      POST /pedidos (produto inexistente)-> 400
GET  /produtos/busca?q=gamer            -> 200      POST /pedidos (estoque insuf.)     -> 400
POST /produtos                          -> 201      GET  /pedidos, /pedidos/usuario/2  -> 200
POST /produtos (nome curto / preço < 0) -> 400      PUT  /pedidos/1/status             -> 200
PUT  /produtos/11                       -> 200      GET  /relatorios/vendas            -> 200
DELETE /produtos/11                     -> 200      POST /admin/reset-db (sem token)   -> 401
DELETE /produtos/11 (repetido)          -> 404      POST /admin/reset-db (com token)   -> 200
GET  /usuarios, /usuarios/2             -> 200 (sem campo "senha")
POST /admin/query                       -> 404  (removido)
```

As diferenças em relação ao baseline são só as listadas em "Mudanças deliberadas de comportamento" (campos sensíveis removidos, SQL Injection bloqueada, endpoints admin protegidos ou removidos). O relatório de vendas (`faturamento_bruto 12089.88`, `desconto_aplicavel 1208.99`) e o total do pedido (`12089.88`) ficaram idênticos aos do original.

Testes adicionais com o Flask test client: sem `SECRET_KEY` o app falha no boot com mensagem clara; usuário legado com senha em texto puro entra uma vez e é re-hasheado (`scrypt:`); JSON inválido, filtro de preço inválido e item de pedido inválido retornam 400; `/admin/reset-db` sem `ADMIN_TOKEN` configurado retorna 403.

Não há screenshots. A validação foi feita por logs e requisições HTTP.

### Observações sobre o comportamento da skill

- **Detecção e baseline:** a skill detectou stack, framework e versão pelo manifesto e pelos imports, e mapeou os 19 endpoints como baseline para a Fase 3. A auditoria cruzou o catálogo com o `scan.sh` e a leitura direta. O scan marca candidatos por padrões neutros, e os falsos positivos (concatenação de constantes, nome de cabeçalho) foram descartados lendo o código.
- **Pesquisa da stack:** foram 3 consultas, com verificação parcial. As fontes eram de terceiros e não confirmaram uma lista oficial de removals por versão, então nenhuma deprecation foi afirmada sem fonte.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`claude --version`).
- Python 3.10+ e `pip`.
- A skill em `.claude/skills/refactor-arch/` (já presente neste projeto).
- Opcional: `bash` no PATH, usado pelo script auxiliar `scan.sh`. Sem ele a skill usa Glob/Grep.

### Executando a skill

```bash
cd code-smells-project
claude "/refactor-arch"
```

A skill imprime o resumo da Fase 1 e o relatório da Fase 2, e então pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar. Nada é alterado antes disso.

### Como rodar este projeto

```bash
pip install -r requirements.txt
export SECRET_KEY="<defina um valor forte>"   # obrigatório
export ADMIN_TOKEN="<token>"                  # opcional: habilita POST /admin/reset-db
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado no primeiro boot, com produtos e usuários de exemplo (senhas guardadas como hash). Todas as variáveis de ambiente estão em [.env.example](.env.example). `POST /admin/reset-db` exige o cabeçalho `X-Admin-Token`.

### Como validar que a refatoração funcionou

```bash
# com a aplicação rodando, em outro terminal
curl -s localhost:5000/health
curl -s localhost:5000/produtos
curl -s -X POST localhost:5000/login -H "Content-Type: application/json" \
     -d '{"email":"joao@email.com","senha":"123456"}'
curl -s -X POST localhost:5000/login -H "Content-Type: application/json" \
     -d "{\"email\":\"' OR '1'='1\",\"senha\":\"' OR '1'='1\"}"     # deve retornar 401
curl -s localhost:5000/usuarios                                       # sem campo "senha"
```

Checklist rápido:

1. A aplicação inicia sem erros com o comando de antes (`python app.py`).
2. Cada rota do baseline responde com o mesmo status e formato (diferenças só as de "Mudanças deliberadas de comportamento").
3. Nenhuma query concatenada e nenhum segredo no código: `grep -rn "SECRET_KEY\s*=" --include=*.py .` não deve mostrar valores literais.
4. O relatório de auditoria está em `../reports/audit-project-1.md`.
