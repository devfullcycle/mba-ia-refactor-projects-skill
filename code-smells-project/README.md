# code-smells-project

API de E-commerce em Python/Flask refatorada para o padrão MVC com a skill `refactor-arch`.

## Stack

- **Linguagem:** Python 3
- **Framework:** Flask 3.1.1 + flask-cors
- **Banco:** SQLite (via `sqlite3` stdlib)
- **Configuração:** `python-dotenv`

## Estrutura

```
code-smells-project/
├── app.py                        # Composition root — só monta a aplicação
├── database.py                   # Conexão por request via Flask g
├── .env                          # Secrets (não commitado)
├── .env.example                  # Template de variáveis de ambiente
├── config/
│   └── settings.py               # Toda configuração lida de env vars
├── models/
│   ├── product_model.py          # CRUD de produtos (queries parametrizadas)
│   ├── user_model.py             # CRUD de usuários + autenticação bcrypt
│   └── order_model.py            # CRUD de pedidos com JOIN e transação
├── controllers/
│   ├── product_controller.py     # Validação e orquestração de produtos
│   ├── user_controller.py        # Validação de email/senha e orquestração
│   └── order_controller.py       # Lógica de desconto e orquestração de pedidos
├── views/
│   ├── product_routes.py         # Blueprint /produtos
│   ├── user_routes.py            # Blueprint /usuarios + /login
│   └── order_routes.py           # Blueprint /pedidos + /relatorios
└── middlewares/
    └── error_handler.py          # Handlers centralizados 400/404/405/500
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env              # edite SECRET_KEY antes de subir em produção
python3 app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot com produtos e usuários de exemplo (senhas hasheadas com bcrypt).

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Índice da API |
| GET | `/health` | Status da aplicação |
| GET | `/produtos` | Listar produtos |
| GET | `/produtos/busca` | Buscar produtos (`?q=`, `?categoria=`, `?preco_min=`, `?preco_max=`) |
| GET | `/produtos/<id>` | Buscar produto por ID |
| POST | `/produtos` | Criar produto |
| PUT | `/produtos/<id>` | Atualizar produto |
| DELETE | `/produtos/<id>` | Deletar produto |
| GET | `/usuarios` | Listar usuários |
| GET | `/usuarios/<id>` | Buscar usuário por ID |
| POST | `/usuarios` | Criar usuário |
| POST | `/login` | Autenticar usuário |
| POST | `/pedidos` | Criar pedido |
| GET | `/pedidos` | Listar todos os pedidos |
| GET | `/pedidos/usuario/<id>` | Listar pedidos de um usuário |
| PUT | `/pedidos/<id>/status` | Atualizar status do pedido |
| GET | `/relatorios/vendas` | Relatório de vendas com faturamento e descontos |

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | `dev-only-change-in-production` | Chave de sessão Flask |
| `DATABASE_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `DEBUG` | `False` | Modo debug (`True`/`False`) |
