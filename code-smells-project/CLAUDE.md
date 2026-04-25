# code-smells-project — E-commerce API

Python/Flask API de e-commerce (produtos, pedidos, usuarios) refatorada para arquitetura MVC.

## Stack
- Python 3 + Flask 3.1.1 + flask-cors
- SQLite (arquivo `loja.db`)
- Queries SQL com parameterized placeholders via `sqlite3`
- Password hashing com `werkzeug.security`

## Como rodar
```bash
pip install -r requirements.txt
cp .env.example .env   # ajuste as variaveis
python app.py
# Roda em http://localhost:5000
```

## Estrutura
```
app.py                  # Composition root (create_app factory)
config/
  settings.py           # Variaveis de ambiente + constantes
database/
  connection.py         # Conexao via Flask g (sem estado global)
  schema.py             # Criacao de tabelas + seed data (senhas com hash)
models/
  product_model.py      # CRUD de produtos + busca
  user_model.py         # CRUD de usuarios + autenticacao
  order_model.py        # CRUD de pedidos (JOINs, sem N+1)
  report_model.py       # Relatorio de vendas + health data
controllers/
  product_controller.py # Validacao + logica de produtos
  user_controller.py    # Validacao + logica de usuarios
  order_controller.py   # Logica de pedidos + delegacao de notificacao
  report_controller.py  # Orquestracao de relatorios
routes/
  product_routes.py     # Endpoints de produtos (Blueprint)
  user_routes.py        # Endpoints de usuarios + login
  order_routes.py       # Endpoints de pedidos
  report_routes.py      # Endpoints de relatorios + health
  admin_routes.py       # Endpoints admin (protegidos por token)
services/
  notification_service.py # Abstracao de notificacoes (logging)
middlewares/
  error_handler.py      # Error handling centralizado + auth admin
reports/
  audit-report.md       # Relatorio de auditoria pre-refatoracao
.env.example            # Template de variaveis de ambiente
```

## Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/` | Index com lista de endpoints |
| GET | `/produtos` | Listar produtos |
| GET | `/produtos/busca?q=&categoria=&preco_min=&preco_max=` | Buscar produtos |
| GET | `/produtos/<id>` | Buscar produto por ID |
| POST | `/produtos` | Criar produto |
| PUT | `/produtos/<id>` | Atualizar produto |
| DELETE | `/produtos/<id>` | Deletar produto |
| GET | `/usuarios` | Listar usuarios (sem senha) |
| GET | `/usuarios/<id>` | Buscar usuario por ID (sem senha) |
| POST | `/usuarios` | Criar usuario (senha com hash) |
| POST | `/login` | Login (email + senha) |
| POST | `/pedidos` | Criar pedido com itens |
| GET | `/pedidos` | Listar todos pedidos (com itens e nomes via JOIN) |
| GET | `/pedidos/usuario/<id>` | Pedidos de um usuario |
| PUT | `/pedidos/<id>/status` | Atualizar status do pedido |
| GET | `/relatorios/vendas` | Relatorio de vendas com faturamento |
| GET | `/health` | Health check (status + counts) |
| POST | `/admin/reset-db` | Deleta todos os dados (requer Bearer token) |
| POST | `/admin/query` | Executa SQL (requer Bearer token) |

## Tabelas SQLite
- `produtos` (id, nome, descricao, preco, estoque, categoria, ativo, criado_em)
- `usuarios` (id, nome, email, senha, tipo, criado_em)
- `pedidos` (id, usuario_id, status, total, criado_em)
- `itens_pedido` (id, pedido_id, produto_id, quantidade, preco_unitario)

## Variaveis de ambiente
| Variavel | Descricao | Default |
|----------|-----------|---------|
| `SECRET_KEY` | Chave secreta do Flask | dev-secret-key-change-in-production |
| `FLASK_DEBUG` | Modo debug | false |
| `DATABASE_PATH` | Caminho do banco SQLite | loja.db |
| `ADMIN_TOKEN` | Token para endpoints admin | admin-dev-token |

## Direcao de dependencia
Routes -> Controllers -> Models. Nunca o reverso.
Routes apenas extraem dados do request e chamam controllers.
Controllers orquestram logica e chamam models/services.
Models acessam o banco e nao dependem de HTTP.
