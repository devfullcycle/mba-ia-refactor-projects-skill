# Análise de Codebase — code-smells-project

> Gerado pela skill `refactor-arch` (Fase 1 — Análise).
> Data: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/code-smells-project`
> Reexecução da Etapa 6: a análise abaixo descreve o codebase **original** (entrada da skill) e permanece válida como contrato de referência. O estado refatorado e as correções do feedback estão em `reports/refactor-code-smells-project.md` e `reports/validation-code-smells-project.md`.

## 1. Resumo

| Campo | Valor |
|---|---|
| Linguagem | Python 3 (versão exata não declarada) |
| Framework | Flask 3.1.1 + Flask-CORS 5.0.1 (declarados e usados) |
| Dependências | `flask==3.1.1`, `flask-cors==5.0.1` |
| Banco de dados | SQLite (stdlib `sqlite3`), arquivo local `loja.db` |
| Domínio | API de E-commerce — produtos, usuários, pedidos e relatório de vendas |
| Arquitetura | Flat / monolítico desestruturado — 4 arquivos na raiz, sem camadas |
| Entrypoint | `app.py` |
| Tamanho | 4 arquivos `.py`, 780 LOC |
| Testes | Nenhum (sem pasta `tests/`, sem framework de teste) |
| Configuração | Hardcoded (`app.py:7-8`, `database.py:5`), sem `.env` |

## 2. Evidências de detecção

### 2.1 Linguagem
- Manifest: `requirements.txt` — `flask==3.1.1`, `flask-cors==5.0.1`.
- Extensões: `.py` = 4 arquivos (`app.py`, `controllers.py`, `database.py`, `models.py`), 780 LOC no total.
- Sintaxe/imports Python em todos os arquivos (`from flask import ...` em `app.py:1`).
- **Veredito:** Python 3 — confiança: alta (manifesto + código + ausência de qualquer outra linguagem).

### 2.2 Framework
- Dependências candidatas: `flask` (framework web), `flask-cors` (middleware CORS).
- Confirmado no código:
  - `app.py:1` — `from flask import Flask, jsonify, request`
  - `app.py:6` — `app = Flask(__name__)`
  - `app.py:9` — `CORS(app)`
  - `app.py:11-30` — `app.add_url_rule(...)` registrando os handlers de `controllers.py`
  - `app.py:32`, `app.py:47`, `app.py:59` — `@app.route(...)` para `/`, `/admin/reset-db`, `/admin/query`
- Servidor: `app.run(host="0.0.0.0", port=5000, debug=True)` (`app.py:88`) — servidor de desenvolvimento do Flask/Werkzeug. Não há `gunicorn`/`uvicorn` no manifesto.
- **Veredito:** Flask 3.1.1 (declarado) — confiança: alta (dependência declarada e confirmada no código).

### 2.3 Banco de dados
- Driver/ORM: `sqlite3` da stdlib (`database.py:1`, `models.py:2`). Não há ORM.
- Conexão: `database.py:10` — `sqlite3.connect(db_path, check_same_thread=False)`.
- Caminho: `database.py:5` — `db_path = "loja.db"` (literal, não configurável por env).
- Schema: DDL inline em `database.py:14-53` (`CREATE TABLE IF NOT EXISTS` para `produtos`, `usuarios`, `pedidos`, `itens_pedido`).
- Seed: `database.py:56-84` insere 10 produtos e 3 usuários no primeiro boot.
- Migrations: ausentes (nenhuma pasta `migrations/` ou `alembic/`).
- **Veredito:** Relacional — SQLite (arquivo local), schema criado em runtime, sem versionamento.

### 2.4 Domínio
- Rotas detectadas (19 endpoints):
  - Produtos: `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`, `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`
  - Usuários: `GET /usuarios`, `GET /usuarios/<id>`, `POST /usuarios`
  - Autenticação: `POST /login`
  - Pedidos: `POST /pedidos`, `GET /pedidos`, `GET /pedidos/usuario/<usuario_id>`, `PUT /pedidos/<pedido_id>/status`
  - Relatórios: `GET /relatorios/vendas`
  - Operação: `GET /health`, `GET /`, `POST /admin/reset-db`, `POST /admin/query`
- Entidades: `produtos`, `usuarios`, `pedidos`, `itens_pedido`.
- **Veredito:** API de E-commerce — catálogo de produtos, cadastro/login de usuários, criação e acompanhamento de pedidos com baixa de estoque, e relatório agregado de vendas.

## 3. Inventário

```
code-smells-project/
├── app.py              (88 LOC)  entrypoint, rotas e endpoints administrativos
├── controllers.py      (292 LOC) handlers HTTP, validação manual e regras de negócio
├── database.py         (86 LOC)  conexão SQLite global, DDL e seed
├── models.py           (314 LOC) SQL bruto, mapeamento de linhas e regras de negócio
├── requirements.txt              flask==3.1.1, flask-cors==5.0.1
├── README.md                     instruções de execução
└── reports/                      relatórios das skills
```

| Linguagem | Arquivos | LOC |
|---|---|---|
| Python | 4 | 780 |

Não há pastas de camada, testes, migrations, CI/CD ou containerização.

## 4. Arquitetura

### 4.1 Classificação
**Rótulo:** Flat / Monolítico desestruturado

**Justificativa:** todos os arquivos de código estão na raiz, sem diretórios de camada (`controllers/`, `services/`, `repositories/`, `config/`). O roteamento vive em `app.py`, os handlers em `controllers.py`, mas ambos concentram lógica de negócio; o acesso a dados e parte das regras de negócio estão misturados em `models.py`; a conexão e o schema estão em `database.py`. Não há camada de serviço, DTO/schema de validação, configuração centralizada nem middleware de erro.

### 4.2 Tabela de camadas

| Camada candidata | Diretório/arquivo | Existe? | Veredito |
|---|---|---|---|
| Model | `models.py` | sim | `papel violado` — mistura SQL bruto (data access), mapeamento para dict e regra de negócio (cálculo de total, baixa de estoque, desconto) |
| Controller | `controllers.py` | sim | `parcial` — recebe request e delega a `models`, mas também valida, decide regra de negócio e dispara notificações |
| View | respostas JSON em `controllers.py` | sim (acoplada) | `parcial` — não há camada de serialização/apresentação; o dict de resposta é montado no handler |
| Service | — | não | `ausente` — casos de uso (`criar_pedido`, `relatorio_vendas`) estão em `models.py` ou `controllers.py` |
| Data access / Repository | — | não | `ausente` — SQL está em `models.py` e também em `app.py:47-78` e `controllers.py:264-290` |
| Config | — | não | `ausente` — segredo, debug e caminho do banco hardcoded (`app.py:7-8`, `database.py:5`) |
| Middleware / error handler | — | não | `ausente` — apenas `CORS(app)`; `try/except` repetido em cada handler |
| Migrations | — | não | `ausente` — DDL inline em `database.py:14-53` |
| Tests | — | não | `ausente` |

### 4.3 Leitura dos arquivos-chave

| Arquivo | LOC | Papel real | Observações |
|---|---|---|---|
| `app.py` | 88 | Entrypoint + tabela de rotas + endpoints administrativos | Registra 17 handlers de `controllers.py`; contém `/admin/reset-db` e `/admin/query` com SQL direto; `SECRET_KEY` e `DEBUG` hardcoded |
| `controllers.py` | 292 | Handlers HTTP + validação + regra de negócio + notificações | Validação manual e duplicada de produto; `print` como log/notificação; `except Exception` genérico em todos os handlers |
| `models.py` | 314 | SQL bruto + mapeamento + regra de negócio | Concatenação de strings em todas as queries; `criar_pedido` calcula total/estoque; `relatorio_vendas` aplica faixas de desconto |
| `database.py` | 86 | Conexão global + DDL + seed | Singleton mutável `db_connection`; `check_same_thread=False`; schema sem FKs/UNIQUE/CHECK |

## 5. Entrypoints, configuração e testes

- **Entrypoints:** `app.py` (`python app.py`, `app.run` na linha 88).
- **Configuração:** hardcoded. `SECRET_KEY` em `app.py:7`, `DEBUG=True` em `app.py:8` e `app.py:88`, caminho do banco em `database.py:5`. Não há `.env`, `.env.example` nem leitura de `os.environ`.
- **Testes:** nenhum. Sem `tests/`, `pytest.ini`, `conftest.py` ou dependência de teste no manifesto.
- **CI/CD:** nenhum workflow em `.github/workflows/`, sem `.gitlab-ci.yml`.
- **Containerização:** sem `Dockerfile`, `docker-compose.yml` ou manifestos de deploy.

## 6. Candidatos a anti-pattern

Achados que a própria leitura de código já revelou. **Não** são o relatório de auditoria — a Fase 2 confirma, classifica severidade e localiza linha exata.

| # | Sinal observado | Evidência | Anti-pattern candidato |
|---|---|---|---|
| 1 | SQL montado por concatenação de strings com entrada do usuário | `models.py:28`, `47-50`, `57-61`, `68`, `92`, `109-111`, `126-129`, `140`, `148-151`, `158-161`, `163-166`, `174`, `188`, `192`, `220`, `224`, `279-281`, `289-299` | SQL Injection |
| 2 | Endpoint executa SQL arbitrário enviado no body | `app.py:59-78` | Execução de SQL arbitrário / RCE via banco |
| 3 | Endpoint apaga todas as tabelas sem autenticação | `app.py:47-57` | Endpoint administrativo sem autorização |
| 4 | Segredo literal no código e exposto em resposta HTTP | `app.py:7`, `controllers.py:289` | Credencial hardcoded / vazamento de segredo |
| 5 | Senhas em texto plano no seed, na comparação de login e na resposta | `database.py:76-78`, `models.py:105-111`, `models.py:79-86`, `models.py:95-102`, `models.py:126-129` | Criptografia fraca / exposição de dados sensíveis |
| 6 | `debug=True` em produção e `ambiente: producao` na resposta | `app.py:8`, `app.py:88`, `controllers.py:286-288` | Configuração insegura |
| 7 | Login não emite token/sessão; rotas não têm autorização | `controllers.py:167-186`; `app.py:11-30` | Autenticação ausente / controle de acesso quebrado |
| 8 | Validação de entrada manual, duplicada e parcial | `controllers.py:30-54`, `74-90`, `153-158` | Validação ausente/inconsistente |
| 9 | `request.get_json()` pode ser `None` e é desreferenciado | `controllers.py:169-170`, `239-240` | Tratamento de entrada frágil (500 em vez de 400) |
| 10 | Sem verificação de tipo em `preco`/`estoque` | `controllers.py:43-46`, `87-90` | Validação de tipo ausente |
| 11 | Regra de negócio no controller (validação, transição de status, notificações) | `controllers.py:24-96`, `208-210`, `237-255` | Lógica de negócio no Controller |
| 12 | Regra de negócio no model (total, estoque, desconto) | `models.py:133-169`, `256-262` | Model com responsabilidades excessivas |
| 13 | Loop com query interna por pedido/item | `models.py:176-201`, `208-233` | N+1 queries |
| 14 | Consultas sem paginação e sem filtro de `ativo` | `models.py:4-22`, `72-87`, `203-233` | Full table scan / listagem sem paginação |
| 15 | Conexão global mutável com `check_same_thread=False` | `database.py:4`, `8-10` | Estado global mutável / concorrência insegura |
| 16 | Checagem de estoque seguida de update não atômico | `models.py:139-166` | Race condition / falta de transação |
| 17 | `except Exception` genérico devolvendo `str(e)` ao cliente | `controllers.py:10-12`, `21-22`, `60-62`, `95-96`, `108-109`, `125-126`, `164-165`, `185-186`, `218-220`, `226-227`, `234-235`, `254-255`, `261-262`, `291-292`; `app.py:77-78` | Tratamento de erro genérico / vazamento de detalhes internos |
| 18 | Código duplicado entre criar/atualizar produto e entre listagens de pedidos | `controllers.py:24-62` vs `64-96`; `models.py:171-201` vs `203-233` | Duplicação de código |
| 19 | Lista de status e de categorias repetida em pontos distintos | `controllers.py:52`, `controllers.py:242`, `models.py:40` | Magic strings / regra duplicada |
| 20 | DDL inline sem migrations, sem FKs, UNIQUE ou CHECK | `database.py:14-53` (email sem UNIQUE na linha 30; `usuario_id`/`pedido_id`/`produto_id` sem FK nas linhas 39, 48-50) | Schema sem versionamento / integridade referencial ausente |
| 21 | `print` usado como log e como integração de notificação | `controllers.py:8`, `11`, `57`, `61`, `106`, `161`, `179`, `182`, `208-210`, `219`, `248`, `250`; `app.py:56`, `83-86` | Logging inadequado / integração simulada |
| 22 | Email do usuário logado em texto plano | `controllers.py:179`, `182` | Exposição de PII em log |
| 23 | Imports não utilizados | `database.py:2` (`os`), `models.py:2` (`sqlite3`) | Dependência/import morto |
| 24 | `SECRET_KEY` definida mas sem uso de sessão/token | `app.py:7` | Configuração morta |

## 7. Notas e lacunas

- **Versão do Python** não está declarada (sem `.python-version`, `runtime.txt` ou `python_requires`). O código é compatível com Python 3; a versão exata exigiria executar o interpretador, o que não foi feito.
- **Versões em runtime** de Flask/Flask-CORS não foram verificadas por import; as versões citadas são as declaradas em `requirements.txt`.
- **Banco `loja.db`** não existe no diretório no momento da análise — é criado no primeiro boot (`database.py:7-10`). Não foi possível inspecionar dados reais além do seed.
- **Estado do Git:** `reports/analysis-code-smells-project.md` consta como deletado no working tree (`git status`), mas existe no histórico. Este relatório foi gerado do zero a partir do código atual; não houve sobrescrita de arquivo existente.
- **Fora de escopo desta fase:** não foram executados boot, testes ou chamadas HTTP. A ausência de testes e de CI foi verificada por estrutura de arquivos e manifesto.
- As referências da skill cobrem o ecossistema Python/Flask sem lacunas relevantes.
