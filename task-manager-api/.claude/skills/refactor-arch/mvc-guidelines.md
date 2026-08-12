# MVC Guidelines

## Objetivo
Definir regras claras para refatorar qualquer projeto legado para uma arquitetura MVC sustentável.

## Camadas MVC
### Models
Responsabilidades:
- Abstrair acesso a dados e persistência.
- Definir entidades e mapeamento de dados.
- Validar regras de integridade de dados de baixo nível.

Exemplos:
- Python: classes ou funções em `models/` que executam queries parametrizadas ou usam ORM.
- Node.js: objetos/repositórios que encapsulam `db.query` e retornam dados.

### Controllers
Responsabilidades:
- Orquestrar a lógica de aplicação.
- Chamar models e serviços.
- Tratar entradas e resultados antes de enviar resposta.
- Delegar tratamento de erros para middleware.

Exemplo:
- `controllers/produto_controller.py` ou `controllers/checkoutController.js`.

### Views / Routes
Responsabilidades:
- Expor endpoints HTTP.
- Mapear rotas para controllers.
- Não conter lógica de negócios ou regras complexas.

Exemplo:
- rotas Flask com Blueprint ou `app.add_url_rule`
- `express.Router()` que importa controllers

## Configuração
- Mova segredos e URIs para `config/settings.py` ou `config/index.js`.
- Use variáveis de ambiente para valores sensíveis.
- Não deixe `SECRET_KEY`, `DB_URI`, `API_KEY` codificados.

## Middlewares e Tratamento de Erros
- Centralize captura de exceções.
- Crie middleware para validação e erros.
- Evite `try/except` ou `try/catch` espalhados que repetem mensagens.

## Regras de Refatoração
- Rotas devem ser finas: validação mínima + chamada de controller.
- Controllers devem ser responsáveis pelo fluxo, não por persistência detalhada.
- Models devem ser responsáveis pela persistência e retorno de dados em formatos simples.
- Normalizar respostas JSON / status HTTP de forma consistente.
- Evitar dependências circulares entre camadas.

## Estrutura mínima sugerida
- `config/`
- `models/`
- `controllers/`
- `routes/` ou `views/`
- `middlewares/`
- `app.py` / `server.js`

## Validação após refatoração
- A aplicação deve iniciar sem erros.
- Um endpoint representativo deve responder corretamente.
- O projeto deve estar mais modular e com responsabilidade separada.
