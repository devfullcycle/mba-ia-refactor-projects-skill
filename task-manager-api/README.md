# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Toda configuração vem de variáveis de ambiente (ou de um arquivo `.env`); veja `.env.example`. Em desenvolvimento nenhuma é obrigatória, mas defina `SECRET_KEY` em produção. Por padrão o servidor escuta em `127.0.0.1` com debug desligado — use `HOST=0.0.0.0` e/ou `FLASK_DEBUG=true` se necessário.

## Estrutura (MVC)

```
app.py              # entry point (python app.py)
seed.py             # dados de exemplo
src/
  app.py            # create_app(): composition root
  config/           # settings lidos do ambiente
  models/           # entidades SQLAlchemy + repositórios (todas as queries)
  controllers/      # regras de negócio, validação, erros de domínio
  views/            # blueprints HTTP finos + serializers
  services/         # adapters de infraestrutura (token, e-mail)
  middlewares/      # error handler central, autenticação
```

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>`; apenas administradores autenticados podem atribuir `role: "admin"` em `POST /users` / `PUT /users/<id>`.
