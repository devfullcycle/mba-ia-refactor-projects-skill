# code-smells-project

API de E-commerce em Python/Flask (produtos, usuários, pedidos e relatório de vendas).

Projeto refatorado para MVC pela skill [`refactor-arch`](.claude/skills/refactor-arch/).
Auditoria: [`reports/audit-project-1.md`](../reports/audit-project-1.md) ·
Validação: [`reports/validation-project-1.md`](../reports/validation-project-1.md).

## Como rodar

Requer Python ≥ 3.9 (`flask==3.1.1`).

```bash
python3.9 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado no primeiro
boot, já com produtos e usuários de exemplo.

Configuração por variáveis de ambiente — ver [`.env.example`](.env.example). Em
desenvolvimento a `SECRET_KEY` é gerada de forma efêmera a cada boot; com
`APP_ENV=production` a aplicação recusa iniciar sem ela. O debug é opt-in
(`FLASK_DEBUG=true`), nunca ligado por default.

## Estrutura

```
src/
├── config/{settings,logging_config}.py                 # ambiente → configuração
├── database/{connection,schema}.py                     # conexão por request, DDL e seed explícitos
├── models/{produto,usuario,pedido}_model.py            # persistência + invariantes
├── validators/{produto,usuario,pedido}_validator.py    # regra única de validação
├── services/notification_service.py
├── controllers/{produto,usuario,pedido,relatorio,health}_controller.py
├── views/{produto,usuario,pedido,relatorio,health}_routes.py    # só mapeamento
├── middlewares/error_handler.py                        # tratamento de erro centralizado
└── app.py                                              # composition root (create_app)
run.py                                                  # entry point
```

## Endpoints

`GET /` · `GET /health` · `GET|POST /produtos` · `GET /produtos/busca` ·
`GET|PUT|DELETE /produtos/<id>` · `GET|POST /usuarios` · `GET /usuarios/<id>` ·
`POST /login` · `GET|POST /pedidos` · `GET /pedidos/usuario/<id>` ·
`PUT /pedidos/<id>/status` · `GET /relatorios/vendas`

`POST /admin/query` e `POST /admin/reset-db` foram **removidos** na refatoração: executavam SQL
arbitrário e apagavam o banco sem autenticação (finding 2 da auditoria).

## Validação

```bash
../scripts/smoke-project-1.sh /tmp/p1     # 33 chamadas nos 19 endpoints
```
