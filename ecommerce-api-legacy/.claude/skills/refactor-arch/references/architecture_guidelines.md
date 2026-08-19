# Guidelines de Arquitetura Target (Padrão MVC)

Toda refatoração executada pela skill deve reestruturar a codebase legada para o padrão **Model-View-Controller (MVC)** robusto. Este documento estabelece as responsabilidades e limites claros de cada camada.

## 1. Estrutura de Diretórios Alvo

A nova estrutura de pastas do projeto após a refatoração deve ser organizada da seguinte forma:

```
[raiz-do-projeto]/
├── config/              # Configurações globais e inicialização de variáveis (ex: banco de dados, chaves)
│   └── settings.py ou config.js
├── models/              # Camada de Dados: Mapeamento de tabelas, schemas e persistência pura
│   ├── produto.py ou produto_model.js
│   └── usuario.py ou usuario_model.js
├── controllers/         # Camada de Controle: Orquestração de fluxo de negócio e lógica da aplicação
│   ├── produto_controller.py ou produto_controller.js
│   └── usuario_controller.py ou usuario_controller.js
├── routes/ (ou views/)  # Camada de Roteamento / Apresentação: Definição de endpoints HTTP e mapeamento
│   ├── routes.py ou routes.js
│   └── (pode ser separado por domínio se fizer sentido)
├── middlewares/         # Processamento de requisições transversais (ex: tratamento global de erros)
│   └── error_handler.py ou error_handler.js
└── app.py ou server.js  # Entry point de inicialização (Composition Root)
```

---

## 2. Responsabilidades das Camadas

### A) Config (`config/`)
* **Papel**: Centralizar a leitura de variáveis de ambiente (`.env`), configurações de porta, caminhos de banco de dados e inicialização primária de conexões (ex: pooling).
* **Regra**: Nunca armazene senhas ou tokens diretamente (use `os.getenv` ou `process.env`).

### B) Models (`models/`)
* **Papel**: Representar as entidades de domínio e encapsular todas as operações com banco de dados (ex: SELECT, INSERT, UPDATE, DELETE).
* **Regras**:
  - **Isolamento de HTTP**: O Model deve ser totalmente "cego" à web. Nunca importe ou faça referência a objetos como `request`, `req`, `res`, `jsonify`, `session` ou status HTTP nos models.
  - Recebe parâmetros primitivos ou instâncias limpas de dados e retorna dados brutos ou objetos serializados puros.

### C) Controllers (`controllers/`)
* **Papel**: Agir como intermediário entre a Camada de Rotas (Views) e a Camada de Dados (Models).
* **Regras**:
  - Extrai dados vindos da rota (parâmetros de rota, query string, body).
  - Executa as validações de input (ex: tamanho de texto, campos obrigatórios).
  - Invoca os Models apropriados para buscar ou persistir informações.
  - Executa lógicas e regras de negócio associadas (cálculos de preço, envio de notificações via serviços).
  - Define o status HTTP correto e envia os dados para formatação final.

### D) Routes / Views (`routes/` ou `views/`)
* **Papel**: Registrar os endpoints de URL (caminhos e métodos HTTP como GET, POST, PUT, DELETE) e mapeá-los para seus respectivos Controllers.
* **Regras**:
  - Não executa lógica de negócio, não valida dados e não conversa com o banco.
  - Apenas passa a requisição para o controller correspondente e retorna a resposta formatada pelo mesmo.

### E) Middlewares / Error Handler (`middlewares/`)
* **Papel**: Centralizar as exceções geradas na aplicação de forma automática.
* **Regras**:
  - Capturar erros não tratados e retornar uma resposta JSON unificada, ocultando detalhes técnicos de stacktrace em produção mas mantendo logs úteis.

### F) Entry point (`app.py` ou `server.js`)
* **Papel**: Composition Root da aplicação.
* **Regras**:
  - Instanciar a aplicação Express ou Flask.
  - Configurar CORS, analisadores de JSON e middlewares globais.
  - Inicializar conexões de banco de dados e registrar as rotas globais.
  - Iniciar o servidor HTTP na porta desejada.
