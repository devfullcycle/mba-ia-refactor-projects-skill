# Catálogo de Anti-Patterns

19 anti-patterns com sinais de detecção acionáveis. Cada um aponta o padrão de transformação
correspondente em `refactor-playbook.md`.

## Escala de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha de segurança ou de arquitetura que expõe dado sensível, permite bypass/execução indevida, corrompe dados, ou viola completamente a separação de responsabilidades (God Class com banco + regra + rota no mesmo arquivo). |
| **HIGH** | Violação forte de MVC/SOLID que inviabiliza teste e manutenção: regra de negócio pesada presa no controller/rota, acoplamento sem injeção de dependência, estado global mutável, escrita multi-tabela sem transação. |
| **MEDIUM** | Padronização, duplicação e performance moderada: N+1, exceção engolida, validação ausente, middleware mal usado, API deprecated em uso corrente. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, código morto, import não usado, `if/else` que devolve booleano. |

**Ajuste de severidade pelo contexto** (declare o motivo no finding):
- ↑ Sobe um nível: o trecho está em caminho de autenticação, pagamento ou rota administrativa
  sem proteção; ou o dado afetado é credencial/PII.
- ↓ Desce um nível: o código é comprovadamente inalcançável (dead code), ou é script de
  seed/teste local que não sobe em produção.
- Ocorrência isolada de `print` é LOW; `print` como *única* estratégia de log em toda a
  aplicação é MEDIUM. Vale o mesmo raciocínio para duplicação: 2 cópias = LOW, sistêmica = MEDIUM.

## Como usar este catálogo

1. Percorra os anti-patterns na ordem (CRITICAL → LOW).
2. Rode os sinais de detecção. **Todo grep é ponto de partida, não prova** — abra o trecho e
   confirme antes de registrar.
3. Agrupe ocorrências do mesmo anti-pattern no mesmo arquivo em **um** finding com a lista de
   linhas. Arquivos diferentes ⇒ findings diferentes.
4. Confira a seção "Falsos positivos" antes de reportar.

---

## CRITICAL

### AP-01 — God Class / God Module
**Definição:** um arquivo ou classe concentra camadas que deveriam estar separadas: acesso a
dados, regra de negócio, roteamento e formatação de resposta.

**Sinais:**
- Arquivo-fonte com mais de ~250 linhas contendo SQL/ORM **e** resposta HTTP **e** validação.
- Classe que abre conexão de banco no construtor e registra rotas em outro método.
- Um único arquivo cobrindo 3+ agregados de domínio (produtos, usuários, pedidos...).
- Matriz de responsabilidades da Fase 1 com 3+ ✓ na mesma linha.

```bash
# tamanho por arquivo
find . -name '*.py' -o -name '*.js' | grep -vE "node_modules|\.venv" | xargs wc -l | sort -rn | head -10
# arquivo que mistura persistência e HTTP
grep -lE "SELECT |INSERT |UPDATE |\.query\(|db\.(run|get|all)" -r --include='*.py' --include='*.js' . | xargs grep -lE "jsonify|res\.(send|json|status)|return.*Response"
```

**Falsos positivos:** arquivo grande de migração/seed/fixture, ou model ORM extenso porém com
responsabilidade única.

**Impacto:** impossível testar em isolamento; qualquer mudança arrisca todos os domínios.
**Playbook:** RP-01.

### AP-02 — Credenciais e Segredos Hardcoded
**Definição:** senha, chave de API, token ou secret key literal no código-fonte.

**Sinais:**
```bash
grep -rniE "(secret|password|passwd|pwd|api_?key|token|private_key|gateway_?key|smtp_?pass)[[:space:]]*[:=][[:space:]]*['\"][^'\"]{3,}" --include='*.*' . | grep -vE "node_modules|\.env\.example|process\.env|os\.environ|getenv"
# prefixos de chave real
grep -rnE "(sk|pk)_(live|test)_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----" . | grep -v node_modules
# URL de conexão com credencial embutida
grep -rnE "(postgres|postgresql|mysql|mongodb(\+srv)?)://[^:/@]+:[^@]+@" . | grep -v node_modules
```

**Falsos positivos:** `.env.example`, fixtures de teste com valor obviamente falso, e o
*nome* da variável de ambiente (`os.environ["SECRET_KEY"]` é o padrão correto).

**Agravante que sobe o finding:** o mesmo segredo aparecer em resposta HTTP (ver AP-03) ou em
log (ver AP-04).

**Impacto:** segredo versionado no Git vale como comprometido — rotação obrigatória.
**Playbook:** RP-02.

### AP-03 — Dado Sensível Exposto na Resposta da API
**Definição:** senha (mesmo com hash), secret key, configuração interna ou stacktrace
devolvidos ao cliente.

**Sinais:**
- Serializador (`to_dict`, `toJSON`, `serialize`, `__dict__`, `SELECT *` → dict) que inclui
  campo de senha/hash/token.
- Endpoint de health/status devolvendo `secret_key`, caminho de banco, flag de debug.
- `SELECT *` numa tabela de usuários com o resultado repassado direto ao cliente.

```bash
grep -rnE "['\"]?(password|passwd|senha|pass|hash|secret|token)['\"]?[[:space:]]*:" --include='*.py' --include='*.js' . | grep -viE "input|body|req\.|request\.|data\.get" | grep -v node_modules
grep -rn "to_dict\|toJSON\|serialize" --include='*.py' --include='*.js' . | grep -v node_modules
```

**Falsos positivos:** campo de senha no *request* de entrada (esperado); token de sessão
legítimo emitido no login.

**Impacto:** vazamento em massa de credenciais por endpoint público.
**Playbook:** RP-04.

### AP-04 — SQL Injection por Concatenação
**Definição:** query montada por concatenação/interpolação de entrada do usuário.

**Sinais:**
```bash
# concatenação com + em Python
grep -rnE "(execute|executemany)\(.*(\+|%|\.format\(|f['\"])" --include='*.py' . 
# template string em JS
grep -rnE "(query|run|get|all|execute)\(\s*[\`\"'].*(\\$\{|['\"][[:space:]]*\+)" --include='*.js' --include='*.ts' . | grep -v node_modules
# construção incremental de WHERE
grep -rnE "query[[:space:]]*\+=|sql[[:space:]]*\+=" . | grep -v node_modules
```
Confirme que o valor concatenado vem de request/params/body — se vier de constante interna, a
severidade cai para MEDIUM (má prática, sem vetor).

**Falsos positivos:** placeholders reais (`?`, `%s`, `:nome`, `$1`) passados como segundo
argumento; nome de tabela interpolado a partir de whitelist.

**Impacto:** bypass de autenticação, leitura e destruição de dados.
**Playbook:** RP-03.

### AP-05 — Autenticação / Criptografia Inadequada
**Definição:** senha em texto plano, hash inadequado (MD5, SHA1, sem salt), cripto caseira,
token previsível, senha default.

**Sinais:**
```bash
grep -rniE "md5|sha1|base64.*(pass|pwd|senha)|hashlib\.(md5|sha1)|createHash\(['\"](md5|sha1)" . | grep -v node_modules
grep -rniE "password[[:space:]]*==|senha[[:space:]]*==|pass[[:space:]]*===" . | grep -v node_modules
grep -rniE "fake.?(jwt|token)|token['\"][[:space:]]*[:=][[:space:]]*['\"].*\+|default.?password|['\"]123456?['\"]" . | grep -v node_modules
```
- INSERT de usuário sem nenhuma função de hash no caminho.
- Comparação de senha dentro do próprio SQL (`WHERE senha = '...'`).
- Função de hash escrita à mão (laço concatenando base64/charcode).

**Falsos positivos:** MD5/SHA1 usados para checksum de arquivo ou cache key (não para senha).

**Impacto:** base de credenciais efetivamente aberta.
**Playbook:** RP-04.

### AP-06 — Endpoint Perigoso ou Administrativo sem Proteção
**Definição:** rota que executa SQL/comando arbitrário, reseta banco, ou expõe dado
administrativo, sem autenticação nem autorização.

**Sinais:**
```bash
# rotas admin/debug/internas
grep -rnE "(route|get|post|put|delete)\(['\"][^'\"]*(admin|debug|internal|reset|drop|truncate|query|exec|eval|sql)" --include='*.py' --include='*.js' . | grep -v node_modules
# execução de entrada do usuário
grep -rnE "execute\((request|req|dados|data|body)|eval\(|exec\(|child_process" . | grep -v node_modules
```
- Nenhum decorator/middleware de auth no projeto inteiro (`grep -rn "login_required\|authenticate\|jwt\|passport\|@UseGuards"` volta vazio) enquanto existem rotas de escrita/administração.

**Falsos positivos:** rota protegida por middleware global registrado em outro arquivo —
verifique antes de reportar.

**Impacto:** administração remota anônima da aplicação e do banco.
**Playbook:** RP-08, RP-14.

---

## HIGH

### AP-07 — Fat Controller / Regra de Negócio na Camada de Apresentação
**Definição:** handler de rota (ou controller) que valida, aplica regra de negócio, monta
query e serializa resposta.

**Sinais:**
- Handler com mais de ~30 linhas, ou com 5+ `if` de validação sequencial.
- SQL/ORM chamado dentro do handler.
- Cálculo de domínio (total, desconto, "está atrasado", agregação de relatório) inline no handler.
- Laço percorrendo entidades e montando dicionário de resposta dentro do handler.

```bash
# handlers longos: liste as rotas e meça a distância até a próxima
grep -rnE "@(app|bp|router)[a-z_]*\.(route|get|post|put|delete)|\b(app|router)\.(get|post|put|delete)\(" --include='*.py' --include='*.js' . | grep -v node_modules
# regra de negócio dentro do handler
grep -rnE "(if|for).*(status|total|price|preco|priority|overdue|estoque|revenue)" --include='*.py' --include='*.js' . | grep -v node_modules
```

**Falsos positivos:** controller "magro" que só delega, com muitas linhas por causa de
argumentos formatados.

**Impacto:** regra intestável sem cliente HTTP; duplicação inevitável entre endpoints.
**Playbook:** RP-05.

### AP-08 — Ausência de Camada de Dados (SQL/ORM espalhado)
**Definição:** persistência acessada direto da rota/controller, sem model ou repository.

**Sinais:** mesma tabela consultada em 2+ arquivos que não são da camada de dados; ausência de
qualquer arquivo cuja responsabilidade única seja acesso a dados; mapeamento manual
`row → dict` repetido.

```bash
grep -rlE "SELECT |INSERT |UPDATE |DELETE FROM|\.query\.|db\.session|db\.(run|get|all)" --include='*.py' --include='*.js' . | grep -v node_modules
```

**Impacto:** mudança de schema exige caçar SQL em todo o projeto.
**Playbook:** RP-01, RP-03.

### AP-09 — Estado Global Mutável
**Definição:** variável de módulo mutável compartilhada entre requisições — conexão
singleton, cache global, contador, config mutável.

**Sinais:**
```bash
grep -rnE "^(global |let |var )[a-zA-Z_]+ *= *(\{\}|\[\]|0|None|null)|^[a-z_]+ = None$" --include='*.py' --include='*.js' . | grep -v node_modules
grep -rn "global " --include='*.py' . 
grep -rn "check_same_thread=False\|globalCache\|singleton" . | grep -v node_modules
```
- Conexão de banco criada por efeito colateral do primeiro acesso (`if conn is None: conn = ...`).
- Cache em dicionário de módulo sem TTL nem limite.

**Falsos positivos:** constante imutável de módulo (config congelada, enum, `Object.freeze`).

**Impacto:** impede DI e teste isolado; corrida em concorrência; vazamento de memória; quebra
com múltiplas instâncias/workers.
**Playbook:** RP-06.

### AP-10 — Escrita Multi-tabela sem Transação
**Definição:** duas ou mais escritas relacionadas sem fronteira transacional nem rollback —
falha no meio deixa dados inconsistentes.

**Sinais:**
- 2+ INSERT/UPDATE/DELETE na mesma função sem `begin`/`commit` único ou sem `rollback` no erro.
- `commit()` dentro de laço.
- Delete de entidade pai sem cascade nem remoção dos filhos (registros órfãos).

```bash
grep -rnE "commit\(\)" --include='*.py' --include='*.js' . | grep -v node_modules
grep -rniE "rollback" . | grep -v node_modules   # ausência total é o sinal
```

**Impacto:** corrupção silenciosa de dado financeiro/estoque.
**Playbook:** RP-07.

### AP-11 — Configuração de Desenvolvimento em Código de Aplicação
**Definição:** debug ligado, servidor exposto, CORS liberado, config literal no entry point,
sem separação por ambiente.

**Sinais:**
```bash
grep -rniE "debug[[:space:]]*[:=][[:space:]]*(True|true|1)|host[[:space:]]*=[[:space:]]*['\"]0\.0\.0\.0|NODE_ENV.*development|CORS\((app)?\)|Access-Control-Allow-Origin.*\*" . | grep -v node_modules
```
- Config atribuída inline no entry point em vez de módulo de config/ambiente.
- Ausência de `.env`/`.env.example` e de qualquer leitura de variável de ambiente.

**Impacto:** o debugger do Werkzeug/Flask permite execução remota de código; CORS `*` em API
autenticada permite acesso cross-origin indevido.
**Playbook:** RP-02.

### AP-12 — Aninhamento Profundo / Callback Hell / Alta Complexidade
**Definição:** fluxo com 4+ níveis de aninhamento, callbacks encadeados, ou função com muitos
caminhos de decisão.

**Sinais:**
- Callback dentro de callback dentro de callback (Node com API de callback: `db.get(... => { db.run(... => { ... }) })`).
- Indentação ≥ 20 espaços em linha de código.
- `let self = this` (indício de escopo perdido em aninhamento).
- Controle manual de conclusão (`pending--; if (pending === 0) res.json(...)`) — frágil e sujeito a resposta dupla.

```bash
grep -rnE "^ {20,}[^ ]" --include='*.py' --include='*.js' . | grep -v node_modules | head -30
grep -rn "self = this\|var that = this" . | grep -v node_modules
```

**Impacto:** erro invisível na leitura; tratamento de erro incompleto por caminho.
**Playbook:** RP-09.

### AP-13 — Camada Fantasma (pasta existe, camada não)
**Definição:** o projeto tem a estrutura de diretórios de uma arquitetura em camadas, mas o
código não a usa: services nunca instanciados, validadores nunca chamados, constantes nunca
importadas, método de model reimplementado inline nas rotas.

**Sinais:**
```bash
# para cada classe/função definida em services|utils|validators, procure uso externo
grep -rn "class \|^def \|^function \|module.exports" services/ utils/ helpers/ validators/ 2>/dev/null
# depois, por símbolo:
grep -rn "<Símbolo>" . --include='*.py' --include='*.js' | grep -v node_modules   # só a definição ⇒ camada fantasma
```

**Impacto:** pior cenário de manutenção — duas versões divergentes da mesma regra, e a
estrutura passa falsa impressão de organização.
**Playbook:** RP-05, RP-11.

---

## MEDIUM

### AP-14 — N+1 Queries
**Definição:** uma query para a lista e uma query adicional por item.

**Sinais:**
```bash
# query dentro de laço
grep -rnB4 -E "(execute|\.query|\.get\(|\.all\(|find|count\()" --include='*.py' --include='*.js' . | grep -E "for |forEach|while |map\(" | head -30
```
- Acesso a relação lazy do ORM dentro de laço (`len(u.tasks)`, `task.user.name`).
- Query aninhada em callback de resultado de outra query.
- `count()` por item de uma coleção.

**Falsos positivos:** laço sobre coleção de tamanho fixo e pequeno (ex.: 5 status conhecidos).

**Impacto:** latência linear no volume de dados; derruba a API em produção.
**Playbook:** RP-10.

### AP-15 — Exceção Engolida / Erro Não Centralizado
**Definição:** `except:` nu, `catch` vazio, erro ignorado, `str(e)` devolvido ao cliente, e
tratamento repetido em cada handler em vez de middleware.

**Sinais:**
```bash
grep -rnE "except[[:space:]]*:|except Exception" --include='*.py' . 
grep -rnE "catch[[:space:]]*\([a-z_]*\)[[:space:]]*\{[[:space:]]*\}|if \(err\)[[:space:]]*\{?[[:space:]]*$" --include='*.js' . | grep -v node_modules
grep -rnE "str\(e\)|err\.message" . | grep -vE "logger|log\." | grep -v node_modules
# parâmetro de erro recebido e nunca usado no corpo do callback
grep -rnE "function ?\(err[,)]|\(err[,)] *=>" --include='*.js' . | grep -v node_modules
# ausência de handler central é parte do finding
grep -rniE "errorhandler|error_handler|app\.use\(\(err|@app\.errorhandler|middleware.*error" . | grep -v node_modules
```

**Impacto:** bug invisível em produção; vazamento de detalhe interno (fragmento de SQL,
caminho de arquivo) na resposta.
**Playbook:** RP-08.

### AP-16 — Lógica Duplicada
**Definição:** mesma regra implementada em 2+ lugares — validação, cálculo, serialização.

**Sinais:** blocos de 5+ linhas quase idênticos; funções que diferem só pelo `WHERE`; listas
de valores válidos repetidas; regex duplicada; a mesma condição de negócio (ex.: "atrasado")
escrita em vários arquivos.

```bash
grep -rnE "\[['\"](pending|active|ativo|done|admin|user)['\"]" . | grep -v node_modules  # listas de enum repetidas
grep -rnoE "r?['\"]\^\[a-zA-Z0-9.*@.*['\"]" . | grep -v node_modules                      # regex de e-mail duplicada
```

**Impacto:** correção aplicada em um lugar e esquecida nos outros — as versões já divergem.
**Playbook:** RP-11.

### AP-17 — APIs Deprecated ou Removidas
**Definição:** uso de API marcada como deprecated pela linguagem, framework ou biblioteca.
**Verificação obrigatória do relatório.**

| Ecossistema | API deprecated | Substituto | Desde |
|---|---|---|---|
| Python | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` | 3.12 |
| Python | `imp`, `asyncio.get_event_loop()` sem loop ativo, `distutils` | `importlib`, `asyncio.run()`, `packaging` | 3.4/3.10/3.12 |
| Python | adaptadores implícitos de `date`/`datetime` no `sqlite3` | adapter/converter explícito | 3.12 |
| SQLAlchemy | `Model.query`, `Query.get()` | `db.session.get(Model, pk)`, `select()` | 1.4 (legacy no 2.0) |
| Flask | `@app.before_first_request`, `flask.json.JSONEncoder` | `with app.app_context()` no factory, `app.json_provider_class` | 2.2 / removido no 2.3 |
| Flask-SQLAlchemy | `db.get_or_404` legado, `SQLALCHEMY_COMMIT_ON_TEARDOWN` | `db.session.get`, commit explícito | 3.0 |
| Node | `new Buffer()`, `url.parse()`, `util.isArray`, `domain` | `Buffer.from/alloc`, `new URL()`, `Array.isArray` | 6 / 11 |
| Node | `crypto.createCipher` | `crypto.createCipheriv` | 10 |
| Node | `fs.exists` | `fs.existsSync` / `fs.access` | 1.0 |
| Express | `body-parser` separado, `app.del()`, `res.send(status, body)` | `express.json()`, `app.delete()`, `res.status(s).send(b)` | 4.16 / 4.0 |
| Mongoose | `update()`, `remove()`, `findAndModify` | `updateOne/updateMany`, `deleteOne`, `findOneAndUpdate` | 5/6 |
| JS | `var`, `require` em pacote ESM-only, `substr()` | `const/let`, `import`, `slice()` | — |
| Java | `new Date()`/`Calendar` para lógica de data | `java.time` | 8 |
| PHP | `mysql_*`, `create_function` | `PDO`/`mysqli`, closures | 5.5/7.2 |

**Como detectar de forma agnóstica** (não confie só na tabela — ela envelhece):
```bash
# 1. procure os símbolos da tabela acima
grep -rnE "utcnow\(\)|\.query\.get\(|\.query\.|before_first_request|new Buffer\(|url\.parse\(|body-parser|createCipher\(|\.remove\(\)" . | grep -v node_modules
# 2. rode a aplicação/testes e leia os avisos do runtime — a fonte mais confiável
python -W all -c "import app" 2>&1 | grep -i "deprecat\|warning"
node --pending-deprecation -e "require('./src/app')" 2>&1 | grep -i deprecat
npm outdated; pip list --outdated 2>/dev/null
```

**Severidade:** MEDIUM em uso corrente; **HIGH** se a API já foi *removida* na versão
declarada no manifesto (a aplicação quebra ao atualizar); LOW se restrita a script auxiliar.

**Impacto:** quebra no próximo upgrade de runtime/biblioteca; comportamento sutilmente errado
(ex.: `utcnow()` devolve datetime *naive*, que compara errado com datetime *aware*).
**Playbook:** RP-15.

### AP-18 — Validação de Entrada Ausente ou Inconsistente
**Definição:** entrada usada sem validar tipo/formato/faixa, ou regras diferentes para o
mesmo campo em endpoints diferentes (tipicamente create vs update).

**Sinais:**
- `request.get_json()` / `req.body` com campo consumido direto, sem checagem.
- Só checagem de presença (`if not x`), sem tipo nem formato.
- Campo numérico usado em comparação sem conversão (`preco < 0` com string).
- Validação presente no create e ausente no update do mesmo recurso.
- Regex de e-mail sem TLD (`^...@[a-zA-Z0-9.-]+$` aceita `a@b`).

```bash
grep -rnE "get_json\(\)|req\.body|request\.args|request\.form|req\.params" . | grep -v node_modules
```

**Impacto:** 500 por entrada malformada, dado inválido persistido, divergência de contrato.
**Playbook:** RP-11.

### AP-19 — `print`/`console.log` como Estratégia de Log
**Definição:** saída de diagnóstico por print, sem nível, timestamp, correlação nem destino
configurável. **Sobe para CRITICAL se logar dado sensível** (cartão, senha, token, chave) —
ver AP-02/AP-03.

**Sinais:**
```bash
grep -rnE "^[[:space:]]*(print\(|console\.(log|error|warn)\()" --include='*.py' --include='*.js' . | grep -v node_modules
grep -rniE "^import logging|require\(['\"](winston|pino|bunyan)|logging\.getLogger" . | grep -v node_modules   # ausência confirma
```

**Falsos positivos:** CLI cuja saída *é* a interface; script de seed; banner de boot.
**Playbook:** RP-12.

---

## LOW

### AP-20 — Magic Numbers e Strings
Literais de regra de negócio sem nome: faixas de desconto, limites de tamanho, prioridades,
prazos, prefixo de cartão, status escritos como string solta.

```bash
grep -rnE "(>|<|>=|<=|==)[[:space:]]*[0-9]{2,}|\*[[:space:]]*0\.[0-9]+" --include='*.py' --include='*.js' . | grep -v node_modules
```
Agravante: existir constante equivalente já definida no projeto e ignorada. **Playbook:** RP-13.

### AP-21 — Nomenclatura Pobre e Shadowing
Variáveis de uma letra fora de laço trivial (`u`, `e`, `p`, `cc`, `cid`), abreviação cifrada em
contrato de API (`usr`, `eml`, `pwd`), shadowing de builtin (`id`, `type`, `list`, `dict`),
mistura de idiomas no mesmo módulo, contadores `p1..p5`.

```bash
grep -rnE "\b(def|function)[[:space:]]+[a-z_]+\(.*\b(id|type|list|dict|str|input)\b" . | grep -v node_modules
grep -rnE "(let|var|const)[[:space:]]+[a-z]{1,2}[[:space:]]*=" --include='*.js' . | grep -v node_modules
```
**Playbook:** RP-13.

### AP-22 — Código Morto e Import Não Utilizado
Import não usado, função/classe definida e nunca chamada, export inútil, variável atribuída e
nunca lida, dependência declarada no manifesto e ausente do código, laço sem efeito.

```bash
# para cada símbolo importado, conte usos no arquivo
grep -rnE "^(import|from|const .*= require)" --include='*.py' --include='*.js' . | grep -v node_modules
# dependência declarada e não usada
# (cruze requirements.txt / package.json dependencies com grep de import)
```
**Playbook:** RP-16.

### AP-23 — Boilerplate de Serialização Repetido
Mapeamento manual `row → dict` (ou entidade → JSON) copiado em vários pontos, com risco de
divergir; `if/else` devolvendo `True`/`False` literal; `type(x) == list` em vez de `isinstance`.

```bash
grep -rn "to_dict\|toJSON\|row\[" --include='*.py' --include='*.js' . | grep -v node_modules
grep -rnE "type\([a-z_]+\)[[:space:]]*==" --include='*.py' . 
```
**Playbook:** RP-16.
