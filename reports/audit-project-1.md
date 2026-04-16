# Audit Report — Project 1: code-smells-project

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — toda lógica em 4 arquivos, sem separação de camadas
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
Description: Todas as queries SQL são construídas com concatenação de strings. Exemplo: `"SELECT * FROM produtos WHERE id = " + str(id)`. O endpoint de login em models.py:109-111 é especialmente crítico, pois permite bypass de autenticação via SQL injection.
Impact: Atacantes podem ler, modificar ou deletar qualquer dado do banco. O endpoint de login pode ser completamente bypassed com `' OR '1'='1`.
Recommendation: Usar queries parametrizadas em todas as operações: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`

### [CRITICAL] Hardcoded Credentials
File: app.py:7-8, database.py:76-84, controllers.py:287-289
Description: SECRET_KEY hardcoded como `'minha-chave-super-secreta-123'` em app.py:7. Debug mode habilitado em app.py:8. Credenciais de seed com senhas fracas como `'admin123'` em database.py:76-84. Health endpoint expõe secret_key, debug mode e db_path em controllers.py:287-289.
Impact: Credenciais expostas no controle de versão. Qualquer pessoa com acesso ao repositório tem acesso total ao sistema.
Recommendation: Extrair todas as configurações para variáveis de ambiente usando `os.environ.get()` e `python-dotenv`. Remover dados sensíveis do endpoint de health.

### [CRITICAL] Insecure Password Storage
File: models.py:105-120
Description: Senhas armazenadas em texto plano no banco de dados. Comparação direta de strings para autenticação: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`.
Impact: Se o banco for comprometido, todas as senhas dos usuários são imediatamente expostas. Combinado com SQL injection, o risco é catastrófico.
Recommendation: Usar `werkzeug.security.generate_password_hash()` para hash e `check_password_hash()` para verificação.

### [CRITICAL] Arbitrary SQL Execution Endpoint
File: app.py:59-78
Description: Endpoint `/admin/query` aceita e executa qualquer query SQL fornecida pelo usuário via POST request, sem autenticação ou autorização.
Impact: Qualquer pessoa pode executar DROP TABLE, SELECT de dados sensíveis, ou qualquer operação destrutiva no banco de dados.
Recommendation: Remover este endpoint completamente ou, se necessário para admin, proteger com autenticação forte e limitar operações permitidas.

### [HIGH] God Class / God File
File: models.py:1-314
Description: Arquivo único contém toda lógica de acesso a dados para 4 domínios diferentes (produtos, usuários, pedidos, relatórios) com 314 linhas. Mistura queries SQL, lógica de negócio, validação e transformação de dados.
Impact: Impossível testar componentes em isolamento. Qualquer mudança em um domínio pode afetar outros.
Recommendation: Separar em módulos por domínio: `product_model.py`, `user_model.py`, `order_model.py`.

### [HIGH] Missing Authentication on Admin Endpoints
File: app.py:47-57, app.py:59-78
Description: Endpoints `/admin/reset-db` e `/admin/query` são publicamente acessíveis sem qualquer autenticação ou autorização.
Impact: Qualquer usuário pode resetar o banco de dados inteiro ou executar queries arbitrárias.
Recommendation: Adicionar middleware de autenticação e verificação de role de admin em todos os endpoints administrativos.

### [HIGH] No Transaction Management
File: models.py:133-169
Description: Função `criar_pedido()` executa múltiplas operações de banco (insert pedido, insert itens, update estoque) sem transação. Se uma operação falhar no meio, dados parciais ficam persistidos.
Impact: Inconsistência de dados — pedido criado sem itens, ou estoque reduzido sem pedido correspondente.
Recommendation: Envolver operações múltiplas em transações com commit/rollback.

### [MEDIUM] N+1 Query Problem
File: models.py:187-200, models.py:219-231
Description: Para cada pedido, queries separadas são executadas para buscar itens (cursor2) e nomes de produtos (cursor3), criando loops de queries aninhados.
Impact: Performance degrada linearmente. 100 pedidos = 300+ queries ao invés de 2-3 JOINs.
Recommendation: Usar queries JOIN: `SELECT p.*, i.* FROM pedidos p LEFT JOIN itens_pedido i ON p.id = i.pedido_id`.

### [MEDIUM] Code Duplication
File: controllers.py:30-35, controllers.py:74-79
Description: Lógica de validação de produto (nome, preço, estoque) duplicada entre `criar_produto()` e `atualizar_produto()`.
Impact: Correções de bug precisam ser aplicadas em múltiplos lugares. Risco de comportamento inconsistente.
Recommendation: Extrair validação para método compartilhado no controller.

### [MEDIUM] Print-based Logging
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250
Description: Uso de `print()` para logging em todo o código ao invés de framework de logging adequado.
Impact: Sem níveis de log, sem formatação, sem rotação de arquivos. Impossível filtrar logs em produção.
Recommendation: Substituir por `logging.getLogger(__name__)` com níveis INFO, WARNING, ERROR.

### [MEDIUM] Deprecated API Usage
File: models.py (multiple locations)
Description: Uso de `jsonify()` para retornar respostas JSON quando Flask >= 2.2 permite retornar dicts diretamente. Também, padrão de conexão global com SQLite usando `check_same_thread=False` é considerado inseguro.
Impact: Uso de APIs obsoletas dificulta manutenção e pode causar problemas em atualizações futuras.
Recommendation: Retornar dicts diretamente nos endpoints (Flask >= 2.2). Usar connection pool adequado.

### [LOW] Missing Database Constraints
File: database.py:8-40
Description: Schema do banco não define FOREIGN KEY, UNIQUE, NOT NULL ou CHECK constraints. Email de usuário não é único. Preços podem ser negativos.
Impact: Dados inválidos podem ser inseridos. Registros órfãos possíveis.
Recommendation: Adicionar constraints: `UNIQUE(email)`, `CHECK(preco >= 0)`, `FOREIGN KEY`.

### [LOW] No Pagination
File: models.py:7-22, models.py:75-87
Description: Endpoints de listagem retornam todos os registros sem LIMIT/OFFSET. `get_all_produtos()` e `get_todos_pedidos()` carregam tudo na memória.
Impact: Performance degrada com crescimento dos dados. Pode causar out-of-memory em datasets grandes.
Recommendation: Adicionar parâmetros `page` e `limit` com defaults sensíveis (ex: 20 por página).

### [LOW] Magic Numbers and Hardcoded Values
File: app.py:88, database.py:5, controllers.py:242
Description: Porta 5000 e host `0.0.0.0` hardcoded em app.py:88. Path do banco `loja.db` hardcoded em database.py:5. Lista de status válidos hardcoded em controllers.py:242.
Impact: Difícil alterar configuração entre ambientes (dev/staging/prod).
Recommendation: Extrair para módulo de configuração com valores de variáveis de ambiente.

================================
Total: 14 findings
================================
```
