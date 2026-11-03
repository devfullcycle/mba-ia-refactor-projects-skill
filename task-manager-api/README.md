# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. O projeto já tinha separação parcial de camadas e foi **reorganizado para MVC** pela skill (`.claude/skills/refactor-arch`), mantendo a organização em pastas na raiz.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (`PORT`/`HOST` configuráveis — no macOS a porta 5000 costuma estar ocupada pelo AirPlay, use `PORT=5053 python app.py`). O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**. Variáveis disponíveis em `.env.example` (`SECRET_KEY`, SMTP etc.).

## Estrutura

```
app.py                 # entry point + composition root (create_app)
config/settings.py     # configuração via variáveis de ambiente
database.py            # instância do SQLAlchemy
models/                # Task, User, Category: colunas, regras de domínio, consultas e serialização
controllers/           # task, user, report, category: fluxo dos casos de uso
routes/                # camada View: Blueprints que mapeiam HTTP → controller
validators/            # validação de entrada por entidade
services/              # notificação (SMTP via config) e token assinado
middlewares/           # error handler central
utils/                 # erros de domínio e helpers de data
seed.py                # dados de exemplo
```

Senhas usam `werkzeug.security` (hashes MD5 legados são migrados no primeiro login) e o login devolve um token assinado com expiração.
