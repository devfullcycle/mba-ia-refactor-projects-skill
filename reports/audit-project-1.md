```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; local 3.14)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, usuários, pedidos, relatório de vendas)
Architecture:  Monolito com pseudo-camadas — models.py concentra SQL + regras de 4 domínios; app.py mistura rotas, SQL e config
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Entry point:   app.py — `python app.py` — porta 5000 (debug=True, host 0.0.0.0)
Endpoints:     19 routes mapped
================================
```

| Método | Path | Handler |
|---|---|---|
| GET | `/` | app.py:32 `index` |
| GET | `/produtos` | controllers.py:5 `listar_produtos` |
| GET | `/produtos/busca` | controllers.py:111 `buscar_produtos` |
| GET | `/produtos/<id>` | controllers.py:14 `buscar_produto` |
| POST | `/produtos` | controllers.py:24 `criar_produto` |
| PUT | `/produtos/<id>` | controllers.py:64 `atualizar_produto` |
| DELETE | `/produtos/<id>` | controllers.py:98 `deletar_produto` |
| GET | `/usuarios` | controllers.py:128 `listar_usuarios` |
| GET | `/usuarios/<id>` | controllers.py:136 `buscar_usuario` |
| POST | `/usuarios` | controllers.py:146 `criar_usuario` |
| POST | `/login` | controllers.py:167 `login` |
| POST | `/pedidos` | controllers.py:188 `criar_pedido` |
| GET | `/pedidos` | controllers.py:229 `listar_todos_pedidos` |
| GET | `/pedidos/usuario/<usuario_id>` | controllers.py:222 `listar_pedidos_usuario` |
| PUT | `/pedidos/<pedido_id>/status` | controllers.py:237 `atualizar_status_pedido` |
| GET | `/relatorios/vendas` | controllers.py:257 `relatorio_vendas` |
| GET | `/health` | controllers.py:264 `health_check` |
| POST | `/admin/reset-db` | app.py:47 `reset_database` |
| POST | `/admin/query` | app.py:59 `executar_query` |

````
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-11-03

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 3

## Findings

### F-01 [CRITICAL] God Class / God File (AP-03)
File: models.py:1-314, app.py:47-78, controllers.py:264-292
Evidence:
```python
def get_todos_produtos(): ...      # models.py:4
def login_usuario(email, senha): ...  # models.py:105
def relatorio_vendas(): ...        # models.py:235
```
Description: models.py contém SQL, regras de negócio (descontos, estoque), mapeamento e formatação de 4 domínios distintos (produtos, usuários, pedidos, relatórios). O entry point app.py também define rotas com SQL inline (reset/query) e o controller de health executa SQL direto.
Impact: Impossível testar em isolamento; qualquer mudança em um domínio arrisca quebrar os outros; viola SRP e a separação MVC.
Recommendation: Separar em models/controllers/views por domínio com composition root (PB-03, PB-09).

### F-02 [CRITICAL] SQL Injection (AP-01)
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Evidence:
```python
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```
Description: Todas as queries com parâmetros são montadas por concatenação de strings com dados do request (login, cadastro, busca com LIKE, update de status).
Impact: Bypass de login com `' OR '1'='1' --`, leitura/alteração/destruição de qualquer tabela.
Recommendation: Placeholders `?` com tupla de parâmetros em todas as queries; montagem dinâmica só de cláusulas fixas (PB-01).

### F-03 [CRITICAL] Credenciais / segredos hardcoded (AP-02)
File: app.py:7, controllers.py:289, database.py:76-78
Evidence:
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
Description: SECRET_KEY literal no código (e repetida no health check); usuários seed com senhas fixas e triviais (`admin123`).
Impact: Chave de assinatura de sessão conhecida por qualquer pessoa com acesso ao repositório; conta admin com senha pública.
Recommendation: Config via variáveis de ambiente com `.env.example`; seed com senhas hasheadas (PB-02, PB-06).

### F-04 [CRITICAL] Exposição de dados sensíveis (AP-04)
File: models.py:83, models.py:99, controllers.py:285-289
Evidence:
```python
"senha": row["senha"],
...
"secret_key": "minha-chave-super-secreta-123"
```
Description: GET /usuarios e GET /usuarios/<id> devolvem a senha de todos os usuários; GET /health devolve secret_key, flag de debug e caminho do banco.
Impact: Qualquer cliente anônimo obtém as credenciais de todos os usuários e a chave da aplicação.
Recommendation: Serialização explícita sem campos sensíveis; health retorna apenas status/contagens (PB-04).

### F-05 [CRITICAL] Endpoint administrativo sem autenticação (AP-05)
File: app.py:47-57, app.py:59-78
Evidence:
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    ...
    cursor.execute(query)
```
Description: POST /admin/reset-db apaga todas as tabelas e POST /admin/query executa SQL arbitrário enviado no body, ambos sem nenhuma autenticação.
Impact: Qualquer pessoa na rede destrói ou exfiltra todo o banco com uma requisição.
Recommendation: Guard por token administrativo vindo da config (desabilitado se não configurado); /admin/query restrito a um único SELECT em conexão somente leitura (PB-05).

### F-06 [CRITICAL] Armazenamento inseguro de senha (AP-06)
File: models.py:109-111, models.py:126-129, database.py:75-83
Evidence:
```python
"INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" +
nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"
```
Description: Senhas gravadas e comparadas em texto puro.
Impact: Vazamento do banco (ou do endpoint /usuarios) expõe as senhas reais, frequentemente reutilizadas em outros serviços.
Recommendation: `werkzeug.security.generate_password_hash/check_password_hash` + migração automática de senhas legadas em texto puro (PB-06).

### F-07 [HIGH] Regra de negócio e side-effects no Controller (AP-07)
File: controllers.py:24-62, controllers.py:188-220, controllers.py:237-255
Evidence:
```python
print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado para usuario " + str(usuario_id))
print("ENVIANDO SMS: Seu pedido foi recebido!")
```
Description: Controllers acumulam validação, regras de domínio (categorias válidas, status válidos) e disparo de notificações, além de lidar com HTTP (`request`, `jsonify`).
Impact: Regras não reutilizáveis nem testáveis sem o Flask; notificações acopladas ao fluxo HTTP.
Recommendation: Validators + controllers sem HTTP + NotificationService injetado (PB-07, PB-13).

### F-08 [HIGH] Estado global mutável (AP-08)
File: database.py:4-11
Evidence:
```python
db_connection = None
def get_db():
    global db_connection
    ...
    db_connection = sqlite3.connect(db_path, check_same_thread=False)
```
Description: Uma única conexão SQLite global compartilhada entre todas as threads/requests (com `check_same_thread=False`).
Impact: Condições de corrida, transações de requests diferentes misturadas (um commit de um request persiste escrita parcial de outro).
Recommendation: Conexão por request via `flask.g` + `teardown_appcontext` (PB-08).

### F-09 [HIGH] Acoplamento forte / sem Injeção de Dependência (AP-09)
File: controllers.py:1-3, controllers.py:266-274, app.py:3-4
Evidence:
```python
import models
from database import get_db
```
Description: Controllers importam módulos concretos e executam SQL diretamente; não existe composition root — dependências resolvidas por imports globais.
Impact: Impossível substituir banco/serviços em testes; mudança de persistência exige alterar controllers.
Recommendation: Composition root `create_app()` instanciando models → services → controllers com injeção via construtor (PB-09).

### F-10 [HIGH] Operação multi-etapa sem transação (AP-10)
File: models.py:133-169
Evidence:
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - " + ...)
db.commit()
```
Description: Criação de pedido grava pedido, itens e baixa de estoque sem transação explícita/rollback; o estoque é checado antes e decrementado depois sem garantia atômica.
Impact: Falha no meio deixa escrita parcial pendente na conexão global (persistida pelo próximo commit de qualquer request); pedidos concorrentes podem deixar estoque negativo.
Recommendation: Transação com rollback e decremento condicional `WHERE estoque >= ?` (PB-10).

### F-11 [HIGH] Debug ativo em produção (AP-12)
File: app.py:8, app.py:88
Evidence:
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```
Description: Debugger do Werkzeug ativo e servidor exposto em todas as interfaces.
Impact: O debugger interativo permite execução remota de código em caso de exceção.
Recommendation: DEBUG/HOST/PORT vindos da config com padrão seguro (PB-02).

### F-12 [MEDIUM] Queries N+1 (AP-13)
File: models.py:171-201, models.py:203-233, models.py:154-156, models.py:239-254
Evidence:
```python
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
Description: Listagem de pedidos executa 1 query por pedido + 1 por item; criação de pedido re-consulta o preço de cada produto; relatório faz 5 queries de agregação separadas.
Impact: Latência cresce linearmente com o volume (P pedidos × I itens queries).
Recommendation: JOIN único agrupado em memória; agregações com `SUM(CASE ...)` (PB-12).

### F-13 [MEDIUM] Validação de entrada ausente/inconsistente (AP-14)
File: controllers.py:43-46, controllers.py:72-90, controllers.py:113-121, controllers.py:169-170, controllers.py:195-201, controllers.py:239-240, models.py:275-283
Evidence:
```python
dados = request.get_json()
novo_status = dados.get("status", "")
```
Description: Body ausente gera `AttributeError` (500); tipos não validados (`"preco": "abc"` → TypeError 500); update de produto não valida nome/categoria como o create; itens de pedido aceitam quantidade negativa (aumenta estoque e gera total negativo); atualização de status não verifica se o pedido existe.
Impact: Erros 500 para entrada inválida, dados inconsistentes e fraude de estoque/valor.
Recommendation: Validators centralizados por entidade com `get_json(silent=True)` (PB-13).

### F-14 [MEDIUM] Tratamento de erros inadequado (AP-15)
File: controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220, controllers.py:226-227, controllers.py:234-235, controllers.py:254-255, controllers.py:261-262, controllers.py:291-292, app.py:77-78
Evidence:
```python
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```
Description: O mesmo try/except genérico é copiado em 17 handlers, devolvendo a mensagem interna da exceção ao cliente.
Impact: Vazamento de detalhes internos (SQL, paths); sem ponto único para logging/observabilidade.
Recommendation: Exceções de domínio + error handler centralizado (PB-14).

### F-15 [MEDIUM] Código duplicado (AP-16)
File: models.py:12-21, models.py:31-40, models.py:304-313, models.py:171-201, models.py:203-233, controllers.py:28-50, controllers.py:72-90
Evidence:
```python
result.append({
    "id": row["id"], "nome": row["nome"], "descricao": row["descricao"], ...
```
Description: Mapeamento row→dict de produto repetido 3x; `get_pedidos_usuario` e `get_todos_pedidos` são quase idênticas; validação de produto duplicada entre criar e atualizar.
Impact: Correções precisam ser replicadas; divergências já existem (update valida menos que create).
Recommendation: Funções únicas de serialização/consulta no Model e validator compartilhado (PB-15, PB-13).

### F-16 [LOW] Magic numbers / strings (AP-19)
File: models.py:256-262, controllers.py:47-52, controllers.py:242, app.py:88, controllers.py:285-286
Evidence:
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
```
Description: Faixas de desconto, limites de tamanho de nome, categorias e status válidos, porta e versão como literais soltos.
Impact: Regras de negócio escondidas e difíceis de alterar com segurança.
Recommendation: Constantes nomeadas no Model de cada domínio (PB-18).

### F-17 [LOW] Nomenclatura ruim / imports não usados (AP-20, AP-21)
File: models.py:2, database.py:2, models.py:187, models.py:191, controllers.py:14, controllers.py:56
Evidence:
```python
import sqlite3        # models.py — não usado
cursor2 = db.cursor()
id = models.criar_produto(...)
```
Description: Imports sem uso (`sqlite3`, `os`), cursores numerados e variáveis que sombreiam o builtin `id`.
Impact: Ruído e leitura mais difícil.
Recommendation: Remover imports mortos e renomear variáveis (PB-19).

### F-18 [LOW] Logging via print (AP-22)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250
Evidence:
```python
print("Login bem-sucedido: " + email)
```
Description: Eventos, erros e "notificações" registrados com `print`, incluindo e-mails de usuários.
Impact: Sem níveis, sem destino configurável; PII em stdout.
Recommendation: `logging` com logger por módulo configurado no composition root (PB-20).

## Deprecated APIs
None detected. Verificados: `datetime.utcnow`, `before_first_request`, `flask.json.JSONEncoder`, `send_file(attachment_filename=)`, `Query.get`, `hashlib.md5` — nenhum presente. Flask 3.1.1 e flask-cors 5.0.1 são versões atuais.

## Refactoring Plan (preview of Phase 3)
- Target structure: `app.py` (shim) + `src/{config,database,models,controllers,views,services,validators,middlewares,utils}` + `src/app.py` (composition root)
- F-01, F-09 → PB-03/PB-09: models por domínio (produto, usuario, pedido), controllers por recurso, Blueprints em views/
- F-02 → PB-01: todas as queries parametrizadas
- F-03, F-11 → PB-02: `src/config/settings.py` + `.env.example`
- F-04 → PB-04: serialização pública de usuário; health sem segredos
- F-05 → PB-05: `require_admin_token` + conexão read-only para /admin/query
- F-06 → PB-06: werkzeug hash + migração de senhas legadas no boot
- F-07, F-13, F-15 → PB-07/PB-13/PB-15: validators e NotificationService
- F-08, F-10 → PB-08/PB-10: conexão por request e transação no pedido
- F-12 → PB-12: JOINs e agregação única
- F-14 → PB-14: error handler central
- F-16..F-18 → PB-18/PB-19/PB-20
- Contract changes required for security: remover `senha` de /usuarios; remover `secret_key`/`debug`/`db_path` de /health; endpoints /admin/* exigem header `X-Admin-Token`.

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````
