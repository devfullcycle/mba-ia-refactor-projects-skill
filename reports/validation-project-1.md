================================
VALIDATION EVIDENCE — code-smells-project
================================
Date:  2026-07-13
Stack: Python + Flask 3.1.1
Port:  5055

## Boot
$ .venv/bin/python -c "import flask, flask_cors, werkzeug; print('deps ok', flask.__version__)"   # deps já instaladas no .venv
$ ADMIN_TOKEN=segredo-teste PORT=5055 .venv/bin/python app.py
[log] ==================================================
[log] SERVIDOR INICIADO
[log] Rodando em http://localhost:5055
[log]  * Serving Flask app 'app'
[log]  * Debug mode: off
[log]  * Running on http://127.0.0.1:5055
[log] Press CTRL+C to quit
Boot: ✓ OK (sem stack trace; debug off)

## Endpoints
| Método | Path                              | Payload                                  | Status | Esperado | OK |
|--------|-----------------------------------|------------------------------------------|--------|----------|----|
| GET    | /                                 | —                                        | 200    | 200      | ✓  |
| GET    | /health                           | —                                        | 200    | 200      | ✓  |
| GET    | /produtos                         | —                                        | 200    | 200      | ✓  |
| GET    | /produtos/1                       | —                                        | 200    | 200      | ✓  |
| GET    | /produtos/busca?q=SSD&preco_min=100 | —                                      | 200    | 200      | ✓  |
| POST   | /produtos                         | {nome,preco,estoque,categoria}           | 201    | 201      | ✓  |
| PUT    | /produtos/11                      | {nome,preco,estoque,categoria}           | 200    | 200      | ✓  |
| DELETE | /produtos/11                      | —                                        | 200    | 200      | ✓  |
| GET    | /usuarios                         | —                                        | 200    | 200      | ✓  |
| GET    | /usuarios/1                       | —                                        | 200    | 200      | ✓  |
| POST   | /usuarios                         | {nome,email,senha}                       | 201    | 201      | ✓  |
| POST   | /login                            | {email:admin@loja.com,senha:admin123}    | 200    | 200      | ✓  |
| POST   | /login (injeção SQL clássica)     | {email:"... OR '1'='1", senha:"..."}     | 401    | 401      | ✓  |
| POST   | /pedidos                          | {usuario_id,itens[]}                      | 201    | 201      | ✓  |
| GET    | /pedidos                          | —                                        | 200    | 200      | ✓  |
| GET    | /pedidos/usuario/2                | —                                        | 200    | 200      | ✓  |
| PUT    | /pedidos/1/status                 | {status:aprovado}                        | 200    | 200      | ✓  |
| GET    | /relatorios/vendas                | —                                        | 200    | 200      | ✓  |
| GET    | /produtos/0 OR 1=1 (probe SQLi)   | —                                        | 404    | 404      | ✓  |
| POST   | /admin/query (removido)           | {sql:"SELECT * FROM usuarios"}           | 404    | 404      | ✓  |
| POST   | /admin/reset-db (sem token)       | —                                        | 403    | 403      | ✓  |
| POST   | /admin/reset-db (com token)       | header X-Admin-Token                     | 200    | 200      | ✓  |

## Amostras de resposta (trechos reais)
- GET /health   → 200 : {"ambiente":"producao","counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","db_path":"loja.db","status":"ok","versao":"1.0.0"}  (sem secret_key/debug)
- GET /usuarios → 200 : [{"criado_em":"...","email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"}, ...]  (campo "senha" não é mais exposto)
- POST /login   → 200 : {"dados":{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},"mensagem":"Login OK","sucesso":true}  (verificação por hash)
- POST /login (SQLi) → 401 : {"erro":"Email ou senha inválidos","sucesso":false}  (bypass antigo neutralizado)
- POST /pedidos → 201 : {"dados":{"pedido_id":1,"total":479.7},"mensagem":"Pedido criado com sucesso","sucesso":true}
- GET /pedidos  → 200 : itens com produto_nome resolvido via JOIN (sem N+1)
- POST /admin/reset-db sem token → 403 : {"erro":"Não autorizado"}

================================
RESULT: PASS (22/22 endpoints)
================================
