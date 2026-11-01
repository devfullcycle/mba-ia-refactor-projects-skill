# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
export SECRET_KEY="troque-por-uma-chave-gerada"
export ADMIN_TOKEN="troque-por-um-token-administrativo"
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo.

Variáveis relevantes: `SECRET_KEY` (assina os tokens de sessão),
`TOKEN_MAX_AGE_SECONDS` (validade do token, padrão 8h) e `ADMIN_TOKEN` (token
estático para `POST /admin/reset-db`).

## Autenticação e autorização

`POST /login` devolve um `token` assinado. Envie-o como
`Authorization: Bearer <token>` nas rotas de escrita:

| Rota | Nível exigido |
|---|---|
| `POST`/`PUT`/`DELETE /produtos` | `admin` |
| `POST /pedidos` | `cliente` (apenas para o próprio `usuario_id`) |
| `PUT /pedidos/<id>/status` | `admin` |
| `POST /admin/reset-db` | `ADMIN_TOKEN` estático |

Sem token (ou com token inválido/expirado) a resposta é `401`; com token de
nível insuficiente é `403`. Usuários do seed:

| E-mail | Senha | Nível |
|---|---|---|
| `admin@loja.com` | `admin123` | `admin` |
| `joao@email.com` | `123456` | `cliente` |
| `maria@email.com` | `senha123` | `cliente` |

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}' | jq -r .token)

curl -X POST http://localhost:5000/produtos \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"nome":"Mouse","preco":89.9,"estoque":10,"categoria":"informatica"}'
```

## Teste de contrato

```bash
python tests/smoke_contract.py
```
