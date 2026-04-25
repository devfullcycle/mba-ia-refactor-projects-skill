# code-smells-project — E-commerce API

Python/Flask API de e-commerce (produtos, pedidos, usuários).

## Stack
- Python 3 + Flask 3.1.1 + flask-cors
- SQLite (arquivo `loja.db`)
- Sem ORM — queries SQL diretas via `sqlite3`

## Como rodar
```bash
pip install -r requirements.txt
python app.py
# Roda em http://localhost:5000
```

## Estrutura atual
```
app.py           # Entry point, rotas registradas via add_url_rule, admin routes inline
controllers.py   # Handlers das rotas (validação + chamadas ao models + respostas)
models.py        # Toda lógica de acesso ao banco (CRUD de 4 domínios misturados)
database.py      # Conexão SQLite global + CREATE TABLE + seed data
requirements.txt # flask, flask-cors
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Index com lista de endpoints |
| GET | `/produtos` | Listar produtos |
| GET | `/produtos/busca?q=&categoria=&preco_min=&preco_max=` | Buscar produtos |
| GET | `/produtos/<id>` | Buscar produto por ID |
| POST | `/produtos` | Criar produto |
| PUT | `/produtos/<id>` | Atualizar produto |
| DELETE | `/produtos/<id>` | Deletar produto |
| GET | `/usuarios` | Listar usuários |
| GET | `/usuarios/<id>` | Buscar usuário por ID |
| POST | `/usuarios` | Criar usuário |
| POST | `/login` | Login (email + senha) |
| POST | `/pedidos` | Criar pedido com itens |
| GET | `/pedidos` | Listar todos pedidos (com itens e nomes) |
| GET | `/pedidos/usuario/<id>` | Pedidos de um usuário |
| PUT | `/pedidos/<id>/status` | Atualizar status do pedido |
| GET | `/relatorios/vendas` | Relatório de vendas com faturamento |
| GET | `/health` | Health check (DB + counts) |
| POST | `/admin/reset-db` | Deleta todos os dados |
| POST | `/admin/query` | Executa SQL arbitrário do body |

## Tabelas SQLite
- `produtos` (id, nome, descricao, preco, estoque, categoria, ativo, criado_em)
- `usuarios` (id, nome, email, senha, tipo, criado_em)
- `pedidos` (id, usuario_id, status, total, criado_em)
- `itens_pedido` (id, pedido_id, produto_id, quantidade, preco_unitario)

## Problemas conhecidos (análise manual)
- SQL Injection: todas as queries usam string concatenation
- Hardcoded SECRET_KEY e senhas de seed
- God File: models.py com 315 linhas e 4 domínios
- Endpoint `/admin/query` executa SQL arbitrário sem auth
- Senhas retornadas em endpoints de usuário e health check
- N+1 queries ao buscar pedidos com itens
- Código duplicado entre funções de pedidos
- debug=True em produção
