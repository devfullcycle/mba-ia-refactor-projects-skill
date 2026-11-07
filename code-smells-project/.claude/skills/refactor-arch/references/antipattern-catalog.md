# Anti-Pattern Catalog (Fase 2)

Catálogo agnóstico de tecnologia. Cada entrada traz **sinais de detecção**
acionáveis (o que procurar no código) e a **severidade** padrão. Ajuste a
severidade ao contexto quando houver agravante/atenuante, mas justifique.

## Escala de severidade

- **CRITICAL** — Falha grave de arquitetura ou segurança: impede o
  funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL
  Injection) ou viola completamente a separação de responsabilidades (God
  Class com banco + lógica + roteamento no mesmo arquivo).
- **HIGH** — Forte violação de MVC/SOLID que dificulta muito manutenção e
  testes: regra de negócio presa no controller/rota, forte acoplamento sem
  injeção de dependência, estado global mutável em toda a app.
- **MEDIUM** — Padronização, duplicação ou performance moderada: queries N+1,
  uso inadequado de middlewares, validação ausente nas rotas, serialização
  duplicada.
- **LOW** — Legibilidade: nomes ruins, magic numbers, prints de debug, imports
  mortos.

---

## Catálogo

### AP-01 · God Class / God File — **CRITICAL**
Um único arquivo/classe concentra roteamento, regra de negócio, acesso a dados
e formatação para múltiplos domínios.
**Sinais:** arquivo com centenas de linhas e dezenas de funções de domínios
diferentes; uma classe `Manager`/`Service` que faz tudo; SQL + HTTP + regras no
mesmo escopo.
**Impacto:** impossível testar isoladamente; qualquer mudança arrisca tudo.

### AP-02 · Hardcoded Secrets / Credentials — **CRITICAL**
Segredos embutidos no código-fonte.
**Sinais:** `SECRET_KEY = "..."`, `password = "..."`, `apiKey`/`pk_live_...`,
senhas de DB/SMTP, tokens literais; o mesmo segredo repetido em respostas de
API (ex.: `/health` devolvendo a secret).
**Impacto:** vazamento de credenciais, comprometimento total em caso de leak do
repositório. **Correção:** mover para variáveis de ambiente (`.env` + `.env.example`).

### AP-03 · SQL Injection / Query por concatenação — **CRITICAL**
Queries montadas por concatenação/interpolação de input do usuário.
**Sinais:** `"SELECT ... WHERE id = " + str(id)`, f-strings/template literals
dentro de `execute(...)`, `LIKE '%" + termo + "%'`. Um endpoint que executa SQL
arbitrário vindo do body também entra aqui.
**Impacto:** leitura/escrita arbitrária no banco. **Correção:** queries
parametrizadas / ORM.

### AP-04 · Senha em texto puro ou hash fraco — **CRITICAL**
Senhas armazenadas/comparadas sem hashing forte, ou devolvidas em respostas.
**Sinais:** coluna `senha`/`pass` guardando o valor cru; `md5`/`sha1`/base64
"caseiro" como "criptografia"; `to_dict()` expondo o campo de senha.
**Impacto:** exposição de credenciais de usuários. **Correção:** `bcrypt`/
`argon2`/`scrypt`; nunca serializar o hash.

### AP-05 · Fat Controller / Regra de negócio na camada HTTP — **HIGH**
Controller/rota contém regra de negócio pesada (cálculos, orquestração de
múltiplos passos, efeitos colaterais) em vez de delegar.
**Sinais:** rota com dezenas de linhas de `if`, cálculo de totais/descontos,
disparo de e-mail/SMS, montagem de relatório direto no handler.
**Impacto:** não reusável, não testável sem HTTP. **Correção:** extrair para
service/model.

### AP-06 · Estado global mutável — **HIGH**
Conexão/cache/contadores guardados em variável global mutável compartilhada.
**Sinais:** `db_connection = None` global reusado entre requests; `globalCache
= {}`, `totalRevenue = 0` em escopo de módulo; singletons mutáveis sem controle.
**Impacto:** condições de corrida, vazamento de estado entre requisições,
acoplamento forte. **Correção:** injeção de dependência / factory por request.

### AP-07 · Missing Dependency Injection / Acoplamento forte — **HIGH**
Módulos instanciam suas próprias dependências e importam umas às outras
diretamente, sem inversão de controle.
**Sinais:** `import models` + `from database import get_db` espalhados;
`new Sqlite3.Database(...)` dentro da classe que também trata HTTP; impossível
trocar o banco/serviço sem editar o consumidor.
**Impacto:** baixa testabilidade (não dá pra mockar), rigidez. **Correção:**
receber dependências por parâmetro/construtor.

### AP-08 · Callback Hell / Async mal estruturado — **HIGH**
Lógica assíncrona aninhada em pirâmide, com fluxo de erro espalhado.
**Sinais:** callbacks dentro de callbacks dentro de callbacks; contadores
manuais (`pending--`) para saber quando terminou; `res.send` repetido em cada
nível. **Impacto:** ilegível, propenso a bugs de concorrência e respostas
duplicadas. **Correção:** `async/await` + Promises, ou camada de repositório.

### AP-09 · Query N+1 — **MEDIUM**
Uma query por item dentro de um loop.
**Sinais:** `for item in itens: cursor.execute("SELECT ... WHERE id = "+...)`;
`User.query.get(t.user_id)` dentro de loop sobre tasks; múltiplos
`db.get(...)` encadeados por registro.
**Impacto:** degradação de performance proporcional ao volume. **Correção:**
join / `IN (...)` / eager loading.

### AP-10 · Validação ausente ou duplicada nas rotas — **MEDIUM**
Validação de input inexistente, ou a mesma validação copiada em vários
handlers.
**Sinais:** rota que confia no body sem checar; blocos idênticos de
`if not x: return 400` repetidos em create/update; validação de status/prioridade
duplicada em model, rota e util.
**Impacto:** inconsistência, bugs, retrabalho. **Correção:** schema/validador
central ou camada de validação única.

### AP-11 · Código duplicado / Serialização manual repetida — **MEDIUM**
O mesmo bloco de montagem de dicionário/DTO repetido em vários lugares.
**Sinais:** o mesmo `{"id": row["id"], "nome": ...}` em várias funções; lógica
`is_overdue` reimplementada inline em 3 rotas; funções `get_todos_*` quase
idênticas. **Impacto:** divergência silenciosa quando um lugar muda.
**Correção:** método `to_dict()`/serializer único e reuso.

### AP-12 · Endpoint administrativo perigoso / sem proteção — **CRITICAL**
Rota que executa operação destrutiva ou arbitrária sem autenticação.
**Sinais:** `/admin/reset-db` que apaga tabelas; `/admin/query` que roda SQL do
body; `DELETE` que deixa dados órfãos. **Impacto:** destruição ou dump total do
banco por qualquer um. **Correção:** remover ou proteger com auth + escopo
restrito; usar deleção em cascata consistente.

### AP-13 · API / Método deprecated — **MEDIUM** (CRITICAL se já removida)
Uso de APIs obsoletas que já têm substituto moderno. **Sempre cheque esta
categoria** e recomende o equivalente atual.
**Sinais e substitutos comuns:**
| Deprecated | Equivalente moderno |
|---|---|
| `datetime.utcnow()` (deprecated no Python 3.12+) | `datetime.now(datetime.UTC)` |
| `Model.query.get(id)` (legacy no SQLAlchemy 2.x) | `db.session.get(Model, id)` |
| `Query.get()` / `Query` style antigo | API 2.0 `select()` |
| `datetime.strptime` sem tz p/ dados UTC | timezone-aware |
| `url_for` com `_external` mal usado, `before_first_request` (removido no Flask 2.3) | `with app.app_context()` no startup |
| `new Buffer()` (Node) | `Buffer.from()` |
| `crypto` MD5/SHA1 para senha | `bcrypt`/`argon2` |
| `request.get_json()` sem `silent`/`force` tratados | validar `None` |
| Callbacks de `sqlite3`/libs antigas | versão baseada em Promise/`util.promisify` |
Reporte arquivo:linha e o substituto recomendado.

### AP-14 · Error handling espalhado / engolido — **MEDIUM**
`try/except` genérico copiado em cada handler, ou exceções silenciadas.
**Sinais:** `except:` ou `except Exception as e: return 500` em toda função;
`catch` vazio; retorno de `str(e)` ao cliente (vaza stack). **Impacto:**
diagnóstico difícil, vazamento de detalhes internos. **Correção:**
middleware/error handler centralizado.

### AP-15 · Debug prints / logging improvisado — **LOW**
`print(...)`/`console.log(...)` como log de produção.
**Sinais:** `print("ENVIANDO EMAIL...")`, `console.log(\`Processando cartão...\`)`
(pior: logando dado sensível), prints de debug no fluxo normal.
**Impacto:** ruído, possível vazamento de PII em logs. **Correção:** logger
configurável por nível.

### AP-16 · Magic numbers / Strings mágicas — **LOW**
Valores literais sem nome espalhados pela lógica.
**Sinais:** `10000`/`0.1` em cálculo de desconto; faixas de prioridade `1..5`,
listas de status repetidas inline; portas/limites fixos no meio do código.
**Impacto:** intenção obscura, mudança arriscada. **Correção:** constantes
nomeadas / config.

### AP-17 · DEBUG habilitado em produção — **HIGH**
App servida com modo debug/auto-reload ligado.
**Sinais:** `app.config["DEBUG"] = True`, `app.run(debug=True)`, `host="0.0.0.0"`
com debug. **Impacto:** execução remota de código via debugger, stack traces
expostos. **Correção:** controlar por env (`FLASK_DEBUG`), default desligado.

### AP-18 · Lógica de domínio em util/helper genérico — **MEDIUM**
"Pasta de tranqueira" (`utils/helpers.py`) acumulando regras de negócio que
deveriam estar em models/services.
**Sinais:** `process_task_data()`, validações de negócio e constantes de domínio
num `helpers`; imports não usados no topo (`os, sys, math`). **Impacto:**
responsabilidade difusa, difícil achar a regra. **Correção:** mover regra para a
camada correta.

---

## Como usar na Fase 2

1. Para cada arquivo-fonte, varra os sinais acima.
2. Registre cada ocorrência com **arquivo:linha** exatos.
3. Classifique pela severidade (ajuste com justificativa se o contexto pedir).
4. Garanta **≥ 5 findings** e **≥ 1 CRITICAL/HIGH**; inclua a checagem de
   **APIs deprecated** (AP-13).
5. Agrupe findings equivalentes repetidos, mas mantenha as linhas de cada
   ocorrência.
