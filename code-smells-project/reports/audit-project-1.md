================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] SQL Injection
File: models.py:28
Description: Query com string concatenation: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`. Input do usuario flui diretamente para a query SQL.
Impact: Atacante pode ler, modificar ou destruir dados do banco via manipulacao do parametro `id`.
Recommendation: Usar parameterized queries: `cursor.execute("SELECT * FROM produtos WHERE id = ?", [id])`

### [CRITICAL] SQL Injection
File: models.py:47-49
Description: INSERT com concatenacao: `cursor.execute("INSERT INTO produtos ... VALUES ('" + nome + "', '" + descricao + "', " + str(preco) + ...)`. Todos os campos sao concatenados diretamente.
Impact: Qualquer campo de produto pode injetar SQL arbitrario.
Recommendation: Usar placeholders: `cursor.execute("INSERT INTO ... VALUES (?, ?, ?, ?, ?)", [nome, descricao, preco, estoque, categoria])`

### [CRITICAL] SQL Injection
File: models.py:57-60
Description: UPDATE com concatenacao: `"UPDATE produtos SET nome = '" + nome + "', descricao = '" + descricao + "'..."`. Mesmo padrao de injection.
Impact: Modificacao nao autorizada de qualquer registro de produto.
Recommendation: Usar parameterized queries com `?` placeholders.

### [CRITICAL] SQL Injection
File: models.py:68
Description: DELETE com concatenacao: `cursor.execute("DELETE FROM produtos WHERE id = " + str(id))`
Impact: Um atacante pode deletar todos os produtos manipulando o parametro.
Recommendation: Usar parameterized query: `cursor.execute("DELETE FROM produtos WHERE id = ?", [id])`

### [CRITICAL] SQL Injection
File: models.py:92
Description: Query de usuario por ID com concatenacao: `cursor.execute("SELECT * FROM usuarios WHERE id = " + str(id))`
Impact: Leitura nao autorizada de dados de usuarios.
Recommendation: Usar parameterized query.

### [CRITICAL] SQL Injection
File: models.py:109-110
Description: Query de login com concatenacao de email e senha: `cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`. Este e o caso mais critico — a senha do usuario e injetada diretamente no SQL.
Impact: Atacante pode bypassar autenticacao injetando `' OR '1'='1` no campo de email ou senha. Pode tambem extrair dados de todas as tabelas.
Recommendation: Usar parameterized query: `cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", [email, senha])`

### [CRITICAL] SQL Injection
File: models.py:126-128
Description: INSERT de usuario com concatenacao: `"INSERT INTO usuarios ... VALUES ('" + nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"`
Impact: Criacao de usuarios com injecao de SQL em qualquer campo.
Recommendation: Usar parameterized query.

### [CRITICAL] SQL Injection
File: models.py:140,148-151,155-160,163-165
Description: Funcao `criar_pedido` com multiplas queries concatenadas: SELECT, INSERT e UPDATE todos com string concatenation usando `item["produto_id"]`, `usuario_id`, etc.
Impact: Manipulacao de pedidos, precos, estoque e dados de itens.
Recommendation: Converter todas as queries para parameterized com `?`.

### [CRITICAL] SQL Injection
File: models.py:174,188,192,219-220,223-224,279-280
Description: Queries em `get_pedidos_usuario`, `get_todos_pedidos` e `atualizar_status_pedido` todas usam concatenacao com IDs recebidos do usuario.
Impact: Leitura e modificacao nao autorizada de pedidos.
Recommendation: Usar parameterized queries em todas as operacoes.

### [CRITICAL] SQL Injection (Dynamic Query Building)
File: models.py:289-297
Description: Funcao `buscar_produtos` monta query dinamicamente com concatenacao: `query += " AND (nome LIKE '%" + termo + "%' ...)"` e `query += " AND categoria = '" + categoria + "'"`. Filtros opcionais sao adicionados via concatenacao.
Impact: Injecao de SQL via parametros de busca `q`, `categoria`, `preco_min`, `preco_max`.
Recommendation: Acumular filtros com `?` e lista de params: `query += " AND nome LIKE ?"; params.append("%" + termo + "%")`

### [CRITICAL] Hardcoded Credentials / Secrets
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — chave secreta do Flask hardcoded no codigo-fonte.
Impact: Qualquer pessoa com acesso ao codigo pode forjar sessoes e tokens JWT.
Recommendation: Mover para variavel de ambiente: `app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")`

### [CRITICAL] Hardcoded Credentials / Secrets
File: database.py:76-78
Description: Senhas de seed em plaintext: `"admin123"`, `"123456"`, `"senha123"` hardcoded no array de usuarios.
Impact: Senhas default conhecidas em producao. Se o seed rodar em prod, usuarios ficam com senhas fracas e conhecidas.
Recommendation: Extrair senhas de seed para variaveis de ambiente ou gerar senhas seguras na inicializacao.

### [CRITICAL] Hardcoded Credentials / Secrets
File: controllers.py:289
Description: Health check retorna a SECRET_KEY na resposta: `"secret_key": "minha-chave-super-secreta-123"`. Endpoint publico expoe credencial.
Impact: Qualquer consumidor do `/health` tem acesso a chave secreta da aplicacao.
Recommendation: Remover campos sensiveis do health check.

### [CRITICAL] God Class / God File
File: models.py:1-315
Description: Arquivo `models.py` com 315 linhas acumula operacoes de 4 dominios distintos: produtos (linhas 4-70), usuarios (linhas 72-131), pedidos (linhas 133-283), relatorios (linhas 235-273). Todas as funcoes de acesso a dados de toda a aplicacao estao em um unico arquivo.
Impact: Impossivel testar dominios em isolamento. Mudancas em produtos podem quebrar pedidos. Viola SRP.
Recommendation: Dividir em arquivos separados por dominio: `models/product_model.py`, `models/user_model.py`, `models/order_model.py`, `models/report_model.py`.

### [CRITICAL] Unauthenticated Sensitive Endpoints
File: app.py:47-57
Description: Endpoint `/admin/reset-db` executa DELETE em todas as tabelas sem nenhuma verificacao de autenticacao. Qualquer usuario anonimo pode chamar `POST /admin/reset-db` e destruir todos os dados.
Impact: Destruicao completa e irreversivel de todos os dados do sistema por qualquer usuario anonimo.
Recommendation: Adicionar middleware de autenticacao e autorizacao admin. Proteger o endpoint com token/autenticacao.

### [CRITICAL] Unauthenticated Sensitive Endpoints
File: app.py:59-78
Description: Endpoint `/admin/query` aceita SQL arbitrario no body (`dados.get("sql")`) e o executa diretamente no banco via `cursor.execute(query)`. Sem autenticacao.
Impact: Qualquer usuario pode executar qualquer SQL: DROP TABLE, ler senhas, modificar dados, criar usuarios admin.
Recommendation: Remover endpoint ou proteger com autenticacao forte. Nunca executar SQL arbitrario recebido via HTTP.

### [CRITICAL] Weak Cryptography
File: database.py:76-78, models.py:109-110
Description: Senhas armazenadas em plaintext no banco. A comparacao de login faz match direto: `WHERE email = ? AND senha = ?` com a senha em texto puro. Nenhum hashing e aplicado.
Impact: Vazamento do banco expoe todas as senhas dos usuarios em texto legivel.
Recommendation: Usar `werkzeug.security.generate_password_hash()` e `check_password_hash()` para hash e verificacao de senhas.

### [HIGH] Business Logic in Route/View Layer
File: controllers.py:208-210
Description: Logica de notificacao embutida no handler de criacao de pedido: `print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado...")`, `print("ENVIANDO SMS: ...")`, `print("ENVIANDO PUSH: ...")`. Notificacoes sao business logic e nao devem estar no controller.
Impact: Impossivel reutilizar ou testar a logica de notificacao. Se mudar para email real, precisa alterar o controller.
Recommendation: Extrair notificacoes para um service: `NotificationService.notify_new_order(pedido_id, usuario_id)`.

### [HIGH] Business Logic in Route/View Layer
File: controllers.py:247-250
Description: Logica de notificacao no handler de atualizacao de status: `if novo_status == "aprovado": print("NOTIFICACAO...")` e `if novo_status == "cancelado": print("NOTIFICACAO...")`. Regras de negocio sobre quando notificar estao no controller.
Impact: Regras de notificacao acopladas ao handler HTTP. Dificil de manter e testar.
Recommendation: Mover regras de notificacao para o controller ou service de pedidos.

### [HIGH] Business Logic in Route/View Layer
File: controllers.py:264-290
Description: Funcao `health_check` executa queries SQL diretamente (`cursor.execute("SELECT 1")`, `cursor.execute("SELECT COUNT(*) FROM produtos")`), misturando logica de acesso a dados com HTTP response.
Impact: Controller acessa banco diretamente, violando a separacao de camadas.
Recommendation: Delegar verificacao de saude para um model ou service.

### [HIGH] Sensitive Data Exposure in API Responses
File: models.py:82-84
Description: Funcao `get_todos_usuarios` inclui campo `"senha": row["senha"]` na serializacao. O endpoint `GET /usuarios` retorna a senha de todos os usuarios.
Impact: Qualquer consumidor da API tem acesso a todas as senhas em plaintext.
Recommendation: Remover campo `senha` da serializacao publica. Criar funcao `to_public_dict()` sem campos sensiveis.

### [HIGH] Sensitive Data Exposure in API Responses
File: models.py:95-101
Description: Funcao `get_usuario_por_id` inclui `"senha": row["senha"]` na serializacao. O endpoint `GET /usuarios/<id>` retorna a senha do usuario.
Impact: Senha do usuario exposta via API publica.
Recommendation: Remover campo `senha` da serializacao.

### [HIGH] Sensitive Data Exposure in API Responses
File: controllers.py:287-289
Description: Health check expoe informacoes sensiveis: `"db_path": "loja.db"`, `"debug": True`, `"secret_key": "minha-chave-super-secreta-123"`.
Impact: Expoe configuracoes internas e credenciais em endpoint publico.
Recommendation: Health check deve retornar apenas `{"status": "ok", "database": "connected"}`.

### [HIGH] Tight Coupling / Global Mutable State
File: database.py:4,9
Description: Conexao de banco armazenada em variavel global mutavel: `db_connection = None` com `global db_connection` em `get_db()`. Todos os modulos importam e dependem deste estado global.
Impact: Impossivel testar com banco mock. Estado compartilhado pode causar problemas sob concorrencia (multiplas threads acessando a mesma conexao SQLite).
Recommendation: Usar injecao de dependencia ou factory pattern. Passar conexao via parametros em vez de estado global.

### [MEDIUM] N+1 Query Problem
File: models.py:171-201
Description: Funcao `get_pedidos_usuario` faz: 1 query para pedidos + 1 query para itens de CADA pedido + 1 query para produto de CADA item. Para N pedidos com M itens cada, gera 1 + N + (N*M) queries.
Impact: Performance degrada linearmente com o numero de pedidos. Para 100 pedidos com 3 itens cada = 401 queries ao banco.
Recommendation: Usar uma unica query com JOINs: `SELECT o.*, oi.*, p.nome FROM pedidos o LEFT JOIN itens_pedido oi ... LEFT JOIN produtos p ...`

### [MEDIUM] N+1 Query Problem
File: models.py:203-233
Description: Funcao `get_todos_pedidos` replica exatamente o mesmo padrao N+1 de `get_pedidos_usuario` — 1 + N + (N*M) queries.
Impact: Mesmo problema de performance, agravado por ser uma listagem de TODOS os pedidos do sistema.
Recommendation: Mesma solucao: query unica com JOINs.

### [MEDIUM] N+1 Query Problem
File: models.py:139-146
Description: Funcao `criar_pedido` faz 1 query SELECT por item dentro do loop para verificar estoque: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))`.
Impact: Performance degrada com o numero de itens no pedido.
Recommendation: Buscar todos os produtos necessarios em uma unica query com `WHERE id IN (...)`.

### [MEDIUM] Duplicated Code
File: models.py:171-201 vs models.py:203-233
Description: Funcoes `get_pedidos_usuario` e `get_todos_pedidos` sao quase identicas — mesma logica de montagem de pedidos com itens, mesmas queries N+1, mesma serializacao. A unica diferenca e o WHERE na query de pedidos.
Impact: Mudancas na estrutura de resposta de pedidos precisam ser feitas em dois lugares.
Recommendation: Extrair logica comum para uma funcao helper que recebe os pedidos e busca os itens.

### [MEDIUM] Duplicated Code
File: controllers.py:30-54 vs controllers.py:73-91
Description: Validacao de produto duplicada entre `criar_produto` e `atualizar_produto`: mesma checagem de campos obrigatorios, mesma validacao de preco negativo, estoque negativo.
Impact: Mudanca em regras de validacao precisa ser replicada manualmente.
Recommendation: Extrair funcao `validate_product_data(dados)` compartilhada entre os dois handlers.

### [MEDIUM] Inadequate Error Handling
File: controllers.py (todas as funcoes)
Description: Todos os 15 handlers usam `try/except Exception as e` como unico tratamento de erro. Sem tipos especificos de excecao. Erros sao retornados como string generica: `{"erro": str(e)}`.
Impact: Erros reais (conexao com banco, constraint violation) sao engolidos e retornados como mensagens genericas. Dificil debug em producao.
Recommendation: Criar middleware de error handling centralizado. Usar excecoes tipadas por dominio. Logar erros ao inves de retornar str(e) para o cliente.

### [LOW] Magic Numbers / Magic Strings
File: models.py:257-262
Description: Constantes de desconto hardcoded: `if faturamento > 10000: desconto = faturamento * 0.1`, `elif faturamento > 5000: desconto = faturamento * 0.05`, `elif faturamento > 1000: desconto = faturamento * 0.02`. Valores sem nome descritivo.
Impact: Regra de negocio dispersa no codigo. Dificil ajustar thresholds ou taxas.
Recommendation: Extrair para constantes nomeadas ou configuracao: `DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]`

### [LOW] Magic Numbers / Magic Strings
File: controllers.py:242
Description: Lista de status validos hardcoded: `["pendente", "aprovado", "enviado", "entregue", "cancelado"]`. Se adicionar um novo status, precisa mudar aqui e no banco.
Impact: Regra de negocio espalhada em magic strings.
Recommendation: Definir constantes ou enum para status de pedido.

### [LOW] Debug Artifacts in Production Code
File: app.py:8,88
Description: Debug mode habilitado: `app.config["DEBUG"] = True` na linha 8 e `app.run(..., debug=True)` na linha 88. Em producao, expoe stack traces interativos.
Impact: Em producao, expoe detalhes internos da aplicacao e permite execucao remota de codigo via debugger.
Recommendation: `DEBUG` deve vir de variavel de ambiente e ser `False` em producao.

### [LOW] Debug Artifacts in Production Code
File: controllers.py:8,57,106,161,179,182,208-210,219,248,250
Description: Multiplas declaracoes `print()` usadas como mecanismo de logging em producao: `print("Listando " + str(len(produtos)) + " produtos")`, `print("ENVIANDO EMAIL: ...")`, `print("ERRO CRITICO: ...")`, etc.
Impact: Saidas de debug poluem logs em producao sem nivel, timestamp ou contexto estruturado.
Recommendation: Substituir por logging estruturado com niveis adequados (info, warning, error).

### [LOW] Unused Imports / Dead Code
File: models.py:2
Description: `import sqlite3` na linha 2 — o modulo e importado mas nunca utilizado diretamente. Todas as operacoes usam `get_db()` que ja retorna uma conexao sqlite3.
Impact: Dependencia declarada mas nao utilizada. Causa confusao sobre dependencias reais.
Recommendation: Remover `import sqlite3` de models.py.

================================
Total: 24 findings
================================
