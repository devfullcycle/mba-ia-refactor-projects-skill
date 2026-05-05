# Guidelines — padrão MVC alvo

## Definições

- **Model:** acesso a dados e invariantes de persistência (ORM/repositório/SQL parametrizado). Sem conhecimento de HTTP.
- **View (API):** camada HTTP “fina” — rotas, parsing de query/body, status codes, serialização. Em Flask: Blueprints ou módulo `views/`; em Express: `routes/` + handlers que **só** delegam.
- **Controller (caso de uso):** orquestra models e regras de aplicação para **um** fluxo (ex.: “criar pedido”, “checkout”). Sem SQL concatenado; sem detalhes de `request`/`response` além de DTOs simples.

## Composition root

- Um **entry point** (`app.py`, `src/app.js`) que:
  - carrega **config** (env)
  - inicializa DB
  - registra rotas
  - registra **error handler** global

## Config e segurança

- **Sem** `SECRET_KEY`, tokens de gateway, senhas SMTP ou strings `pk_live_` no código versionado.
- Use `os.environ` / `process.env` com valores default apenas para desenvolvimento **não secretos** (ex.: porta).

## Error handling

- Flask: `@app.errorhandler` ou blueprint de erros JSON consistente `{ "error": "..." }`.
- Express: middleware `(err, req, res, next)` no final da cadeia.

## Testabilidade

- Controllers recebem dependências (DB/repo) por **factory** ou parâmetros quando possível; evitar singleton global mutável para estado de negócio.

## Nomenclatura de pastas (sugestão)

```
src/
  config/
  models/        # ou repositories/
  controllers/
  views/         # rotas / blueprints
  middlewares/
app.py / src/app.js
```

Adaptar ao projeto: o importante é **responsabilidade**, não o nome exato da pasta.
