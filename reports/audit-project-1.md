# Audit Report — Project 1: code-smells-project

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuarios)
Architecture:  Monolitica — toda logica em 4 arquivos, sem separacao de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~794 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] SQL Injection
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155-166, 174, 188-224, 280-281, 291-297
Description: Todas as queries SQL sao construidas com concatenacao de strings. Exemplo: `"SELECT * FROM produtos WHERE id = " + str(id)`. O endpoint de login em models.py:109-111 e especialmente critico, pois permite bypass de autenticacao via SQL injection.
Impact: Atacantes podem ler, modificar ou deletar qualquer dado do banco. O endpoint de login pode ser completamente bypassed com `' OR '1'='1`.
Recommendation: Usar queries parametrizadas em todas as operacoes: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`

### [CRITICAL] Hardcoded Credentials
File: app.py:7-8, database.py:76-84, controllers.py:287-289
Description: SECRET_KEY hardcoded como `'minha-chave-super-secreta-123'` em app.py:7. Debug mode habilitado em app.py:8. Credenciais de seed com senhas fracas como `'admin123'` em database.py:76-84. Health endpoint expoe secret_key, debug mode e db_path em controllers.py:287-289.
Impact: Credenciais expostas no controle de versao. Qualquer pessoa com acesso ao repositorio tem acesso total ao sistema.
Recommendation: Extrair todas as configuracoes para variaveis de ambiente usando `os.environ.get()` e `python-dotenv`. Remover dados sensiveis do endpoint de health.

### [CRITICAL] Insecure Password Storage
File: models.py:105-120
Description: Senhas armazenadas em texto plano no banco de dados. Comparacao direta de strings para autenticacao: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`.
Impact: Se o banco for comprometido, todas as senhas dos usuarios sao imediatamente expostas. Combinado com SQL injection, o risco e catastrofico.
Recommendation: Usar `werkzeug.security.generate_password_hash()` para hash e `check_password_hash()` para verificacao.

### [CRITICAL] Arbitrary SQL Execution Endpoint
File: app.py:59-78
Description: Endpoint `/admin/query` aceita e executa qualquer query SQL fornecida pelo usuario via POST request, sem autenticacao ou autorizacao.
Impact: Qualquer pessoa pode executar DROP TABLE, SELECT de dados sensiveis, ou qualquer operacao destrutiva no banco de dados.
Recommendation: Remover este endpoint completamente ou, se necessario para admin, proteger com autenticacao forte e limitar operacoes permitidas.

### [HIGH] God Class / God File
File: models.py:1-314
Description: Arquivo unico contem toda logica de acesso a dados para 4 dominios diferentes (produtos, usuarios, pedidos, relatorios) com 314 linhas. Mistura queries SQL, logica de negocio, validacao e transformacao de dados.
Impact: Impossivel testar componentes em isolamento. Qualquer mudanca em um dominio pode afetar outros.
Recommendation: Separar em modulos por dominio: `product_model.py`, `user_model.py`, `order_model.py`.

### [HIGH] Missing Authentication on Admin Endpoints
File: app.py:47-57, app.py:59-78
Description: Endpoints `/admin/reset-db` e `/admin/query` sao publicamente acessiveis sem qualquer autenticacao ou autorizacao.
Impact: Qualquer usuario pode resetar o banco de dados inteiro ou executar queries arbitrarias.
Recommendation: Adicionar middleware de autenticacao e verificacao de role de admin em todos os endpoints administrativos.

### [HIGH] No Transaction Management
File: models.py:133-169
Description: Funcao `criar_pedido()` executa multiplas operacoes de banco (insert pedido, insert itens, update estoque) sem transacao. Se uma operacao falhar no meio, dados parciais ficam persistidos.
Impact: Inconsistencia de dados — pedido criado sem itens, ou estoque reduzido sem pedido correspondente.
Recommendation: Envolver operacoes multiplas em transacoes com commit/rollback.

### [MEDIUM] N+1 Query Problem
File: models.py:187-200, models.py:219-231
Description: Para cada pedido, queries separadas sao executadas para buscar itens (cursor2) e nomes de produtos (cursor3), criando loops de queries aninhados.
Impact: Performance degrada linearmente. 100 pedidos = 300+ queries ao inves de 2-3 JOINs.
Recommendation: Usar queries JOIN: `SELECT p.*, i.* FROM pedidos p LEFT JOIN itens_pedido i ON p.id = i.pedido_id`.

### [MEDIUM] Code Duplication
File: controllers.py:30-35, controllers.py:74-79
Description: Logica de validacao de produto (nome, preco, estoque) duplicada entre `criar_produto()` e `atualizar_produto()`.
Impact: Correcoes de bug precisam ser aplicadas em multiplos lugares. Risco de comportamento inconsistente.
Recommendation: Extrair validacao para metodo compartilhado no controller.

### [MEDIUM] Print-based Logging
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250
Description: Uso de `print()` para logging em todo o codigo ao inves de framework de logging adequado.
Impact: Sem niveis de log, sem formatacao, sem rotacao de arquivos. Impossivel filtrar logs em producao.
Recommendation: Substituir por `logging.getLogger(__name__)` com niveis INFO, WARNING, ERROR.

### [MEDIUM] Deprecated API Usage
File: models.py (multiple locations)
Description: Uso de `jsonify()` para retornar respostas JSON quando Flask >= 2.2 permite retornar dicts diretamente. Tambem, padrao de conexao global com SQLite usando `check_same_thread=False` e considerado inseguro.
Impact: Uso de APIs obsoletas dificulta manutencao e pode causar problemas em atualizacoes futuras.
Recommendation: Retornar dicts diretamente nos endpoints (Flask >= 2.2). Usar connection pool adequado.

### [LOW] Missing Database Constraints
File: database.py:8-40
Description: Schema do banco nao define FOREIGN KEY, UNIQUE, NOT NULL ou CHECK constraints. Email de usuario nao e unico. Precos podem ser negativos.
Impact: Dados invalidos podem ser inseridos. Registros orfaos possiveis.
Recommendation: Adicionar constraints: `UNIQUE(email)`, `CHECK(preco >= 0)`, `FOREIGN KEY`.

### [LOW] No Pagination
File: models.py:7-22, models.py:75-87
Description: Endpoints de listagem retornam todos os registros sem LIMIT/OFFSET. `get_all_produtos()` e `get_todos_pedidos()` carregam tudo na memoria.
Impact: Performance degrada com crescimento dos dados. Pode causar out-of-memory em datasets grandes.
Recommendation: Adicionar parametros `page` e `limit` com defaults sensiveis (ex: 20 por pagina).

### [LOW] Magic Numbers and Hardcoded Values
File: app.py:88, database.py:5, controllers.py:242
Description: Porta 5000 e host `0.0.0.0` hardcoded em app.py:88. Path do banco `loja.db` hardcoded em database.py:5. Lista de status validos hardcoded em controllers.py:242.
Impact: Dificil alterar configuracao entre ambientes (dev/staging/prod).
Recommendation: Extrair para modulo de configuracao com valores de variaveis de ambiente.

================================
Total: 14 findings
================================
```
