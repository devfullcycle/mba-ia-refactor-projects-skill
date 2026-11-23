# code-smells-project

API de E-commerce em Python/Flask refatorada seguindo a arquitetura MVC desacoplada.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Arquitetura e Decisões Técnicas

- **MVC Desacoplado**:
  - `models/`: Entidades de domínio com queries 100% parametrizadas (proteção contra SQL Injection) e soft delete seguro.
  - `controllers/`: Orquestradores de regras de negócio com Guard Clauses lineares.
  - `views/`: Registro explícito de rotas utilizando Flask Blueprints e verbos HTTP declarados.
  - `config/`: Centralização de variáveis de ambiente e constantes desacopladas.
  - `middlewares/`: Tratamento centralizado de erros e exceções (`error_handler.py`).

- **Health Check Otimizado (`/health`)**:
  - Em conformidade com as boas práticas de observabilidade e sondas (*probes* de liveness/readiness), o endpoint `/health` não executa mais `COUNT(*)` sobre as tabelas da base de dados.
  - Valida apenas a conectividade atômica com o banco (`SELECT 1`), evitando sobrecarga de I/O e risco de *cascading failures* em checagens periódicas de infraestrutura. Retorna HTTP 200 quando saudável ou 503 se o banco estiver inacessível.
