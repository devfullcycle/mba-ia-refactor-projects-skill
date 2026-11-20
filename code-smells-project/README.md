# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Todas as configurações vêm de variáveis de ambiente — veja `.env.example` (`SECRET_KEY`, `ADMIN_TOKEN`, `FLASK_DEBUG`, `HOST`, `PORT`, `DATABASE_PATH`, `APP_ENV`, `CORS_ORIGINS`). Por padrão o servidor escuta em `127.0.0.1` com debug desligado.

Os endpoints `/admin/*` exigem o cabeçalho `X-Admin-Token` igual a `ADMIN_TOKEN` (sem `ADMIN_TOKEN` definido eles respondem 403). `/admin/query` aceita apenas uma única consulta `SELECT`, executada em modo somente leitura.

## Estrutura (MVC)

```
app.py               # entrada: python app.py
src/app.py           # create_app(): composition root
src/config/          # settings via variáveis de ambiente
src/models/          # conexão, schema/seed e repositórios (SQL parametrizado)
src/controllers/     # regras de negócio, validação e erros de domínio
src/views/           # blueprints Flask (rotas finas)
src/services/        # notificações e hash de senha
src/middlewares/     # tratamento de erros e autenticação admin
```
