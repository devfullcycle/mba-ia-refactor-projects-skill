================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask (3.1.1) + flask-cors (5.0.1)
Files:   4 analisados (app.py, controllers.py, models.py, database.py) | ~780 linhas de código
Database: SQLite (`loja.db`) / driver `sqlite3` direto, SQL cru por concatenação

## Summary
| Severidade | Qtde |
|---|---|
| CRITICAL | 3 |
| HIGH     | 4 |
| MEDIUM   | 3 |
| LOW      | 2 |
| **Total** | **12** |

## Current Architecture
Nível **parcial**: existe separação em arquivos (`app.py` = rotas, `controllers.py`, `models.py`, `database.py`), mas tudo na raiz, sem pastas por responsabilidade. Há vazamento entre camadas: `app.py` contém handlers administrativos com SQL direto, `controllers.py` acessa o banco no `health_check` e concentra validação/notificações, e `models.py` mistura SQL, regra de negócio (desconto, estoque) e serialização. A conexão SQLite é um singleton global em `database.py`, com schema e seed executados dentro de `get_db()`.

## Findings

### [CRITICAL] AP-01 — SQL Injection (queries por concatenação)
- **File**: `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`, `models.py:92`, `models.py:109-111`, `models.py:126-129`, `models.py:140`, `models.py:148-151`, `models.py:155-166`, `models.py:174`, `models.py:188`, `models.py:192`, `models.py:220`, `models.py:224`, `models.py:279-281`, `models.py:289-297`; `app.py:69`
- **Description**: Todas as queries são montadas com `"..." + variavel + "..."` usando dados do request (ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`). `/admin/query` executa SQL arbitrário vindo do body.
- **Impact**: Bypass de login (`' OR '1'='1`), leitura/alteração/destruição de qualquer tabela.
- **Recommendation**: Usar placeholders `?` com parâmetros em todas as queries; remover/proteger `/admin/query` (Playbook P1).

### [CRITICAL] AP-02 — Credenciais e segredos hardcoded
- **File**: `app.py:7-8`, `app.py:88`, `controllers.py:286-289`, `database.py:5`, `database.py:75-79`
- **Description**: `SECRET_KEY = "minha-chave-super-secreta-123"` fixa no código, `DEBUG = True` fixo (também `debug=True` em `app.run`), caminho do banco fixo, senhas de seed em claro (`admin123`, `123456`, `senha123`).
- **Impact**: Segredo versionado no repositório; debugger do Werkzeug ativo e exposto em `0.0.0.0` permite execução remota de código.
- **Recommendation**: Mover para variáveis de ambiente via módulo `config` (Playbook P2).

### [CRITICAL] AP-03 — Exposição de dados sensíveis / autenticação fraca
- **File**: `database.py:27-34`, `models.py:83`, `models.py:99`, `models.py:109-111`, `models.py:126-129`, `controllers.py:285-289`, `app.py:47-57`, `app.py:59-78`, `app.py:9`
- **Description**: Senhas armazenadas e comparadas em texto puro; `GET /usuarios` e `GET /usuarios/<id>` devolvem o campo `senha`; `/health` devolve `secret_key`; `POST /admin/reset-db` (apaga todas as tabelas) e `POST /admin/query` (SQL arbitrário) não exigem autenticação; CORS aberto para qualquer origem.
- **Impact**: Comprometimento de contas e perda total de dados por qualquer cliente anônimo.
- **Recommendation**: Hash de senha (werkzeug `generate_password_hash`/`check_password_hash`), serializer que omite `senha`, remover `secret_key` do health, proteger ou remover rotas admin (Playbook P2, P8).

### [HIGH] AP-04 — God File
- **File**: `models.py:1-314`, `controllers.py:1-292`, `app.py:1-88`
- **Description**: `models.py` (314 linhas) mistura SQL, regras de negócio (desconto de faturamento 256-262, validação de estoque 144-145), orquestração de pedido e serialização manual. `app.py` mistura composition root, rota inline `/` e dois handlers administrativos com acesso ao banco.
- **Impact**: Difícil testar e evoluir por recurso (produtos/usuários/pedidos/relatórios no mesmo arquivo).
- **Recommendation**: Separar por recurso em `models/`, `controllers/`, `routes/`; handlers admin saem do entry point (Playbook P3, P4).

### [HIGH] AP-05 — Lógica de negócio e acesso a dados no controller/rota
- **File**: `controllers.py:52-54`, `controllers.py:208-210`, `controllers.py:247-250`, `controllers.py:264-292`; `app.py:47-78`
- **Description**: Controller contém lista de categorias válidas, regras de validação, "envio" de e-mail/SMS/push e notificações por status; `health_check` abre cursor e executa SQL; `app.py` executa SQL nos handlers admin.
- **Impact**: Viola MVC; regra não reutilizável nem testável sem HTTP.
- **Recommendation**: Mover SQL para models e regras para services/validators; controller só orquestra (Playbook P3, P4, P5).

### [HIGH] AP-06 — Estado global mutável e conexão global
- **File**: `database.py:4-10`
- **Description**: `db_connection` global criado com `check_same_thread=False` e compartilhado entre todas as requests/threads; schema e seed rodam dentro de `get_db()` na primeira chamada.
- **Impact**: Race conditions e transações misturadas entre requests; ciclo de vida da conexão não controlado; testes frágeis.
- **Recommendation**: Conexão por request (`flask.g` + `teardown_appcontext`), init de schema/seed em função própria no boot (Playbook P6).

### [HIGH] AP-07 — Tratamento de erros ausente ou inadequado
- **File**: `controllers.py:10-12`, `controllers.py:21-22`, `controllers.py:60-62`, `controllers.py:95-96`, `controllers.py:108-109`, `controllers.py:125-126`, `controllers.py:133-134`, `controllers.py:143-144`, `controllers.py:164-165`, `controllers.py:185-186`, `controllers.py:218-220`, `controllers.py:226-227`, `controllers.py:234-235`, `controllers.py:254-255`, `controllers.py:261-262`, `controllers.py:291-292`; `app.py:77-78`; `models.py:133-169`; `models.py:275-283`
- **Description**: Todo handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo mensagens internas ao cliente. `criar_pedido` faz vários INSERT/UPDATE sem `rollback` em caso de falha (pedido parcial). `atualizar_status_pedido` não verifica se o pedido existe (retorna 200 mesmo assim). Cancelar pedido apenas imprime "Devolver estoque" sem devolver.
- **Impact**: Vazamento de internals, inconsistência de dados, formato de erro não uniforme.
- **Recommendation**: Error handler central com formato uniforme, exceções de domínio, transação com rollback (Playbook P7).

### [MEDIUM] AP-08 — Problema N+1 / queries ineficientes
- **File**: `models.py:171-201`, `models.py:203-233`, `models.py:139-166`, `models.py:239-254`, `controllers.py:268-275`; `SELECT *` em `models.py:7`, `28`, `75`, `92`, `174`, `206`, `289`
- **Description**: `get_pedidos_usuario` e `get_todos_pedidos` fazem 1 query de itens por pedido e 1 query de produto por item; `criar_pedido` consulta o produto duas vezes por item; relatório faz 5 queries separadas; listagens sem paginação.
- **Impact**: Latência cresce com o volume de pedidos.
- **Recommendation**: JOIN `pedidos`/`itens_pedido`/`produtos` numa única query, agregações em uma consulta, colunas explícitas (Playbook P9).

### [MEDIUM] AP-09 — Validação de entrada ausente ou duplicada
- **File**: `controllers.py:24-54` vs `controllers.py:64-93`, `controllers.py:118-121`, `controllers.py:169-171`, `controllers.py:195-203`, `controllers.py:239-243`, `controllers.py:153-158`
- **Description**: Validação de produto duplicada e divergente entre criar e atualizar (atualizar não valida tamanho do nome nem categoria). Não há checagem de tipo: `preco < 0` com string gera `TypeError` → 500. `login` e `atualizar_status_pedido` chamam `dados.get` sem checar `None`. `float()` em `buscar_produtos` sem tratamento. Itens do pedido acessados com `item["produto_id"]` sem validar chave/tipo/quantidade. E-mail sem formato e sem unicidade.
- **Impact**: Erros 500 para entrada inválida e dados inconsistentes.
- **Recommendation**: Validador único reutilizado por criar/atualizar, retornando 400 (Playbook P5).

### [MEDIUM] AP-10 — Duplicação de código (DRY)
- **File**: `models.py:12-21`, `models.py:31-40`, `models.py:304-313`; `models.py:79-86`, `models.py:95-102`; `models.py:178-199`, `models.py:211-231`
- **Description**: Conversão linha→dict de produto repetida 3x, de usuário 2x, e o bloco de montagem de pedido+itens copiado integralmente entre as duas listagens de pedidos.
- **Impact**: Correções precisam ser replicadas em vários pontos.
- **Recommendation**: Helpers/serializers únicos (`produto_to_dict`, `pedido_to_dict`) (Playbook P4, P5).

### [LOW] AP-11 — Magic numbers e strings
- **File**: `models.py:257-262`, `controllers.py:52`, `controllers.py:242`, `controllers.py:285-288`, `app.py:36`, `app.py:88`
- **Description**: Faixas de desconto (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`), status de pedido, categorias, `"1.0.0"` duplicado, `"producao"`, porta `5000` como literais.
- **Impact**: Regras de negócio escondidas e difíceis de alterar.
- **Recommendation**: Constantes nomeadas/enums em módulo de config/domínio (Playbook P10).

### [LOW] AP-12 — Nomenclatura e convenções inconsistentes
- **File**: `controllers.py:8`, `11`, `57`, `61`, `106`, `161`, `179`, `182`, `208-210`, `219`, `248-250`; `app.py:56`, `83-86`; `models.py:2`; `database.py:2`
- **Description**: `print` de debug no lugar de logger; parâmetro `id` sombreia o builtin (`controllers.py:14`, `24`, `64`, `98`, `136`; `models.py:24`, `54`, `65`, `89`); imports não usados (`sqlite3` em `models.py`, `os` em `database.py`); mistura de prefixos (`get_todos_produtos` vs `listar_produtos`).
- **Impact**: Legibilidade e observabilidade reduzidas.
- **Recommendation**: Usar `logging`, renomear para `produto_id`/`usuario_id`, remover imports mortos (Playbook P10).

## Deprecated APIs
Nenhuma API deprecated detectada. (Flask 3.1.1 / flask-cors 5.0.1: o código usa `app.add_url_rule`, `app.route`, `app.config`, `jsonify` — todos vigentes. Não há `before_first_request`, `flask.ext`, `datetime.utcnow` ou equivalentes. A concatenação de SQL e as senhas em texto puro já estão cobertas por AP-01/AP-03.)

## Target Architecture (proposta)
```
code-smells-project/
├── app.py                      # composition root (create_app, registra blueprints)
├── config/
│   └── settings.py             # SECRET_KEY, DEBUG, DB_PATH, PORT via env
├── database/
│   ├── connection.py           # get_db por request (flask.g), teardown
│   └── schema.py               # create tables + seed
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   ├── pedido_model.py
│   └── relatorio_model.py
├── services/
│   ├── pedido_service.py       # estoque, total, notificações
│   └── relatorio_service.py    # regra de desconto
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   └── admin_controller.py
├── routes/                     # blueprints: produtos, usuarios, pedidos, relatorios, admin, health
├── views/
│   └── serializers.py          # produto/usuario/pedido (sem senha)
└── middlewares/
    └── error_handler.py        # tratamento central de erros
```

================================
Total: 12 achados (3 critical, 4 high, 3 medium, 2 low)
================================

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]
