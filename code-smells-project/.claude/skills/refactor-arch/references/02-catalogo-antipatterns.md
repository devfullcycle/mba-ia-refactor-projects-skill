# 02 — Catálogo de anti-patterns e vulnerabilidades

Use este arquivo na **Fase 2**. Ele diz *o que procurar*, *como confirmar* e *que severidade atribuir*. É um guia, não um limite: achados reais fora do catálogo entram como `OUTRO` (seção 6).

## 1. Como ler uma entrada

Cada entrada tem: **Sinal** (descrição abstrata, vale para qualquer linguagem) · **Dicas por stack** (atalhos; nunca exaustivos) · **NÃO é finding** (controle contra falso positivo) · **Confirmar** (o que provar antes de reportar) · **Severidade** (padrão e ajustes) · **Correção** (padrão do playbook `05-playbook-refatoracao.md`).

**Stack sem dica listada?** Derive o equivalente a partir do **Sinal** e registre `derivado` em "Observações da execução". Isso é o mecanismo de agnosticismo: o sinal manda, a dica ajuda.

## 2. Procedimento de verificação (obrigatório para cada candidato)

1. **Localize** por busca (Grep) usando o sinal e as dicas.
2. **Releia** o trecho (Read com offset/limit) e anote o número de linha **real**. Nunca reporte linha de memória ou estimada.
3. **Rastreie a origem** do dado quando o sinal falar em "dado externo" (request, body, query, params, headers, arquivo, variável de ambiente controlada por usuário). Dado interno/constante não é finding.
4. **Verifique o NÃO é finding** da entrada.
5. **Atribua severidade** pela rubrica (seção 3) e confiança:
   - `CONFIRMED`: você leu o trecho e rastreou a origem/efeito.
   - `LIKELY`: o padrão está claro, mas parte do fluxo não foi rastreada.
   - `SUSPECTED`: indício sem confirmação (ex.: versão de API deprecated inferida). Nunca use `SUSPECTED` em CRITICAL sem dizer o que falta confirmar.
6. **Mascare segredos** na evidência.
7. **Agrupe**: ocorrências do mesmo anti-pattern viram **um** finding com a lista de localizações (campo `File:` e `Ocorrências:`). Dois anti-patterns diferentes no mesmo trecho são dois findings.
8. Candidatos que falharem em 3 ou 4 vão para "Descartados / falsos positivos".

## 3. Rubrica de severidade (aplique as perguntas nesta ordem; pare na primeira resposta "sim")

| Sev. | Pergunta |
|---|---|
| **CRITICAL** | Um atacante **remoto e não autenticado** consegue comprometer confidencialidade, integridade ou disponibilidade (execução de código/SQL, vazamento de segredos ou credenciais, destruição de dados)? **Ou** há segredo/credencial real versionado? **Ou** um único arquivo/classe concentra todas as camadas (God Class/File)? |
| **HIGH** | Exige pré-condição (autenticação, outro bug) ou o impacto é parcial? **Ou** é violação forte de MVC/SOLID que impede teste e manutenção (lógica de negócio no controller, estado global mutável, acoplamento sem injeção)? |
| **MEDIUM** | Degrada performance, consistência ou padronização sem comprometer segurança diretamente (N+1, validação ausente, duplicação, API deprecated sem risco de segurança)? |
| **LOW** | Afeta só legibilidade/estilo sem efeito funcional (magic numbers, nomes ruins, imports sem uso, `print` no lugar de logger)? |

**Ajustes permitidos** (±1 nível, sempre justificados em uma frase na `Description`): código comprovadamente inalcançável/morto (−1); exposição efetiva comprovada em ambiente produtivo (+1). **API deprecated criptográfica**: mínimo HIGH. Não rebaixe segredo real versionado.

## 4. Segurança (SEC)

### SEC-01 · SQL Injection — CRITICAL
- **Categoria:** Segurança · CWE-89 · OWASP A03:2021
- **Sinal:** dado externo chega a uma chamada que executa consulta montada por concatenação, interpolação ou formatação de string, em vez de parâmetros ligados.
- **Dicas:** Python `execute("..." + x)`, `execute(f"...{x}")`, `execute("..." % x)`, `.format()` · Node `db.run(\`...${x}\`)`, `db.all("..." + x)` · Java `Statement.executeQuery("..." + x)` · PHP `mysqli_query("..." . $x)` · Go `db.Query("..." + x)` / `fmt.Sprintf` · Ruby `execute("...#{x}")` · ORMs: `raw()`, `text()`, `extra()`, `createQuery("..." + x)`.
- **NÃO é finding:** placeholders (`?`, `$1`, `:nome`, `%s` passado como argumento separado do `execute`), ORM com filtros por método, concatenação de constante/enum interno.
- **Confirmar:** rastrear a variável até request/body/query/params (ou dado persistido anteriormente vindo do usuário).
- **Severidade:** CRITICAL; HIGH se só alcançável autenticado (justificar).
- **Correção:** P-02

### SEC-02 · Segredos e credenciais hardcoded — CRITICAL
- **Categoria:** Segurança · CWE-798 · OWASP A07:2021
- **Sinal:** literal atribuído a nome que indica segredo (`secret`, `key`, `token`, `pass`, `pwd`, `credential`, `api_key`, `dsn`, `smtp`) ou literal com formato conhecido de chave (`pk_live_`, `sk_`, `AKIA…`, `ghp_`, `-----BEGIN … PRIVATE KEY-----`), em código versionado; senha de seed/admin em texto no fonte.
- **Dicas:** `SECRET_KEY = "..."`, `app.config[...] = "..."`, objeto `config = { dbPass: "..." }`, `application.properties` com senha, `.env` versionado (verifique o `.gitignore`).
- **NÃO é finding:** leitura de variável de ambiente, placeholder óbvio documentado (`changeme`, `<seu-valor>`) em arquivo `*.example`, chave pública que é pública por definição, valor de teste dentro de diretório de testes.
- **Confirmar:** o valor é usado de fato (config, conexão, assinatura) ou é exemplo?
- **Severidade:** CRITICAL (chave `live`/`prod` ou usada em runtime); HIGH se evidentemente só de desenvolvimento local.
- **Correção:** P-01

### SEC-03 · Endpoint administrativo/destrutivo sem autenticação — CRITICAL
- **Categoria:** Segurança · CWE-306 · OWASP A01:2021
- **Sinal:** rota cujo caminho/ação é administrativa ou destrutiva (`/admin`, `reset`, `drop`, `wipe`, exclusão em massa, relatório financeiro, remoção de usuário) e que não verifica identidade nem perfil antes de executar.
- **Dicas:** decoradores/middlewares de auth ausentes (`@login_required`, `@jwt_required`, `authenticate`, `[Authorize]`, `@PreAuthorize`, `before_action :authenticate`); rotas registradas direto no arquivo de entrada.
- **NÃO é finding:** rota que de fato verifica token/perfil (leia a verificação, não apenas o decorador); rota somente de desenvolvimento protegida por flag de ambiente que fica desligada por padrão.
- **Confirmar:** ler o handler e a cadeia de middlewares até o ponto de registro.
- **Severidade:** CRITICAL; HIGH se o efeito for apenas leitura de dados não sensíveis.
- **Correção:** P-05

### SEC-04 · Execução arbitrária (SQL, comando ou código) — CRITICAL
- **Categoria:** Segurança · CWE-94 / CWE-78 · OWASP A03:2021
- **Sinal:** o servidor executa texto/objeto controlado pelo cliente como SQL, comando de shell ou código; ou usa funções de avaliação/deserialização insegura sobre dado externo.
- **Dicas:** `eval`, `exec`, `compile`, `os.system`, `subprocess(..., shell=True)`, `pickle.loads`, `yaml.load` sem `SafeLoader`, `child_process.exec`, `new Function`, `vm.runInNewContext`, `Runtime.exec`, `system()`/backticks, `unserialize`, rota que recebe `sql`/`query`/`cmd` e executa.
- **NÃO é finding:** execução de comando com argumentos fixos e lista de argumentos (sem shell); `eval` sobre literal interno.
- **Confirmar:** origem do argumento.
- **Severidade:** CRITICAL.
- **Correção:** P-05 (remover/proteger), P-02, P-07

### SEC-05 · Modo debug / console remoto ativo e bind público — CRITICAL
- **Categoria:** Segurança · CWE-489 · OWASP A05:2021
- **Sinal:** flag de depuração ligada de forma fixa no código de inicialização, especialmente com escuta em todas as interfaces.
- **Dicas:** `debug=True`, `app.config["DEBUG"] = True`, `host="0.0.0.0"`, `NODE_ENV` forçado a `development`, `APP_DEBUG=true`, `spring.devtools`, `display_errors=On`.
- **NÃO é finding:** debug controlado por variável de ambiente com padrão desligado; bind em `127.0.0.1`.
- **Confirmar:** valor fixo no código de inicialização.
- **Severidade:** CRITICAL (debug + bind público); HIGH (debug fixo com bind local).
- **Correção:** P-01

### SEC-06 · Armazenamento inseguro de senha — CRITICAL
- **Categoria:** Segurança · CWE-256 / CWE-327 / CWE-916 · OWASP A02:2021
- **Sinal:** senha gravada em texto puro, ou protegida por hash rápido sem salt, ou por esquema artesanal/reversível (base64, XOR, "hash" caseiro); comparação de senha por igualdade direta.
- **Dicas:** `md5`, `sha1`, `sha256` sem KDF, `Buffer.from(x).toString('base64')`, `password == input`, `hashlib.md5(pwd...)`, colunas `senha`/`password` preenchidas com o valor recebido.
- **NÃO é finding:** bcrypt/argon2/scrypt/PBKDF2 com parâmetros razoáveis; hash usado para integridade de arquivo (não senha).
- **Confirmar:** o valor armazenado é a senha ou derivada dela de forma fraca?
- **Severidade:** CRITICAL (texto puro, reversível, MD5/SHA1 sem salt); HIGH (SHA-256 salgado sem KDF).
- **Correção:** P-03

### SEC-07 · Dados sensíveis expostos em respostas — CRITICAL
- **Categoria:** Segurança · CWE-200 / CWE-201 · OWASP A02:2021
- **Sinal:** serializador ou handler devolve ao cliente campos sensíveis (senha/hash, chave secreta, token, configuração interna); endpoint de saúde/diagnóstico devolve configuração ou segredos.
- **Dicas:** `to_dict()`/`toJSON()` que inclui `password`; resposta com `secret_key`, `db_path`, `debug`; `SELECT *` devolvido sem filtro de colunas.
- **NÃO é finding:** o campo existe só no modelo interno e é filtrado antes da resposta.
- **Confirmar:** o campo chega ao corpo da resposta de pelo menos uma rota.
- **Severidade:** CRITICAL (segredo, senha ou hash em rota pública); HIGH (PII).
- **Correção:** P-04

### SEC-08 · Dados sensíveis em logs — CRITICAL
- **Categoria:** Segurança · CWE-532 · OWASP A09:2021
- **Sinal:** log/print que interpola número de cartão, senha, token, chave ou PII.
- **Dicas:** `print("..." + senha)`, `console.log(\`cartão ${cc}\`)`, `logger.info(request.body)`, `log.debug(user)`.
- **NÃO é finding:** log de identificador não sensível; valor já mascarado.
- **Confirmar:** o valor logado é sensível e não está mascarado.
- **Severidade:** CRITICAL (cartão, senha, segredo); HIGH (e-mail/PII).
- **Correção:** P-15

### SEC-09 · Autenticação/autorização ausente ou falsa — HIGH
- **Categoria:** Segurança · CWE-306 / CWE-862 · OWASP A01:2021, A07:2021
- **Sinal:** rotas que leem ou alteram dados de usuários sem nenhuma verificação de identidade; "login" que devolve token constante, previsível ou sem validação posterior; CORS liberado a qualquer origem em API com dados de usuário.
- **Dicas:** `'fake-jwt-token-' + id`, token nunca verificado, `CORS(app)` sem origens, `app.use(cors())`, `Access-Control-Allow-Origin: *`.
- **NÃO é finding:** API pública de dados públicos; rotas realmente protegidas por gateway documentado no próprio repositório.
- **Confirmar:** não existe validação de token/sessão em nenhuma rota de dados.
- **Severidade:** HIGH; CRITICAL se **nenhuma** rota verifica identidade e há dados pessoais ou escrita.
- **Correção:** P-05

### SEC-10 · Escalação de privilégio / mass assignment — CRITICAL
- **Categoria:** Segurança · CWE-915 / CWE-269 · OWASP A01:2021
- **Sinal:** campos de privilégio ou estado de conta (`role`, `is_admin`, `active`, `permissions`) aceitos do corpo da requisição e gravados sem restrição.
- **Dicas:** `user.role = data.get('role')`, `Model(**request.json)`, `Object.assign(user, req.body)`, `update(request.all())`.
- **NÃO é finding:** campo restrito por verificação de perfil administrador.
- **Confirmar:** handler grava o campo vindo do cliente.
- **Severidade:** CRITICAL (qualquer um vira admin sem autenticação); HIGH (exige autenticação).
- **Correção:** P-05, P-07

### SEC-11 · IDOR / falta de checagem de propriedade — HIGH
- **Categoria:** Segurança · CWE-639 · OWASP A01:2021
- **Sinal:** recurso buscado por identificador vindo do cliente sem confrontar com o usuário autenticado (leitura/alteração de dados de terceiros).
- **Dicas:** `/usuarios/<id>/pedidos` sem comparar `id` com o usuário da sessão.
- **NÃO é finding:** recurso público por definição.
- **Confirmar:** existe identidade de usuário no fluxo (se não existe autenticação, reporte SEC-09 em vez deste).
- **Severidade:** HIGH.
- **Correção:** P-05

### SEC-12 · Validação de entrada ausente ou frágil — MEDIUM
- **Categoria:** Segurança · CWE-20 · OWASP A03:2021
- **Sinal:** dado externo usado sem checar presença, tipo, faixa ou formato; valores que alteram regra de negócio sem limites (quantidade negativa, preço como texto).
- **Dicas:** `int(request.args[...])` sem tratamento, `request.get_json()` sem checar `None`, `req.body.x` direto em cálculo, regex de e-mail permissiva.
- **NÃO é finding:** validação centralizada (schema/middleware) comprovada para a rota.
- **Confirmar:** existe caminho do dado até um efeito (cálculo, gravação) sem validação.
- **Severidade:** MEDIUM; HIGH se chega a regra financeira, estoque ou sink perigoso.
- **Correção:** P-07

### SEC-13 · Vazamento de detalhes internos em erros — MEDIUM
- **Categoria:** Segurança · CWE-209 · OWASP A05:2021
- **Sinal:** exceção/mensagem interna devolvida ao cliente; ausência de handler central de erros.
- **Dicas:** `return jsonify({"erro": str(e)})`, `res.status(500).send(err.message)`, `e.printStackTrace()` para a resposta, stack trace em produção.
- **NÃO é finding:** mensagem de validação de negócio controlada pelo próprio código.
- **Confirmar:** o texto da exceção chega ao corpo da resposta.
- **Severidade:** MEDIUM.
- **Correção:** P-06

### SEC-14 · Regra financeira confiando no cliente ou simulada — CRITICAL
- **Categoria:** Segurança · CWE-602 / CWE-840 · OWASP A04:2021
- **Sinal:** aprovação de pagamento decidida por heurística trivial (prefixo do cartão, flag enviada pelo cliente); total/preço aceito do cliente em vez de calculado no servidor; ausência de integração real tratada como se fosse produção.
- **Dicas:** `status = card.startswith("4") ? "PAID" : "DENIED"`, `total = body.total`.
- **NÃO é finding:** stub explicitamente isolado em ambiente de teste, sem caminho para produção.
- **Confirmar:** o resultado da "aprovação" libera um bem ou acesso.
- **Severidade:** CRITICAL (libera bem sem cobrança real); HIGH (preço/total vindo do cliente).
- **Correção:** P-09, P-07

### SEC-15 · Fluxo crítico sem transação / condição de corrida — HIGH
- **Categoria:** Segurança/Integridade · CWE-362 / CWE-367 · OWASP A04:2021
- **Sinal:** verificação e escrita de estoque, saldo ou matrícula em passos separados sem transação, bloqueio ou operação atômica; várias escritas dependentes sem rollback.
- **Dicas:** loop que lê estoque e depois outro loop que grava; inserts encadeados sem `BEGIN`/`commit`/`rollback`; erro ignorado em callback intermediário.
- **NÃO é finding:** operação única atômica; transação comprovada.
- **Confirmar:** falha entre passos deixa estado inconsistente.
- **Severidade:** HIGH.
- **Correção:** P-10

### SEC-16 · Dependências vulneráveis, antigas ou não usadas — MEDIUM
- **Categoria:** Segurança · CWE-1104 · OWASP A06:2021
- **Sinal:** versões fixadas antigas de framework/bibliotecas, ausência de lockfile, pacotes declarados e nunca importados.
- **Dicas:** `requirements.txt` com `==` antigo, `package.json` com `^` em major antigo, pacote sem import (busque o nome no código).
- **NÃO é finding:** dependência de desenvolvimento declarada à parte.
- **Confirmar:** confronte manifesto × imports. **Não** consulte rede/CVE por conta própria: apenas **sugira** `pip-audit`/`npm audit`/equivalente no relatório (executar é classe C e exige aprovação).
- **Severidade:** MEDIUM; LOW para pacote não usado isolado.
- **Correção:** P-18

### SEC-17 · Falta de proteções HTTP básicas — MEDIUM
- **Categoria:** Segurança · CWE-770 / CWE-693 · OWASP A05:2021
- **Sinal:** ausência de limitação de taxa em rotas sensíveis (login, checkout), de cabeçalhos de segurança e de CORS restrito.
- **Dicas:** `helmet`, `express-rate-limit`, `flask-limiter`, `flask-talisman`, `SecurityFilterChain`, `django.middleware.security`.
- **NÃO é finding:** proteção provida por camada documentada no repositório.
- **Confirmar:** nenhum middleware equivalente registrado.
- **Severidade:** MEDIUM.
- **Correção:** P-19

## 5. Arquitetura (ARC), Deprecated (DEP), Testes (TST) e Qualidade (QLT)

### ARC-01 · God Class / God File — CRITICAL
- **Sinal:** um módulo reúne ≥ 3 papéis (config, acesso a dados, regra de negócio, rota/HTTP, formatação) ou concentra vários domínios; classe que cria banco, define schema, semeia dados e registra rotas.
- **Dicas:** arquivo > ~300 linhas com SQL + validação + serialização; classe `*Manager`/`*Service` com rotas e queries; entrypoint com rotas e acesso a banco.
- **NÃO é finding:** arquivo grande porém coeso (um papel, um domínio).
- **Confirmar:** liste os papéis encontrados no arquivo (use a classificação da Fase 1).
- **Severidade:** CRITICAL. **Correção:** P-08, P-09, P-13

### ARC-02 · Lógica de negócio em controller/rota — HIGH
- **Sinal:** handler com cálculo de domínio, validação de regra, orquestração de várias entidades ou persistência direta.
- **NÃO é finding:** handler fino que valida formato, chama serviço e escolhe status.
- **Severidade:** HIGH. **Correção:** P-09

### ARC-03 · Estado global mutável / conexão única global — HIGH
- **Sinal:** variável de módulo alterada durante requests (cache, contadores, conexão) compartilhada por todas as requisições.
- **Dicas:** `global x`, `let cache = {}` exportado e mutado, conexão de banco singleton com `check_same_thread=False`.
- **NÃO é finding:** constante imutável; singleton de configuração somente leitura.
- **Severidade:** HIGH. **Correção:** P-13

### ARC-04 · Acoplamento forte sem injeção de dependência — HIGH
- **Sinal:** camadas importam/instanciam infraestrutura direta (`get_db()`, `new Database()`, `config` global) em vez de recebê-la.
- **NÃO é finding:** acesso a infraestrutura isolado na camada de dados/composition root.
- **Severidade:** HIGH. **Correção:** P-13, P-08

### ARC-05 · Callback hell / fluxo assíncrono manual — HIGH
- **Sinal:** ≥ 4 níveis de callbacks aninhados; contadores manuais de conclusão; erros ignorados em callbacks.
- **Dicas:** Node `db.get(..., (err, x) => { db.get(..., (err, y) => ...` ; contadores `pending--`.
- **NÃO é finding:** callback isolado de 1–2 níveis.
- **Severidade:** HIGH. **Correção:** P-12

### ARC-06 · Responsabilidade fora do lugar — HIGH
- **Sinal:** rota/handler/modelo em módulo de outro domínio (ex.: CRUD de categorias dentro do módulo de relatórios).
- **Severidade:** HIGH (MEDIUM se houver só um handler). **Correção:** P-08

### ARC-07 · Queries N+1 — MEDIUM
- **Sinal:** consulta executada dentro de loop sobre o resultado de outra consulta (ou acesso a relacionamento tardio por item).
- **Dicas:** `for x in rows: cursor.execute(... x.id)`, `.forEach(... db.get(...))`, `len(user.tasks)` em lista de usuários, `Model.query.get(x.fk)` em loop.
- **NÃO é finding:** loop sobre coleção pequena fixa e limitada.
- **Severidade:** MEDIUM. **Correção:** P-11

### ARC-08 · Código duplicado — MEDIUM
- **Sinal:** mesmo bloco ou regra repetido ≥ 3 vezes (serialização row→dict, regra "atrasada", validação criar/atualizar).
- **Severidade:** MEDIUM. **Correção:** P-16

### ARC-09 · Tratamento de erro ruim — MEDIUM
- **Sinal:** captura genérica que descarta o erro (`except:`/`catch {}`), erro ignorado em callback, respostas de erro inconsistentes (texto × JSON, idiomas misturados).
- **Severidade:** MEDIUM. **Correção:** P-06

### ARC-10 · Integridade referencial ausente — MEDIUM
- **Sinal:** schema sem `UNIQUE`/`FOREIGN KEY`/`NOT NULL` onde a regra de negócio exige; exclusão que deixa registros órfãos.
- **Severidade:** MEDIUM. **Correção:** P-10

### ARC-11 · Sem paginação / carga total / `SELECT *` — MEDIUM
- **Sinal:** listagens que carregam toda a tabela em memória; `.all()`/`SELECT *` sem limite; várias `COUNT` onde uma agregação resolve.
- **Severidade:** MEDIUM. **Correção:** P-11

### ARC-12 · Dinheiro em ponto flutuante — MEDIUM
- **Sinal:** valores monetários em `REAL`/`float`/`double`.
- **Severidade:** MEDIUM. **Correção:** P-17

### DEP-01 · `datetime.utcnow()` (Python ≥ 3.12) — MEDIUM
- **Sinal/Equivalente:** `datetime.utcnow()` / `utcfromtimestamp()` → `datetime.now(timezone.utc)`.
- **Confirmar:** versão de Python declarada/em uso ≥ 3.12 ou ausência de restrição. **Correção:** P-14

### DEP-02 · SQLAlchemy `Model.query.get(id)` — MEDIUM
- **Sinal/Equivalente:** `Query.get()` (legado em 2.x) → `db.session.get(Model, id)`.
- **Confirmar:** versão do SQLAlchemy/Flask-SQLAlchemy ≥ 2.0/3.0 no manifesto. **Correção:** P-14

### DEP-03 · APIs deprecated de Node — MEDIUM (HIGH se criptografia)
- **Sinal/Equivalente:** `new Buffer()` → `Buffer.from`/`alloc`; `url.parse` → `new URL`; `fs.exists` → `fs.access`/`existsSync`; `crypto.createCipher/createDecipher` → `createCipheriv/createDecipheriv`; `req.param()` → `req.params/query/body`; `body-parser` standalone → `express.json()`; pacote `request` → `fetch`/`undici`/`axios`. **Correção:** P-14

### DEP-04 · APIs deprecated de Flask/Python web — MEDIUM
- **Sinal/Equivalente:** `@app.before_first_request` → inicialização no factory; `flask.json.JSONEncoder` → `JSONProvider`; `flask.escape` → `markupsafe.escape`; `imp` → `importlib`; `distutils` → `setuptools`. **Correção:** P-14

### DEP-05 · Deprecated genérico da stack declarada — MEDIUM
- **Sinal:** API marcada como deprecated/obsoleta na versão do framework **declarada** no manifesto (Java `new Integer()`, `Thread.stop`; PHP `mysql_*`; .NET `WebClient`; Go `ioutil`; Ruby `URI.escape` etc.).
- **Regra:** só reporte com base em conhecimento seguro da versão; senão `SUSPECTED` e diga o que consultar (nota de versão). Sempre indique o **equivalente moderno**. Criptografia/segurança deprecated: mínimo HIGH. **Correção:** P-14

### TST-01 · Ausência de testes automatizados — MEDIUM
- **Sinal:** nenhum diretório/arquivo/config de teste reconhecido (inventário de validação da Fase 1).
- **NÃO é finding:** teste manual documentado **e** coleção de requisições executável (aí é LOW).
- **Observação:** a skill **não cria testes** (política D5); recomende e explique o impacto na validação.
- **Correção:** recomendação apenas.

### TST-02 · Ausência de instruções de execução/validação — LOW
- **Sinal:** README sem como instalar/rodar/testar; nenhum script, target ou CI que mostre isso.
- **Correção:** recomendação apenas (documentar).

### TST-03 · Testes existentes quebrados ou não executáveis — MEDIUM
- **Sinal:** configuração/dependência de teste referenciada mas ausente; testes que importam módulos inexistentes (**estático**: não rode testes na Fase 2; a execução real só ocorre na Fase 3, passo 0b — se lá o baseline falhar, registre).
- **Correção:** recomendação apenas.

### QLT-01 · Magic numbers e strings soltas — LOW
- **Sinal:** literais numéricos/strings de regra (faixas de desconto, status, limites) repetidos ou sem nome. **Correção:** P-16

### QLT-02 · Nomes ruins ou que sombreiam builtins — LOW
- **Sinal:** `id`, `list`, `type`, `u`, `e`, `cc`, `cursor2`; payload com chaves crípticas. **Correção:** P-16

### QLT-03 · Imports, variáveis e código mortos — LOW
- **Sinal:** import nunca usado, função/serviço nunca chamado, variável exportada e não consumida. **Confirmar:** busque usos por nome em todo o projeto. **Correção:** P-16

### QLT-04 · `print`/`console.log` no lugar de logger — LOW
- **Sinal:** saída por `print`/`console.log` como mecanismo de log. **Correção:** P-15

### QLT-05 · Estilo inconsistente — LOW
- **Sinal:** `type(x) == list` em vez de `isinstance`; `if/else` que devolve booleano; mistura `this`/`self`; `let` onde cabe `const`; datas serializadas por `str()` em vez de ISO 8601; `==` onde cabe checagem estrita. **Correção:** P-16

## 6. Achados fora do catálogo (`OUTRO`)

Se encontrar problema real de segurança, arquitetura ou qualidade que não cabe em nenhuma entrada, reporte-o com ID `OUTRO-01…`, `Categoria: Outro`, severidade pela rubrica (seção 3), `Confiança` e `Recommendation` descritiva (sem `P-xx`; se houver padrão equivalente no playbook, cite-o). Mencione em "Observações da execução".

## 7. Distribuição esperada e checagem final da Fase 2

Antes de fechar o relatório confirme: (a) varreu todas as categorias SEC, ARC, DEP, TST, QLT; (b) o resultado separa Segurança de Arquitetura; (c) APIs deprecated foram **procuradas** (se nenhuma, escreva "DEP: nenhuma encontrada para <versões declaradas>"); (d) ≥ 5 findings (ver `03-template-relatorio.md`); (e) pelo menos um CRITICAL/HIGH, ou justificativa expressa; (f) cada finding tem arquivo:linha relido.
