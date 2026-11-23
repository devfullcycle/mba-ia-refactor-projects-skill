# Guidelines de Arquitetura MVC Alvo

Este documento define as regras arquiteturais e de responsabilidades que a **Fase 3 (Refatoração)** da skill `refactor-arch` deve aplicar em qualquer projeto legado, independente da tecnologia (Python, Node.js, Go, etc.).

---

## 1. Princípios Fundamentais do Padrão MVC para APIs

Em uma arquitetura de API RESTful orientada a MVC:
- **Model**: Responsável exclusivamente pela representação e persistência dos dados (entidades, regras de integridade relacional, consultas parametrizadas ao banco de dados).
- **View / Route**: Camada de fronteira HTTP responsável por expor as rotas/endpoints, mapear verbos e caminhos, e serializar/deserializar respostas (Blueprints no Flask, Routers no Express).
- **Controller**: Camada de orquestração do fluxo de requisição. Recebe dados validados da rota/view, coordena as operações chamando os Models/Services e determina a resposta e código HTTP adequado.

```
       +------------------------------------+
       |          Client (HTTP)             |
       +-----------------+------------------+
                         |
                         v
       +------------------------------------+
       |          Views / Routes            |  (Mapeamento de rotas e verbos HTTP)
       +-----------------+------------------+
                         |
                         v
       +------------------------------------+
       |            Controllers             |  (Orquestração do fluxo e status codes)
       +--------+------------------+--------+
                |                  |
                v                  v
       +----------------+  +----------------+
       |     Models     |  |   Services     |  (Regras de negócio e persistência de dados)
       +--------+-------+  +----------------+
                |
                v
       +----------------+
       | Database / SQL |
       +----------------+
```

---

## 2. Estrutura Padrão de Diretórios

Ao refatorar qualquer aplicação, organize a árvore de arquivos de forma limpa e modular:

### Estrutura Python / Flask:
```
src/ (ou na raiz do projeto conforme convenção)
├── config/
│   └── settings.py          # Configurações extraídas de variáveis de ambiente
├── models/
│   ├── base.py (ou database.py) # Conexão e sessão centralizada
│   ├── produto_model.py     # Queries parametrizadas ou Model ORM
│   ├── usuario_model.py     # Métodos de busca, criação e auth segura
│   └── pedido_model.py      # Operações transacionais e joins
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── views/ (ou routes/)
│   ├── produto_routes.py    # Flask Blueprints
│   ├── usuario_routes.py
│   └── pedido_routes.py
├── middlewares/
│   └── error_handler.py     # Tratamento centralizado de exceções
└── app.py                   # Composition Root (inicialização e registro)
```

### Estrutura Node.js / Express:
```
src/
├── config/
│   └── config.js            # Extração de process.env com defaults seguros
├── models/
│   ├── database.js          # Pool de conexão SQLite/Postgres
│   ├── userModel.js         # Queries parametrizadas de usuários
│   ├── courseModel.js       # Queries de cursos
│   └── paymentModel.js      # Transações de matrículas e pagamentos
├── controllers/
│   ├── checkoutController.js
│   ├── reportController.js
│   └── userController.js
├── routes/
│   ├── checkoutRoutes.js    # express.Router()
│   ├── reportRoutes.js
│   └── userRoutes.js
├── middlewares/
│   └── errorHandler.js      # Middleware de erro: (err, req, res, next)
└── app.js                   # Composition Root (servidor Express e middlewares)
```

---

## 3. Matriz de Responsabilidades por Camada

### Camada Config (`config/`)
- **DEVE**: Ler parâmetros sensíveis e de ambiente via variáveis de ambiente (`os.getenv`, `process.env`), fornecendo fallbacks seguros apenas para desenvolvimento local.
- **NÃO DEVE**: Conter segredos de produção hardcoded ou lógica de processamento de dados.

### Camada Models (`models/`)
- **DEVE**:
  - Isolar todas as instruções SQL (usando estritamente prepared statements / queries parametrizadas com placeholders).
  - Executar operações transacionais (`commit`, `rollback`) de forma atômica.
  - Implementar queries complexas usando `JOIN` para eliminar o anti-pattern de N+1 queries.
  - Ocultar dados sensíveis (nunca serializar hashes de senha ou chaves no método `to_dict()` ou de exportação de dados).
- **NÃO DEVE**: Importar objetos de requisição HTTP (`request`, `Response`, `jsonify`, `req`, `res`).

### Camada Controllers (`controllers/`)
- **DEVE**:
  - Receber os dados tratados da requisição HTTP (parâmetros de rota, query string, JSON body).
  - Validar tipos básicos e obrigatórios.
  - Chamar os métodos dos Models e Services correspondentes.
  - Retornar o código de status HTTP semântico (`200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, etc.) e a resposta estruturada.
- **NÃO DEVE**:
  - Conter queries SQL brutas (`cursor.execute`, `SELECT * FROM`).
  - Executar concatenações de strings SQL.
  - Engolir exceções com blocos vazios.

### Camada Views / Routes (`views/` ou `routes/`)
- **DEVE**:
  - Declarar as rotas com métodos HTTP explícitos (`methods=['GET']`, `router.post(...)`).
  - Delegar a execução para a função correspondente do Controller.
  - Centralizar agrupamento por domínio via Blueprints (Flask) ou Routers (Express).
- **NÃO DEVE**: Conter lógica de negócio, loops de agregação de dados ou chamadas diretas ao banco.

### Camada Middlewares & Error Handling (`middlewares/`)
- **DEVE**:
  - Capturar exceções não tratadas globalmente.
  - Registrar logs com nível de detalhe adequado (usando o módulo padrão de log da linguagem).
  - Responder ao cliente com formato JSON uniforme e sem expor stacktraces internos em ambiente de produção.

---

## 4. Regras de Compatibilidade e Semântica

Ao refatorar qualquer projeto:
1. **Preservar Contratos de API de Negócio**: Todos os endpoints de negócio existentes, métodos HTTP, parâmetros aceitos e formato das respostas JSON válidas devem continuar respondendo conforme os contratos originais da aplicação.
   - *Exceção para Endpoints de Infraestrutura / Health Checks (`/health`)*: Devem ser simplificados para validação atômica de conectividade (`SELECT 1`), eliminando contagens agregadas (`COUNT(*)`) ou scans desnecessários que sobrecarregam o banco em sondas periódicas (probes).
2. **Preservar a Base de Dados**: As tabelas e dados seed pré-existentes devem ser mantidos e acessíveis.
3. **Validar a Execução**: A aplicação deve inicializar sem falhas e responder a testes de saúde e chamadas aos endpoints.
