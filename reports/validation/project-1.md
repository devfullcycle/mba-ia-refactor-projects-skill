# Validação pós-refatoração — Projeto 1 (code-smells-project)

Gerado com um smoke test HTTP independente (fora da skill): a mesma lista de requisições foi enviada à aplicação **original** (baseline) e à **refatorada**, sobre um banco recém-criado.

## Boot da aplicação refatorada

```
$ ADMIN_TOKEN=*** python app.py
2026-11-19 20:02:34,413 WARNING src.config.settings: SECRET_KEY não definida; usando chave aleatória efêmera
2026-11-19 20:02:34,637 INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Serving Flask app 'src.app'
 * Debug mode: off
2026-11-19 20:02:34,642 INFO werkzeug: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
2026-11-19 20:02:34,642 INFO werkzeug: Press CTRL+C to quit
2026-11-19 20:02:34,918 INFO src.controllers.produto_controller: Produto criado id=11
2026-11-19 20:02:34,923 INFO src.controllers.produto_controller: Produto criado id=12
2026-11-19 20:02:34,928 INFO src.controllers.produto_controller: Produto deletado id=11
2026-11-19 20:02:35,000 INFO src.controllers.usuario_controller: Usuário criado id=4
2026-11-19 20:02:35,070 INFO src.controllers.usuario_controller: Login bem-sucedido usuario_id=1
```

## Comparação antes × depois

| # | Request | Antes | Depois | Resultado |
|---|---|---|---|---|
| 1 | `GET /` — index | 200 | 200 | ✅ igual |
| 2 | `GET /health` — health | 200 | 200 | ✅ status igual; não expõe mais `secret_key`, `db_path`, `debug` |
| 3 | `GET /produtos` — list produtos | 200 | 200 | ✅ igual |
| 4 | `GET /produtos/1` — get produto | 200 | 200 | ✅ igual |
| 5 | `GET /produtos/999` — get produto 404 | 404 | 404 | ✅ igual |
| 6 | `GET /produtos/busca` — busca termo | 200 | 200 | ✅ igual |
| 7 | `GET /produtos/busca` — busca filtros | 200 | 200 | ✅ igual |
| 8 | `GET /produtos/busca` — busca sqli probe | 200 | 200 | ✅ igual (injeção neutralizada (0 resultados em vez de todos)) |
| 9 | `POST /produtos` — criar produto | 201 | 201 | ✅ igual |
| 10 | `POST /produtos` — criar produto sem nome | 400 | 400 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 11 | `POST /produtos` — criar produto cat invalida | 400 | 400 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 12 | `POST /produtos` — criar produto com aspas | 500 | 201 | 🔒 `D'Agua` criado (antes: 500 syntax error) |
| 13 | `PUT /produtos/11` — atualizar produto | 200 | 200 | ✅ igual |
| 14 | `PUT /produtos/999` — atualizar produto 404 | 404 | 404 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 15 | `DELETE /produtos/11` — deletar produto | 200 | 200 | ✅ igual |
| 16 | `DELETE /produtos/11` — deletar produto 404 | 404 | 404 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 17 | `GET /usuarios` — list usuarios | 200 | 200 | ✅ igual (campo `senha` removido) |
| 18 | `GET /usuarios/1` — get usuario | 200 | 200 | ✅ igual (campo `senha` removido) |
| 19 | `GET /usuarios/999` — get usuario 404 | 404 | 404 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 20 | `POST /usuarios` — criar usuario | 201 | 201 | ✅ igual |
| 21 | `POST /usuarios` — criar usuario invalido | 400 | 400 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 22 | `POST /login` — login ok | 200 | 200 | ✅ igual |
| 23 | `POST /login` — login novo usuario | 200 | 200 | ✅ igual |
| 24 | `POST /login` — login falha | 401 | 401 | ✅ igual |
| 25 | `POST /login` — login sqli probe | 200 | 401 | 🔒 bypass de login bloqueado (antes: 200 como Admin) |
| 26 | `POST /pedidos` — criar pedido | 201 | 201 | ✅ igual |
| 27 | `POST /pedidos` — criar pedido sem estoque | 400 | 400 | ✅ igual |
| 28 | `POST /pedidos` — criar pedido produto inexistente | 400 | 400 | ✅ igual |
| 29 | `POST /pedidos` — criar pedido sem itens | 400 | 400 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 30 | `GET /pedidos` — list pedidos | 200 | 200 | ✅ igual |
| 31 | `GET /pedidos/usuario/2` — pedidos usuario | 200 | 200 | ✅ igual |
| 32 | `PUT /pedidos/1/status` — status pedido | 200 | 200 | ✅ igual |
| 33 | `PUT /pedidos/1/status` — status pedido invalido | 400 | 400 | ✅ status igual; envelope de erro unificado (+`sucesso`) |
| 34 | `GET /relatorios/vendas` — relatorio vendas | 200 | 200 | ✅ igual |
| 35 | `POST /admin/query` — admin query sem auth | 200 | 403 | 🔒 exige `X-Admin-Token` |
| 36 | `GET /nao-existe` — rota inexistente | 404 | 404 | ✅ igual |
| 37 | `POST /admin/query` — admin query com token | — | 200 | 🆕 SELECT único permitido com token |
| 38 | `POST /admin/query` — admin query DELETE com token | — | 400 | 🆕 escrita via /admin/query bloqueada |
| 39 | `POST /pedidos` — pedido quantidade negativa | — | 400 | 🆕 quantidade negativa rejeitada (antes aumentava estoque) |

**33 iguais ao baseline · 3 mudanças intencionais · 3 verificações novas · 0 erros 5xx**
