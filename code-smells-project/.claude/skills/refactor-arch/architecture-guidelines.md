# MVC Architecture Guidelines

## Visao Geral

O padrao MVC (Model-View-Controller) separa responsabilidades em 3 camadas:

- **Model** — Estrutura de dados, acesso ao banco, regras de dominio
- **View/Routes** — Definicao de endpoints, serializacao de respostas HTTP
- **Controller** — Orquestracao do fluxo, logica de negocio, coordenacao de services

## Estrutura de Diretorios

### Python/Flask

```
src/
├── config/
│   └── settings.py          # Config via env vars (DB URI, SECRET_KEY)
├── models/
│   ├── __init__.py
│   ├── produto_model.py     # Um model por dominio
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── routes/
│   ├── __init__.py
│   ├── produto_routes.py    # Blueprint com rotas
│   ├── usuario_routes.py
│   └── pedido_routes.py
├── services/
│   ├── __init__.py
│   └── notification_service.py
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py     # Error handling centralizado
├── database.py              # Configuracao do DB
└── app.py                   # Composition root (entry point)
```

### Node.js/Express

```
src/
├── config/
│   └── settings.js          # Config via env vars
├── models/
│   ├── userModel.js         # Um model por dominio
│   ├── courseModel.js
│   └── enrollmentModel.js
├── controllers/
│   ├── checkoutController.js
│   ├── reportController.js
│   └── userController.js
├── routes/
│   ├── checkoutRoutes.js
│   ├── reportRoutes.js
│   └── userRoutes.js
├── services/
│   ├── paymentService.js
│   └── authService.js
├── middlewares/
│   └── errorHandler.js
├── database.js
└── app.js                   # Composition root
```

## Responsabilidades de Cada Camada

### Model Layer
- Define schema/estrutura dos dados
- Operacoes CRUD no banco
- Validacao de campos (tipos, obrigatoriedade)
- Metodos de dominio (ex: `is_overdue()`, `to_dict()`)
- **NUNCA** importa request/response do Flask ou req/res do Express
- **NUNCA** contem HTTP status codes ou logica de roteamento

### Controller Layer
- Recebe dados validados das routes
- Aplica regras de negocio (alem de validacao de campos)
- Chama methods dos models para operacoes de dados
- Chama services para preocupacoes transversais (notificacao, pagamento)
- Retorna dados estruturados para a route
- **NUNCA** contem SQL queries diretamente (sempre via models)
- **NUNCA** contem codigo HTTP-specific (status codes, jsonify, response objects)

### Route/View Layer
- Define patterns de URL e metodos HTTP
- Extrai parametros do request (body, query, path params)
- Chama o controller method apropriado
- Formata e retorna HTTP responses (status codes, JSON)
- Registra blueprints (Flask) ou routers (Express)
- **NUNCA** contem logica de negocio
- **NUNCA** contem database queries

### Config Layer
- Strings de conexao de banco via variaveis de ambiente
- SECRET_KEY via variaveis de ambiente
- Feature flags
- Portas, hosts
- **NUNCA** contem hardcoded secrets

### Middleware Layer
- Error handling centralizado
- CORS configuration
- Authentication/Authorization
- Request logging

### Entry Point (app.py / app.js)
- Cria a instancia da aplicacao
- Carrega configuracao
- Inicializa database
- Registra blueprints/routes
- Registra error handlers
- Inicia o servidor

Deve ser minimal — apenas um "composition root" que conecta tudo.

## Principios Chave

1. **Direcao de dependencia:** Routes → Controllers → Models. Nunca o reverso.
2. **Single Responsibility:** Cada arquivo/classe cuida de um conceito de dominio.
3. **Sem God Classes:** Dividir arquivos multi-dominio em modulos separados.
4. **Configuracao externa:** Todos secrets, DB paths, portas vem de env vars.
5. **Error handling centralizado:** Um middleware captura todos erros de forma consistente.
6. **Parameterized queries:** Sempre usar `?` ou `%s` placeholders, nunca concatenacao.
7. **Sem logica de negocio em Routes:** Routes apenas parseiam request e chamam controller.
8. **Sem SQL em Controllers:** Controllers chamam model methods, models executam queries.
9. **Async/Await em Node.js:** Nunca callbacks aninhadas — usar async/await com Promises.
10. **Hash seguro de senhas:** bcrypt ou werkzeug.security, nunca MD5/SHA1.
