```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.x
Framework:     Flask 3.1.1 (flask-cors)
Dependencies:  flask, flask-cors, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, usuários, pedidos, relatórios)
Architecture:  Monolítica — 4 arquivos, sem separação de camadas; SQL cru,
               regra de negócio e roteamento misturados
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~783 lines of code
Date:    2026-11-07

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] SQL Injection por concatenação de string (AP-03)
File: models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 148-166, 174, 188, 192, 280, 289-297
Description: Praticamente todas as queries são montadas concatenando input do
usuário diretamente na string SQL — ex.: `"SELECT * FROM produtos WHERE id = " + str(id)`
e `"...WHERE email = '" + email + "' AND senha = '" + senha + "'"`. A busca de
produtos concatena `termo`/`categoria` vindos da query string.
Impact: Leitura, alteração e destruição arbitrária do banco; bypass de login.
Recommendation: Queries 100% parametrizadas com placeholders `?` e tuplas de
parâmetros (playbook T-02).

### [CRITICAL] Credenciais hardcoded e segredo exposto na API (AP-02)
File: app.py:7; controllers.py:289
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` hardcoded no código;
pior, o endpoint `/health` devolve `secret_key` e `debug` no corpo da resposta.
Impact: Qualquer um que leia o repo ou chame `/health` obtém a chave da aplicação.
Recommendation: Mover para variável de ambiente (`.env` + `.env.example`) e
nunca serializar segredos em respostas (T-01, T-05).

### [CRITICAL] Senhas em texto puro e expostas em respostas (AP-04)
File: database.py:76-78; models.py:83, 99, 110; controllers.py:132
Description: Senhas são gravadas em texto puro no seed e comparadas cruas no
login (`WHERE ... senha = '...'`). `get_todos_usuarios` e `get_usuario_por_id`
incluem o campo `senha`, que vaza em `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Vazamento direto de credenciais de todos os usuários.
Recommendation: Hash forte (`werkzeug.security`/bcrypt) e remover `senha` da
serialização (T-05).

### [CRITICAL] Endpoints administrativos perigosos sem proteção (AP-12)
File: app.py:47-57 (`/admin/reset-db`), app.py:59-78 (`/admin/query`)
Description: `/admin/reset-db` apaga todas as tabelas sem autenticação;
`/admin/query` executa SQL arbitrário recebido no corpo da requisição.
Impact: Destruição total e execução arbitrária de SQL por qualquer cliente.
Recommendation: Remover `/admin/query`; proteger operações admin com
autenticação/role; isolar reset atrás de flag de ambiente (T-12).

### [CRITICAL] God File — models.py concentra tudo (AP-01)
File: models.py:1-315; controllers.py:1-293
Description: `models.py` reúne acesso a dados, regra de negócio (cálculo de
total de pedido, relatório de vendas com desconto), montagem de resposta e SQL
cru para 4 domínios. `controllers.py` acumula validação, serialização e
efeitos colaterais.
Impact: Impossível testar em isolamento; qualquer mudança afeta todos os domínios.
Recommendation: Separar em `models/` por entidade + `services/`/`controllers/`
por domínio (T-03, T-04).

### [HIGH] Regra de negócio e efeitos colaterais no controller (AP-05)
File: controllers.py:208-210, 247-250; models.py:133-169, 235-273
Description: Criação de pedido calcula total, verifica estoque e cria itens no
model, e o controller dispara "e-mail/SMS/push" via `print`. O relatório de
vendas calcula faixas de desconto dentro do model de dados.
Impact: Lógica não reutilizável nem testável sem HTTP; responsabilidades misturadas.
Recommendation: Extrair para `PedidoService`/`RelatorioService` com notifier
injetado (T-04).

### [HIGH] Estado global mutável de conexão (AP-06)
File: database.py:4-11
Description: `db_connection = None` em escopo de módulo é reutilizado entre
todas as requisições via `get_db()` com `check_same_thread=False`.
Impact: Condições de corrida e acoplamento global; difícil de testar/trocar.
Recommendation: Factory de conexão + injeção de dependência no composition root (T-06).

### [HIGH] Ausência de injeção de dependência / acoplamento forte (AP-07)
File: controllers.py:2-3; models.py:1
Description: Controllers importam `models` e `database` diretamente; models
chamam `get_db()` global. Não há como mockar o banco para teste.
Impact: Baixa testabilidade e rigidez arquitetural.
Recommendation: Injetar models/serviços nos controllers e a conexão nos models (T-06).

### [HIGH] DEBUG habilitado em produção (AP-17)
File: app.py:8, 88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)`.
Impact: Execução remota de código via debugger do Werkzeug e stack traces expostos.
Recommendation: Controlar via env (`FLASK_DEBUG`), default desligado (T-01).

### [MEDIUM] Queries N+1 na listagem de pedidos (AP-09)
File: models.py:187-199, 219-231
Description: Para cada pedido, uma query de itens; para cada item, uma query do
nome do produto. Cresce linearmente com o volume.
Impact: Degradação de performance com muitos pedidos/itens.
Recommendation: Substituir por um único JOIN e agrupar em memória (T-08).

### [MEDIUM] Validação e serialização duplicadas (AP-10, AP-11)
File: controllers.py:28-54 vs 72-90; models.py:12-21, 31-40, 304-313
Description: Validações de produto repetidas em `criar_produto`/`atualizar_produto`;
o mesmo dicionário de produto é montado em três funções de `models.py`.
Impact: Divergência silenciosa quando uma cópia muda.
Recommendation: Validador central e serializer único por entidade (T-09, T-10).

### [MEDIUM] Error handling genérico que vaza detalhes (AP-14)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 125-126, 143-144, 164-165, 185-186, 218-220
Description: Quase todo handler tem `except Exception as e: return jsonify({"erro": str(e)}), 500`,
devolvendo a mensagem interna ao cliente.
Impact: Vazamento de detalhes internos e código repetido em todo lugar.
Recommendation: Error handler centralizado em middleware (T-11).

### [LOW] Prints de debug no fluxo de produção (AP-15)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: `print(...)` usado como log (inclusive "ENVIANDO EMAIL/SMS/PUSH").
Impact: Ruído e ausência de controle de nível de log.
Recommendation: Logger configurável; notificações em serviço dedicado (T-14).

### [LOW] Magic numbers no cálculo de desconto (AP-16)
File: models.py:256-262
Description: Faixas `10000`/`5000`/`1000` e percentuais `0.1`/`0.05`/`0.02`
soltos na lógica de relatório.
Impact: Intenção obscura; alteração arriscada.
Recommendation: Extrair para constantes nomeadas em config (T-14).

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
