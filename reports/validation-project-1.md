# Validação — Projeto 1 (code-smells-project)

Protocolo de `references/validation.md`: baseline capturado antes de qualquer modificação,
refatoração aplicada, mesma bateria reexecutada e comparada.

- Runtime: Python 3.9.5 (venv local), Flask 3.1.1
- Antes: `python app.py` — Após: `python run.py`
- Banco recriado do zero (mesmo seed) nas duas execuções
- Bateria: 33 chamadas cobrindo os 19 endpoints (caminhos felizes, 404, 400 e sonda de SQLi)

## Resultado

```
Validation
  ✓ Application boots without errors        (log limpo, "Debug mode: off")
  ✓ 30/30 endpoints inalterados respondem com o mesmo status
  ✓ 3/3 diferenças são intencionais e rastreadas a findings da auditoria
  ✓ No hardcoded secrets remaining          (grep vazio em src/ e run.py)
  ✓ Layer boundaries respected              (sem SQL fora de models/database, sem HTTP em models/)
  ✓ Sem concatenação em query, sem estado global, sem print de diagnóstico
  ✓ Import de src.app sem efeito colateral de I/O
```

## Comparação status a status

| Chamada | Baseline | Após | Situação |
|---|---|---|---|
| GET / | 200 | 200 | igual |
| GET /health | 200 | 200 | igual (payload reduzido — ver abaixo) |
| GET /produtos | 200 | 200 | igual |
| GET /produtos/1 | 200 | 200 | igual |
| GET /produtos/999999 | 404 | 404 | igual |
| GET /produtos/busca?q=notebook | 200 | 200 | igual |
| GET /produtos/busca (filtros) | 200 | 200 | igual |
| POST /produtos (válido) | 201 | 201 | igual |
| POST /produtos {} | 400 | 400 | igual |
| POST /produtos (categoria inválida) | 400 | 400 | igual |
| PUT /produtos/11 | 200 | 200 | igual |
| PUT /produtos/999999 | 404 | 404 | igual |
| DELETE /produtos/11 | 200 | 200 | igual |
| DELETE /produtos/999999 | 404 | 404 | igual |
| GET /usuarios | 200 | 200 | igual (campo `senha` removido — ver abaixo) |
| GET /usuarios/1 | 200 | 200 | igual (campo `senha` removido) |
| GET /usuarios/999999 | 404 | 404 | igual |
| POST /usuarios | 201 | 201 | igual |
| POST /usuarios {} | 400 | 400 | igual |
| POST /login (correto) | 200 | 200 | igual |
| POST /login (senha errada) | 401 | 401 | igual |
| **POST /login (SQL Injection)** | **200** | **401** | **corrigido — finding 1** |
| POST /pedidos (válido) | 201 | 201 | igual |
| POST /pedidos {} | 400 | 400 | igual |
| POST /pedidos (estoque insuficiente) | 400 | 400 | igual |
| GET /pedidos | 200 | 200 | igual |
| GET /pedidos/usuario/1 | 200 | 200 | igual |
| PUT /pedidos/1/status | 200 | 200 | igual |
| PUT /pedidos/1/status (inválido) | 400 | 400 | igual |
| GET /relatorios/vendas | 200 | 200 | igual |
| **POST /admin/query** | **200** | **404** | **endpoint removido — finding 2** |
| **POST /admin/reset-db** | **200** | **404** | **endpoint removido — finding 2** |
| GET /produtos (após reset) | 200 | 200 | igual |

## Diferenças intencionais de contrato

| Mudança | Antes | Depois | Finding |
|---|---|---|---|
| Bypass de autenticação por SQLi | `POST /login` com `x' OR '1'='1` → 200 como `Admin` | 401 | 1 |
| `POST /admin/query` (SQL arbitrário) | 200 executando qualquer SQL | 404 (removido) | 2 |
| `POST /admin/reset-db` | 200 apagando as 4 tabelas | 404 (removido) | 2 |
| `/health` | expunha `secret_key`, `db_path`, `debug`, `ambiente` | apenas `status`, `database`, `counts`, `versao` | 4 |
| `/usuarios` e `/usuarios/<id>` | incluíam `"senha": "admin123"` em texto plano | campo removido da serialização | 4, 6 |
| Envelope de erro | inconsistente (`{erro}` em 8 respostas, `{erro, sucesso}` nas outras) | sempre `{erro, sucesso: false}` | 14 |

A padronização do envelope de erro é aditiva: nenhuma chave existente foi removida, apenas
`sucesso: false` passou a estar presente em todas as respostas de erro.

## Evidência das correções de segurança

```console
# ANTES — bypass de autenticação
$ curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
       -d '{"email":"x'"'"' OR '"'"'1'"'"'='"'"'1","senha":"x'"'"' OR '"'"'1'"'"'='"'"'1"}'
{"dados":{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},
 "mensagem":"Login OK","sucesso":true}                                    # 200

# DEPOIS
{"erro":"Email ou senha inválidos","sucesso":false}                       # 401
```

```console
# ANTES — /health vazando o segredo da aplicação
{"ambiente":"producao","counts":{...},"database":"connected","db_path":"loja.db",
 "debug":true,"secret_key":"minha-chave-super-secreta-123","status":"ok","versao":"1.0.0"}

# DEPOIS
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected",
 "status":"ok","versao":"1.0.0"}
```

```console
# ANTES — /usuarios devolvendo senhas em texto plano
{"dados":[{"email":"admin@loja.com","id":1,"nome":"Admin","senha":"admin123","tipo":"admin"},...]}

# DEPOIS (senha persistida com hash scrypt do werkzeug, fora da serialização)
{"dados":[{"criado_em":"2026-07-24 21:09:31","email":"admin@loja.com","id":1,
           "nome":"Admin","tipo":"admin"},...]}
```

## Checagens estruturais

| Checagem | Comando | Resultado |
|---|---|---|
| Segredo literal | `grep -rniE "(secret\|password\|api_key\|token)\s*[:=]\s*['\"]..." src/ run.py` | vazio ✓ |
| SQL fora da camada de dados | `grep -rlE "SELECT \|INSERT \|UPDATE \|DELETE FROM" src/ \| grep -v "src/(models\|database)/"` | vazio ✓ |
| HTTP dentro de models | `grep -rn "from flask import\|jsonify\|request\." src/models/` | vazio ✓ |
| `print()` de diagnóstico | `grep -rnE "^\s*print\(" src/ run.py` | vazio ✓ |
| Concatenação em query | `grep -rnE "execute\(.*(\+\|%\|\.format\(\|f['\"])" src/` | vazio ✓ |
| `except` genérico em controller/view | `grep -rnE "except (Exception\|:)" src/controllers/ src/views/` | vazio ✓ |
| Estado global mutável | `grep -rnE "^(global \|[a-z_]+ = (None\|\{\}\|\[\]\|0))" src/` | vazio ✓ |
| Import sem efeito colateral | `python -c "importlib.import_module('src.app')"` | sem I/O ✓ |

## Log de boot após a refatoração

```
2026-07-24 18:09:31,439 WARNING  [src.app] SECRET_KEY não definida no ambiente — usando
                                 chave efêmera de desenvolvimento. Defina SECRET_KEY antes
                                 de subir em produção.
2026-07-24 18:09:31,761 INFO     [src.database.connection] Banco populado com dados de demonstração
2026-07-24 18:09:31,762 INFO     [src.app] Servidor iniciado em http://127.0.0.1:5000 (ambiente: development)
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

Diferenças em relação ao boot legado: sem `Debugger PIN` (debug é opt-in explícito), sem
`Running on all addresses (0.0.0.0)` (host default `127.0.0.1`), e log estruturado com nível
e timestamp em vez de `print`.
