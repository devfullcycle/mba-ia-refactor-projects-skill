================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3 + Flask 3.1.1
Files:   5 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] SQL Injection / Query por concatenação de string (AP-01)
File: models.py:28, 48-50, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155-156, 159-161, 164-166, 174, 188, 192, 220, 224, 280, 291, 293, 295, 297
Description: Todas as funções de acesso a dados em `models.py` montam SQL concatenando strings com entrada vinda diretamente do request (`get_produto_por_id`, `criar_produto`, `atualizar_produto`, `deletar_produto`, `get_usuario_por_id`, `login_usuario`, `criar_usuario`, `criar_pedido`, `get_pedidos_usuario`, `atualizar_status_pedido`, `buscar_produtos`). Nenhuma usa placeholders parametrizados apesar do driver `sqlite3` suportá-los nativamente.
Impact: Qualquer parâmetro de rota, query string ou corpo de request pode injetar SQL arbitrário (leitura, alteração ou exclusão de dados, bypass de autenticação em `login_usuario`).
Recommendation: Reescrever todas as queries com placeholders `?` do `sqlite3` (ex.: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`).

### [CRITICAL] Credenciais / segredos hardcoded e vazados em resposta HTTP (AP-02)
File: app.py:7; controllers.py:285-289
Description: `SECRET_KEY` fixa (`"minha-chave-super-secreta-123"`) definida em `app.py:7` e devolvida literalmente no corpo JSON do endpoint `/health` (`controllers.py:289`), junto com `debug: True`.
Impact: Qualquer cliente que chame `/health` obtém a secret key da aplicação, permitindo forjar sessões/tokens assinados com ela.
Recommendation: Mover `SECRET_KEY` para variável de ambiente (`os.environ.get("SECRET_KEY")`) com default seguro só em dev; remover segredos e flags de debug do payload de `/health`.

### [CRITICAL] Senha em texto plano, sem hash, e exposta em respostas (AP-03)
File: models.py:72-103, 105-120, 122-131
Description: `criar_usuario` grava a senha recebida sem qualquer hash (122-131); `login_usuario` compara senha em texto plano via SQL (105-120); `get_todos_usuarios`/`get_usuario_por_id` (72-103) incluem o campo `senha` no dicionário retornado, exposto por `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Vazamento de senhas de todos os usuários em texto plano via API pública; comprometimento total de contas em caso de qualquer leitura não autorizada.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já disponível via Flask) para armazenar e validar senhas; remover o campo `senha` de qualquer serialização de resposta.

### [CRITICAL] Endpoint que executa SQL arbitrário sem autenticação (AP-04)
File: app.py:59-78
Description: `/admin/query` (POST) recebe uma string SQL livre no corpo (`dados.get("sql")`) e executa via `cursor.execute(query)` sem nenhuma autenticação, autorização ou allowlist.
Impact: Execução remota de SQL arbitrário — leitura, alteração ou destruição completa do banco por qualquer chamador não autenticado.
Recommendation: Remover o endpoint. Se uma ferramenta admin for necessária, restringir a operações pré-definidas, com autenticação forte e allowlist de comandos.

### [CRITICAL] Endpoint destrutivo sem autenticação (AP-04)
File: app.py:47-57
Description: `/admin/reset-db` (POST) apaga todos os registros de `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem qualquer verificação de identidade ou confirmação.
Impact: Qualquer chamador não autenticado pode zerar o banco de produção em uma requisição.
Recommendation: Remover em produção ou proteger com autenticação + autorização de admin e confirmação explícita.

### [HIGH] Estado global mutável para conexão de banco (AP-07)
File: database.py:4, 8-11
Description: `db_connection` é uma variável de módulo global, inicializada uma única vez (`sqlite3.connect(..., check_same_thread=False)`) e reutilizada como singleton mutável entre todas as requisições.
Impact: Acesso concorrente à mesma conexão sem isolamento por requisição, condição de corrida em cenários multi-thread e dificuldade de testar em isolamento.
Recommendation: Abrir conexão por requisição (`before_request`/`teardown_request` do Flask) ou usar um pool; evitar estado de módulo mutável. API relacionada obsoleta: `sqlite3.connect(check_same_thread=False)` como singleton global → usar conexão por requisição/pool (severidade típica HIGH conforme catálogo de APIs deprecated).

### [HIGH] Acoplamento forte / ausência de injeção de dependência (AP-10)
File: controllers.py:1-3, 266; models.py:1
Description: `controllers.py` importa e chama `models` e `get_db()` diretamente (linha 3, e novamente em `health_check` na linha 266); `models.py` importa `get_db` diretamente de `database`. Nenhuma camada recebe suas dependências por parâmetro/injeção.
Impact: Impossível testar controllers ou models isoladamente (sem banco real ou mock injetável); qualquer troca de implementação de acesso a dados exige editar múltiplos arquivos.
Recommendation: Injetar a conexão/repositório como parâmetro ou via padrão de fábrica/DI, permitindo substituição em testes.

### [HIGH] Lógica de negócio e efeitos colaterais no controller (AP-06)
File: controllers.py:208-210, 247-250
Description: `criar_pedido` simula envio de e-mail/SMS/push diretamente no controller (208-210); `atualizar_status_pedido` decide, com `if` embutido, notificações de negócio conforme o novo status (247-250). Essas regras deveriam estar numa camada de serviço/notificação, não no controller HTTP.
Impact: Regras de negócio de notificação ficam espalhadas e difíceis de testar/reaproveitar fora do contexto HTTP.
Recommendation: Extrair para um serviço de notificação dedicado, chamado pelo controller ou pelo model após a operação.

### [MEDIUM] Query N+1 (AP-11)
File: models.py:139-146, 187-199, 219-231
Description: `criar_pedido` executa uma query de produto por item do pedido dentro de um loop (139-146); `get_pedidos_usuario` (187-199) e `get_todos_pedidos` (219-231) abrem cursores adicionais por pedido e por item, em vez de usar `JOIN`.
Impact: Número de queries cresce linearmente com o número de itens/pedidos, degradando performance conforme o volume de dados cresce.
Recommendation: Substituir por `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, ou por uma query única com `IN (...)`.

### [MEDIUM] Validação duplicada entre create/update (AP-12)
File: controllers.py:24-54, 64-92
Description: `criar_produto` e `atualizar_produto` repetem o mesmo bloco de validação (campos obrigatórios, preço/estoque negativos) quase palavra por palavra.
Impact: Qualquer mudança de regra de validação precisa ser replicada manualmente nos dois lugares, com risco de divergência.
Recommendation: Extrair a validação para uma função/schema único (ex.: `validar_produto(dados, parcial=False)`) reutilizado por ambos os endpoints.

### [MEDIUM] Configuração/middleware inadequados para produção (AP-14)
File: app.py:8-9, 88
Description: `CORS(app)` libera todas as origens sem restrição (linha 9); `app.config["DEBUG"] = True` e `app.run(..., debug=True)` (linhas 8 e 88) ficam fixos no código, não condicionados a ambiente.
Impact: CORS aberto expõe a API a qualquer origem; debug ligado em produção habilita o debugger interativo do Werkzeug (execução de código arbitrário se exposto publicamente).
Recommendation: Configurar CORS com origens explícitas por ambiente; ler `debug`/`DEBUG` de variável de ambiente com default `False`.

### [MEDIUM] Código duplicado na montagem de pedidos (AP-13)
File: models.py:171-201, 203-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` duplicam quase integralmente a lógica de montar o dicionário de pedido e buscar seus itens/produtos.
Impact: Manutenção dobrada e risco de as duas versões divergirem com o tempo.
Recommendation: Extrair uma função privada comum (ex.: `_montar_pedidos(rows)`) reutilizada pelos dois métodos.

### [LOW] Logging por print (AP-15)
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Toda a aplicação usa `print(...)` para logs de eventos, erros e "notificações", sem nível, timestamp ou estrutura.
Impact: Impossível filtrar por severidade, correlacionar logs ou integrar com ferramentas de observabilidade.
Recommendation: Adotar o módulo `logging` do Python com níveis apropriados (`INFO`, `ERROR`).

### [LOW] Magic numbers e listas de valores hardcoded (AP-16)
File: controllers.py:52, 242; models.py:257-262
Description: Lista de categorias válidas hardcoded inline (controllers.py:52), lista de status válidos hardcoded inline (controllers.py:242), faixas de desconto e percentuais fixos no código (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02` em models.py:257-262).
Impact: Regras de negócio ficam escondidas em meio ao código, difíceis de localizar e alterar com segurança.
Recommendation: Extrair para constantes nomeadas ou configuração (ex.: `CATEGORIAS_VALIDAS`, `FAIXAS_DESCONTO`).

### [LOW] Tratamento de exceção genérico (AP-19)
File: controllers.py:10, 21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291
Description: Todas as funções do controller usam `except Exception as e` genérico, retornando `str(e)` diretamente ao cliente.
Impact: Detalhes internos (mensagens de erro do banco, stack) podem vazar ao cliente; erros distintos (validação, banco, negócio) são tratados de forma indistinta.
Recommendation: Capturar exceções específicas, logar detalhes internamente e devolver mensagens de erro padronizadas ao cliente.

### [LOW] Import não utilizado (AP-18)
File: models.py:2
Description: `import sqlite3` é declarado em `models.py` mas nunca usado — todo acesso ao driver passa por `get_db()` de `database.py`.
Impact: Ruído no código, sugere dependência que não existe de fato.
Recommendation: Remover o import não utilizado.

================================
Total: 16 findings
================================
