# task-manager-api

API de Task Manager em Python/Flask refatorada para o padrao MVC pelo `refactor-arch`.

## Como rodar
```bash
pip install -r requirements.txt
cp .env.example .env
python seed.py
python app.py
```

A aplicacao sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuarios, categorias e tasks de exemplo — rode-o antes do primeiro boot.

## Arquitetura MVC
- **Models** (`models/`) — schema de dados, acesso ao banco, regras de dominio (ex: `Task.is_overdue()`)
- **Controllers** (`controllers/`) — logica de negocio, orquestracao de models e services
- **Routes** (`routes/`) — definicao de endpoints, extracao de parametros, retorno de responses
- **Services** (`services/`) — integracoes externas (email via SMTP)
- **Middlewares** (`middlewares/`) — error handling centralizado
- **Config** (`config.py`) — toda configuracao via variaveis de ambiente
