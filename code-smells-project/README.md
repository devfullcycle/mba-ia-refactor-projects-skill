# code-smells-project

API de E-commerce (produtos, pedidos, usuários) construída em **Python + Flask + SQLite**.

## O que faz

Gerencia uma loja virtual com catálogo de produtos, carrinho de compras, pedidos e relatórios de vendas. Inclui autenticação básica e endpoints administrativos.

### Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Index com lista de endpoints |
| **Produtos** | | |
| `GET` | `/produtos` | Listar todos os produtos |
| `GET` | `/produtos/busca?q=&categoria=&preco_min=&preco_max=` | Buscar com filtros |
| `GET` | `/produtos/<id>` | Buscar por ID |
| `POST` | `/produtos` | Criar produto |
| `PUT` | `/produtos/<id>` | Atualizar produto |
| `DELETE` | `/produtos/<id>` | Remover produto |
| **Usuários** | | |
| `GET` | `/usuarios` | Listar usuários (sem senhas) |
| `GET` | `/usuarios/<id>` | Buscar por ID |
| `POST` | `/usuarios` | Criar usuário (senha com hash) |
| `POST` | `/login` | Login (email + senha) |
| **Pedidos** | | |
| `POST` | `/pedidos` | Criar pedido com itens |
| `GET` | `/pedidos` | Listar todos os pedidos (com itens e nomes via JOIN) |
| `GET` | `/pedidos/usuario/<id>` | Pedidos de um usuário |
| `PUT` | `/pedidos/<id>/status` | Atualizar status |
| **Relatórios** | | |
| `GET` | `/relatorios/vendas` | Relatório de vendas com faturamento |
| `GET` | `/health` | Health check (status + contagens) |
| **Admin** (requer Bearer token) | | |
| `POST` | `/admin/reset-db` | Limpa todos os dados |
| `POST` | `/admin/query` | Executa SQL arbitrário |

### Banco de Dados

SQLite em arquivo (`loja.db`), criado automaticamente no primeiro boot com dados de exemplo:

| Tabela | Descrição |
|--------|-----------|
| `produtos` | Catálogo (nome, descrição, preço, estoque, categoria) |
| `usuarios` | Usuários (nome, email, senha hasheada, tipo) |
| `pedidos` | Pedidos (usuário, status, total) |
| `itens_pedido` | Itens de cada pedido (produto, quantidade, preço unitário) |

### Dados de Exemplo (seed)

- **Admin:** admin (`admin@loja.com`, senha: `admin123`)
- **Usuários:** Maria, Carlos, Ana
- **Produtos:** Notebook, Mouse, Teclado, Monitor, Webcam, Headset
- **Pedidos:** Alguns pedidos de exemplo com itens

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env    # ajuste as variáveis
python app.py
```

Sobe em `http://localhost:5000`.

## Arquitetura

```
app.py                       # Composition root (create_app factory)
config/
  settings.py                # Variáveis de ambiente + constantes
database/
  connection.py              # Conexão via Flask g (sem estado global)
  schema.py                  # Criação de tabelas + seed data (senhas com hash)
models/
  product_model.py           # CRUD de produtos + busca com filtros
  user_model.py              # CRUD de usuários + autenticação
  order_model.py             # CRUD de pedidos (JOINs, sem N+1)
  report_model.py            # Relatório de vendas + health data
controllers/
  product_controller.py      # Validação + lógica de produtos
  user_controller.py         # Validação + lógica de usuários
  order_controller.py        # Lógica de pedidos + delegação de notificação
  report_controller.py       # Orquestração de relatórios
routes/
  product_routes.py          # Endpoints de produtos (Blueprint)
  user_routes.py             # Endpoints de usuários + login
  order_routes.py            # Endpoints de pedidos
  report_routes.py           # Endpoints de relatórios + health
  admin_routes.py            # Endpoints admin (protegidos por token)
services/
  notification_service.py    # Abstração de notificações (logging)
middlewares/
  error_handler.py           # Error handling centralizado + auth admin
```

**Direção de dependência:** Routes → Controllers → Models. Nunca o reverso.

## Configuração

Veja `.env.example`:

```env
SECRET_KEY=dev-secret-key-change-in-production
FLASK_DEBUG=false
DATABASE_PATH=loja.db
ADMIN_TOKEN=admin-dev-token
```
