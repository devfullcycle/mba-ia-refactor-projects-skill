# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Originalmente tinha alguma separação de camadas, mas com problemas arquiteturais e de qualidade; foi refatorado para MVC (veja a seção de arquitetura).

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Arquitetura (pós-refatoração)

```
app.py            # create_app(): composition root
config/           # settings.py (única leitura de variáveis de ambiente)
models/           # entidades + regras de domínio (is_overdue, hash de senha)
services/         # regras de negócio e queries (task, user, category, report, notification)
controllers/      # orquestração: request -> validator -> service -> view
validators/       # validação de entrada (400 com mensagens uniformes)
views/            # serializers JSON (nunca expõem password)
routes/           # só mapeia URL -> controller
middlewares/      # auth.py (token assinado), error_handler.py (erros centralizados)
utils/            # constants, errors, clock, stats, request_utils
```

## Configuração

Copie `.env.example` para `.env`. Principais variáveis: `SECRET_KEY`, `DATABASE_URL`, `DEBUG` (padrão `false`), `HOST` (padrão `127.0.0.1`), `PORT`, `CORS_ORIGINS`, `SMTP_*`.

## Autenticação

`POST /login` devolve um token assinado. Envie-o em `Authorization: Bearer <token>` nas operações protegidas:

- `DELETE /tasks/<id>` e `DELETE /categories/<id>`: qualquer usuário autenticado.
- `DELETE /users/<id>`: apenas `admin`.
- `POST /users` com `role` diferente de `user`: apenas `admin`.

Senhas antigas em MD5 continuam válidas e são migradas para hash seguro no próximo login.
