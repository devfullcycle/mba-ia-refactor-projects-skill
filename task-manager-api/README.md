# task-manager-api

API de Task Manager em Python/Flask (tasks, usuários, categorias e relatórios), refatorada para MVC em camadas pela skill `refactor-arch` (`.claude/skills/refactor-arch/`).

> Status: skill executada neste projeto (3 fases concluídas e validadas).

---

## A) Análise Manual

Li o código original inteiro (`app.py`, `database.py`, `seed.py`, `models/`, `routes/`, `services/` e `utils/`, 15 arquivos e uns 1160 linhas) antes de rodar a skill. O projeto já tem pastas de camadas, então o foco foi achar o que vaza entre elas. As linhas abaixo são do código original. Usei estes critérios de severidade:

- **CRITICAL:** falha grave de segurança ou arquitetura, como credencial hardcoded e dado sensível exposto.
- **HIGH:** violação forte de MVC ou SOLID que complica a manutenção e os testes, como regra de negócio presa na rota e configuração insegura de produção.
- **MEDIUM:** problemas de padronização, duplicação e performance moderada, como queries N+1, validação ausente e APIs deprecated.
- **LOW:** legibilidade, nomes ruins, magic numbers e código morto.

| # | Severidade | O que encontrei | Onde | Por que incomoda |
|---|---|---|---|---|
| 1 | CRITICAL | **Segredos hardcoded.** A `SECRET_KEY` está escrita em `app.py`, e o usuário e a senha do SMTP estão no construtor do `NotificationService`. | `app.py:13`; `services/notification_service.py` 9-10 | Quem vê o repositório tem os segredos, e não dá para trocá-los sem mexer no código. |
| 2 | CRITICAL | **Autenticação falsa e nenhuma autorização.** O login devolve `'fake-jwt-token-' + id`, que nenhuma rota valida. Qualquer um apaga usuários, tasks e categorias, e cria usuário com `role='admin'` pelo corpo da requisição. | `routes/user_routes.py` 52, 71-78, 134-151, 210; `routes/task_routes.py` 225-238; `routes/report_routes.py` 211-223 | Qualquer pessoa pode se passar por outra, escalar privilégio e destruir dados. |
| 3 | HIGH | **Regra de negócio e acesso a dados dentro das rotas.** O cálculo de atraso, as estatísticas, a taxa de conclusão e as consultas ao banco ficam nos handlers. O `summary_report` tem ~90 linhas com laços aninhados. | `routes/task_routes.py` 11-63, 273-299; `routes/report_routes.py` 12-101, 103-155 | A regra fica presa na camada HTTP e não dá para testar sozinha. O `services/` existe, mas as rotas não o usam. |
| 4 | HIGH | **Configuração insegura de produção.** `app.run(debug=True, host='0.0.0.0')` expõe o debugger do Werkzeug em todas as interfaces, e o CORS está totalmente aberto. | `app.py` 15, 34 | O debugger permite executar código remotamente e vaza stack traces. |
| 5 | MEDIUM | **Tratamento de erro espalhado e silencioso.** Há `except:` genérico que engole o erro sem log, cada rota monta a própria resposta de erro e não existe tratador global. | `routes/task_routes.py` 62, 137, 204, 236; `routes/user_routes.py` 130, 149; `routes/report_routes.py` 186, 207, 221 | Falhas ficam invisíveis, e qualquer exceção não prevista vira um 500 bruto. |
| 6 | LOW | **Magic numbers e strings soltas.** Os limites de título (3 e 200), a faixa de prioridade (1 a 5), o tamanho mínimo da senha (4), as listas de status e de roles e a janela de 7 dias estão soltos no código. As constantes de `utils/helpers.py` 110-116 existem, mas ninguém as usa. | `routes/task_routes.py` 96, 99, 110, 113; `routes/user_routes.py` 64, 71; `routes/report_routes.py:45` | É difícil achar e mudar essas regras, e os valores se repetem. |
| 7 | LOW | **Código morto e imports sem uso.** Quase todo o `utils/helpers.py` nunca é chamado, o `NotificationService` também não, e `Task.validate_status` e `validate_priority` ficam sem uso. `marshmallow`, `requests` e `python-dotenv` estão no `requirements.txt` sem uso. | `utils/helpers.py` 2-108; `services/notification_service.py` 4-48; `models/task.py` 38-48; `requirements.txt` 4-6 | Ruído, e dá a falsa impressão de que existe validação e notificação. |
| 8 | LOW | **Nomes ruins.** Há `p1` a `p5`, `p`, `t`, `u`, `cat` e `pwd`, além de `process_task_data`, que não diz o que faz. O CRUD de categorias mora em `report_routes.py`. | `routes/report_routes.py` 24-28; `models/task.py:45`; `utils/helpers.py` 57, 84 | Atrapalha a leitura e esconde onde cada coisa deve estar. |
| 9 | LOW | **`print()` no lugar de log.** Os eventos e os erros saem por `print`. | `routes/task_routes.py` 149, 153, 219, 234; `routes/user_routes.py` 83, 89, 147 | Sem níveis de log e sem como filtrar ou rotear a saída. |

No total são 9 problemas: 2 CRITICAL, 2 HIGH, 1 MEDIUM e 4 LOW.

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

Relatório de auditoria (saída da Fase 2): [audit-project-3.md](../reports/audit-project-3.md).

### Resumo do relatório de auditoria

| CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| 3 | 3 | 6 | 3 | **15** |

| Severidade | Findings |
|---|---|
| CRITICAL | AP-02 segredos hardcoded (`SECRET_KEY`, senha SMTP); AP-04 MD5 sem sal e senha/hash devolvidos nas respostas; AP-04 sem autenticação (token falso, `role=admin` autoatribuível, DELETE aberto) |
| HIGH | AP-05 regra de negócio nas rotas; AP-07 rotas acessam o banco direto e categorias vivem em `report_routes.py`; AP-08 `debug=True` em `0.0.0.0` e CORS aberto |
| MEDIUM | AP-09 N+1; AP-10 validação ausente; AP-11 `except:` engolindo erro; AP-12 duplicação (regra de atraso repetida 6 vezes); AP-13 `Query.get()` legado; AP-13 `datetime.utcnow()` deprecated |
| LOW | AP-14 magic numbers; AP-15 nomes opacos; AP-16 código morto, imports não usados e `print` |

A pesquisa da stack ficou "partially verified" (3 fontes consultadas). Os dois findings AP-13 têm fonte: o `Query.get()` é legado no SQLAlchemy 2.x, e o `datetime.utcnow()` é deprecated a partir do Python 3.12. A versão de Python de produção ficou como "a verificar", porque o interpretador local é 3.10.

### Comparação antes/depois da estrutura

O projeto já era parcialmente organizado (`models/`, `routes/`, `services/`, `utils/`), mas as rotas concentravam regra, consultas e serialização, e `services/` e `utils/` não eram usados.

Antes (parcialmente em camadas, 15 arquivos, ~1158 linhas):

```
task-manager-api/
├── app.py                  # config hardcoded + SECRET_KEY + debug=True
├── database.py
├── seed.py
├── models/                 # task, user (MD5, devolve senha), category
├── routes/
│   ├── task_routes.py      # 299 linhas: regra, queries, N+1, serialização
│   ├── user_routes.py      # token falso, role livre
│   └── report_routes.py    # relatórios + CRUD de categorias, queries em laço
├── services/               # notification_service (senha SMTP hardcoded, não usado)
└── utils/helpers.py        # funções e constantes mortas
```

Depois (MVC em camadas, 33 arquivos, ~1500 linhas):

```
task-manager-api/
├── app.py                  # composition root: create_app() + `python app.py`
├── database.py
├── seed.py
├── .env.example
├── config/                 # settings.py (env) + constants.py
├── models/                 # base (find/save/delete), task, user, category + acesso a dados
├── controllers/            # task, user, category, report + common (erros de persistência)
├── routes/                 # task, user, category, report, health (só roteamento)
├── middlewares/            # error_handler.py (erros centralizados), auth.py (Bearer)
├── services/               # auth_service (token assinado), notification_service
└── utils/                  # helpers (utc_now), validators, errors (AppError)
```

Mapeamento MVC: Model → `models/` (dados e queries), Controller → `controllers/`, View/Routes → `routes/` (Blueprints).

Principais ganhos mensuráveis: `GET /tasks` passou de 1+2N consultas para 1, `GET /users` e `GET /categories` para 2, e `GET /reports/summary` roda 10 consultas fixas, independentes do volume.

### Mudanças deliberadas de comportamento (Deviations)

- `password` (hash) não aparece mais em nenhuma resposta (criação, atualização, `GET /users/<id>`, login).
- O login devolve um token assinado (itsdangerous) em vez de `fake-jwt-token-<id>`. Não é um JWT e expira em 24h (`TOKEN_MAX_AGE_SECONDS`).
- Passam a exigir `Authorization: Bearer <token>`: `DELETE /tasks/<id>` e `DELETE /categories/<id>` (usuário autenticado), `DELETE /users/<id>` (admin), `PUT /users/<id>` (o próprio usuário ou admin; `role`/`active` só admin). Sem token a resposta é 401, e sem permissão 403.
- `POST /users` com `role` diferente de `user` exige token de admin. O cadastro anônimo como `user` continua funcionando.
- Senhas passam de MD5 para scrypt (werkzeug). Hashes MD5 antigos continuam válidos e são migrados no primeiro login.
- `SECRET_KEY` agora é obrigatória: sem ela `python app.py` falha com mensagem clara.
- Debug desligado e host `127.0.0.1` por padrão (antes `debug=True`, `0.0.0.0`), configuráveis via `APP_DEBUG` e `HOST`.
- Entradas que antes davam 500 agora dão 400: `priority` não numérica, `priority`/`user_id` inválidos na busca, tags que não sejam strings, corpo `null` em `PUT /categories`.
- Validação nova: cor de categoria fora de `#rrggbb` ("Cor inválida"), nome vazio ou não string no PUT de usuário/categoria, `active` não booleano.
- `marshmallow` e `requests` saíram do `requirements.txt` (não eram usados). Os 22 endpoints continuam existindo.

### Pendências que exigem decisão humana

- Defina `SECRET_KEY` (`cp .env.example .env`). Os valores antigos (`SECRET_KEY` e senha SMTP) estão no histórico do git: considere-os comprometidos e rotacione.
- As demais rotas (GET, `POST`/`PUT` de tasks e categorias, cadastro anônimo de `user`) continuam abertas, como no original, para preservar o contrato. Avalie estender a autenticação. Clientes que usam `DELETE` e `PUT /users` precisam enviar o token.
- Contas com MD5 só migram quando o usuário faz login. Planeje o fim do suporte ao MD5.
- `NotificationService` está montado em `app.extensions`, mas nenhuma rota o aciona (igual ao original). O envio real de e-mail não foi testado.
- Não foi validado em Python ≥ 3.12 (o local é 3.10). O CORS segue aberto por padrão (`CORS_ORIGINS=*`).
- O projeto não tem suíte de testes automatizados.

### Checklist de validação

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0, Flask-SQLAlchemy 3.1.1)
- [x] Domínio da aplicação descrito corretamente (Task Manager: tasks, usuários, categorias, relatórios)
- [x] Número de arquivos analisados condiz com a realidade (15)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (15)
- [x] Detecção de APIs deprecated incluída (2 findings AP-13)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (88/88 chamadas idênticas ao baseline; 22 rotas)
```

### Logs da aplicação rodando após a refatoração

Boot (`SECRET_KEY` definida, banco temporário populado com `seed.py`):

```
2026-11-22 16:11:05,047 INFO werkzeug: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

Sem `SECRET_KEY` o boot falha com `config.settings.ConfigError: Missing required config: SECRET_KEY (defina no ambiente ou em .env; veja .env.example)`.

Antes de refatorar, rodei o app original e gravei 88 chamadas (status e corpo, ignorando `password` e timestamps). Depois repeti as mesmas 88 chamadas no app refatorado: **as 88 respostas foram idênticas**. Resumo do app refatorado:

```
GET  /, /health                          -> 200      POST /users (válido / role manager c/ admin)  -> 201
GET  /tasks, /tasks/1                    -> 200      POST /users (email dup.)                      -> 409
GET  /tasks/9999                         -> 404      POST /users (email/senha/role/nome inválidos) -> 400
GET  /tasks/search?q|status|priority|user_id -> 200  PUT  /users/4 (válido)                        -> 200
GET  /tasks/stats                        -> 200      PUT  /users/9999                              -> 404
POST /tasks (completa / mínima / tags)   -> 201      GET  /users/1/tasks                           -> 200
POST /tasks (título/status/prioridade/data inválidos)-> 400   GET /reports/summary, /reports/user/1  -> 200
POST /tasks (usuário/categoria inexistente)          -> 404   GET /reports/user/9999                -> 404
PUT  /tasks/11 (válido)                  -> 200      GET  /categories                              -> 200
PUT  /tasks/11 (inválido)                -> 400/404  POST /categories (válida / sem nome)          -> 201 / 400
DELETE /tasks/11 (com token)             -> 200      PUT/DELETE /categories/<id>                   -> 200 / 404
DELETE /tasks/9999                       -> 404      POST /login (ok / senha errada / inativo)     -> 200 / 401 / 403
GET  /nao-existe -> 404 | PATCH /tasks/1 -> 405 | POST /tasks sem JSON -> 415   (iguais ao original)
```

Verificações adicionais (31 de 31 passaram), com o Flask test client:

- Respostas de login, `GET /users` e `GET /users/<id>` não contêm `password`, e o hash gravado é `scrypt:`.
- `DELETE` sem token retorna 401, `DELETE /users` por não admin retorna 403, e token adulterado retorna 401.
- `POST /users` com `role: admin` retorna 401 sem token e 403 com token de não admin. `PUT /users` de outra conta retorna 403.
- Um usuário com hash MD5 entra uma vez e é re-hasheado. O login seguinte e a senha errada se comportam corretamente.
- A busca com `' OR 1=1 --` retorna lista vazia, e `priority` como string ou `priority=abc` retornam 400 (antes 500).
- Contagem de consultas: `/tasks` 1, `/users` 2, `/categories` 2, `/reports/summary` 10.

Re-scan com `scan.sh` e `pyflakes`: nenhum anti-pattern tratado permaneceu. Sobraram só o MD5 em `models/user.py`, mantido de propósito para migrar contas antigas, e os `print` do `seed.py` (saída de CLI). Não há screenshots: a validação foi feita por logs e requisições HTTP.

### Observações sobre o comportamento da skill

- **Projeto já em camadas:** a skill classificou a arquitetura como "parcialmente em camadas" e não recriou o que existia. Manteve os nomes `models/`, `routes/`, `services/` e `utils/`, e acrescentou `config/`, `controllers/` e `middlewares/`. Também mudou de lugar o que estava errado (categorias fora de `report_routes.py`, helpers mortos removidos).
- **Baseline como régua:** os 22 endpoints foram mapeados na Fase 1 e comparados na Fase 3. A comparação respondeu rápido às dúvidas de contrato, por exemplo: 404/405/415 do Flask continuam com a resposta padrão (o tratador global deixa `HTTPException` passar), e as mensagens de erro de cada rota foram mantidas.
- **Segurança vs. contrato:** a skill aplicou as correções de AP-04 e registrou cada mudança em "Deviations". Parou na autenticação ampla (só as rotas destrutivas e de role foram protegidas) e deixou o resto em "Needs Human".
- **Pesquisa da stack:** foram 3 consultas, com verificação parcial. As fontes confirmaram `Query.get()` como legado e `datetime.utcnow()` como deprecated no Python 3.12, mas não a versão de produção nem o algoritmo padrão do werkzeug. O `scrypt` foi confirmado ao rodar a aplicação.
- **Ambiente:** o interpretador local não tinha as dependências instaladas, então a validação rodou em um virtualenv fora do projeto.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`claude --version`).
- Python 3.10+ e `pip`.
- A skill em `.claude/skills/refactor-arch/` (já presente neste projeto).
- Opcional: `bash` no PATH, usado pelo script auxiliar `scan.sh`. Sem ele a skill usa Glob/Grep.

### Executando a skill

```bash
cd task-manager-api
claude "/refactor-arch"
```

A skill imprime o resumo da Fase 1 e o relatório da Fase 2, e então pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar. Nada é alterado antes disso.

### Como rodar este projeto

```bash
pip install -r requirements.txt
cp .env.example .env          # e preencha SECRET_KEY (obrigatória)
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (ajuste com `HOST`/`PORT`). O `seed.py` popula o banco SQLite (`instance/tasks.db`) com 3 usuários, 4 categorias e 10 tasks. **Rode-o antes do primeiro boot**, senão os endpoints retornam listas vazias. Gere uma chave com `python -c "import secrets; print(secrets.token_hex(32))"`. Todas as variáveis estão em [.env.example](.env.example): `SECRET_KEY` (obrigatória), `DATABASE_URL`, `APP_DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS`, `TOKEN_MAX_AGE_SECONDS`, `LOG_LEVEL` e `EMAIL_*`.

Usuários do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd` (user) e `pedro@email.com` / `pass` (manager).

### Autenticação

`POST /login` devolve um `token` assinado. Envie-o em `Authorization: Bearer <token>`. Exigem token: `DELETE /tasks/<id>`, `DELETE /categories/<id>`, `PUT /users/<id>` (próprio usuário ou admin; `role`/`active` só admin), `DELETE /users/<id>` (admin) e `POST /users` com `role` diferente de `user` (admin).

### Como validar que a refatoração funcionou

```bash
# com a aplicação rodando, em outro terminal
curl -s localhost:5000/health
curl -s localhost:5000/tasks
curl -s localhost:5000/tasks/stats
curl -s localhost:5000/reports/summary
curl -s localhost:5000/users                         # sem campo "password"

# login e uso do token
TOKEN=$(curl -s -X POST localhost:5000/login -H "Content-Type: application/json" \
        -d '{"email":"joao@email.com","password":"1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -s -X DELETE localhost:5000/tasks/10                                    # deve retornar 401
curl -s -X DELETE localhost:5000/tasks/10 -H "Authorization: Bearer $TOKEN"  # deve retornar 200

# entradas que antes causavam 500
curl -s "localhost:5000/tasks/search?priority=abc"                           # deve retornar 400
```

Checklist rápido:

1. A aplicação inicia sem erros com o comando de antes (`python app.py`), com `SECRET_KEY` definida.
2. Cada rota do baseline responde com o mesmo status e formato (diferenças só as de "Mudanças deliberadas de comportamento").
3. Nenhum segredo no código: `grep -rn "SECRET_KEY\s*=" --include=*.py .` não deve mostrar valores literais.
4. Nenhuma resposta contém `password`.
5. O relatório de auditoria está em `../reports/audit-project-3.md`.
