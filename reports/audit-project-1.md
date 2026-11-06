================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Path:    code-smells-project
Run:     2026-11-05T17:55:12-03:00          Run id: 20261105-175512
Stack:   Python 3.14.0 + Flask 3.1.1 (confiança: alta)
Files:   4 analyzed | ~780 lines of code
Architecture: parcialmente-em-camadas
Skill:   refactor-arch 1.1 | Catalog 1.0
Evidence: reports/evidence/project-1/20261105-175512/

## Summary
CRITICAL: 9 | HIGH: 6 | MEDIUM: 10 | LOW: 6
Total: 31 findings (159 ocorrências)
Por categoria: Segurança 14 | Arquitetura 10 | Deprecated 0 | Testes 1 | Qualidade 5 | Outro 1
Cobertura: 4/4 arquivos-fonte lidos integralmente (+ 2 arquivos de teste lidos); 0 inspecionados só por busca

## Estrutura ANTES
```
code-smells-project/
├── app.py                 (88)   entrypoint + config + rotas + handlers admin com SQL
├── controllers.py         (292)  handlers HTTP + validação + regra + health com SQL
├── database.py            (86)   conexão global + schema + seed
├── models.py              (314)  SQL + regra de negócio + serialização
├── tests/
│   ├── conftest.py        (100)
│   └── test_api.py        (247)
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── loja.db                (ignorado pelo git; não lido)
```
Obs.: `config/`, `controllers/`, `database/`, `middlewares/`, `models/`, `routes/`, `services/` existem no disco, não versionados, contendo **apenas** `__pycache__` de uma execução anterior (sem código-fonte).

| Métrica | Valor |
|---|---|
| Arquivos-fonte | 4 |
| Linhas de código (aprox.) | ~780 |
| Camadas presentes (papéis) | entrypoint, config (misturada), rotas (misturadas no entrypoint), controllers, models/acesso a dados; **ausentes**: services, middleware, config dedicada |
| Maior arquivo | models.py (314) |
| Arquivos com 3+ papéis | 3 (app.py, controllers.py, models.py) |

## Superfície de ataque
| Método | Rota | Handler (arquivo:linha) | Autenticação | Administrativa/destrutiva |
|---|---|---|---|---|
| GET | / | app.py:33 | não | não |
| GET | /produtos | controllers.py:5 | não | não |
| GET | /produtos/busca | controllers.py:111 | não | não |
| GET | /produtos/<int:id> | controllers.py:14 | não | não |
| POST | /produtos | controllers.py:24 | não | não |
| PUT | /produtos/<int:id> | controllers.py:64 | não | não |
| DELETE | /produtos/<int:id> | controllers.py:98 | não | não |
| GET | /usuarios | controllers.py:128 | não | não (expõe PII e senha) |
| GET | /usuarios/<int:id> | controllers.py:136 | não | não (expõe PII e senha) |
| POST | /usuarios | controllers.py:146 | não | não |
| POST | /login | controllers.py:167 | não | não |
| POST | /pedidos | controllers.py:188 | não | não |
| GET | /pedidos | controllers.py:229 | não | não |
| GET | /pedidos/usuario/<int:usuario_id> | controllers.py:222 | não | não |
| PUT | /pedidos/<int:pedido_id>/status | controllers.py:237 | não | não |
| GET | /relatorios/vendas | controllers.py:257 | não | **sim** (relatório financeiro) |
| GET | /health | controllers.py:264 | não | não (expõe configuração/segredo) |
| POST | /admin/reset-db | app.py:48 | não | **sim** |
| POST | /admin/query | app.py:60 | não | **sim** |

Entradas: corpo JSON (produtos, usuários, login, pedidos, status, `sql`), query string (`q`, `categoria`, `preco_min`, `preco_max`), parâmetros de rota inteiros. Segredos: literais no fonte (app.py:7; controllers.py:289; database.py:76-78). Integrações externas: nenhuma real (e-mail/SMS/push simulados com `print`, controllers.py:208-210).

## Findings

### [CRITICAL] F-001 · SEC-02 Segredos e credenciais hardcoded
File: app.py:7; controllers.py:289; database.py:76-78
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-798 / A07:2021
Evidência: `app.config["SECRET_KEY"] = "minh***"` · `("Admin", "admin@loja.com", "admi***", "admin")`
Description: a `SECRET_KEY` do Flask é um literal versionado e usado em runtime; o mesmo literal é repetido na resposta do `/health`; o seed grava as senhas dos usuários de exemplo, incluindo o administrador, em texto no fonte.
Impact: qualquer pessoa com acesso ao repositório (ou ao histórico git) conhece a chave de assinatura da aplicação e a senha do administrador.
Recommendation: módulo de config lendo variáveis de ambiente, `.env.example` só com nomes, seed de usuários condicionado a variáveis (sem senha padrão no código) e rotação da chave/senha já expostas no histórico (Playbook P-01).

### [CRITICAL] F-002 · SEC-05 Modo debug ativo e bind público
File: app.py:8, 88
Ocorrências: 2 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-489 / A05:2021
Evidência: `app.run(host="0.0.0.0", port=5000, debug=True)`
Description: debug fixo no código (`app.config["DEBUG"] = True` e `debug=True`) com escuta em todas as interfaces.
Impact: o depurador interativo do Werkzeug (console Python protegido só por PIN) e os tracebacks ficam acessíveis a qualquer máquina da rede.
Recommendation: `DEBUG`, `HOST` e `PORT` por variável de ambiente, padrão `debug=False` e `127.0.0.1` (Playbook P-01).

### [CRITICAL] F-003 · SEC-09 Autenticação/autorização ausente e CORS irrestrito
File: app.py:9, 11-30; controllers.py:167-186
Ocorrências: 2 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-306 / CWE-862 / A01:2021, A07:2021
Evidência: `CORS(app)` · `return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200`
Description: nenhuma das 19 rotas verifica identidade ou perfil (ausência — referência no ponto de registro das rotas); `/login` apenas devolve os dados do usuário, sem emitir token/sessão que alguma rota valide; `CORS(app)` libera qualquer origem. Há dados pessoais (`/usuarios`) e escrita (produtos, pedidos), o que eleva a CRITICAL pela rubrica.
Impact: qualquer cliente anônimo lê todos os usuários e pedidos, cria/altera/remove produtos e muda status de pedidos de terceiros; páginas de qualquer origem podem chamar a API pelo navegador da vítima.
Recommendation: emitir token assinado no login, exigir credencial nas rotas de dados com checagem de perfil/propriedade e restringir origens do CORS (Playbook P-05, P-19). **Exige contrato** (CT-04, CT-08).

### [CRITICAL] F-004 · SEC-03 Endpoints administrativos/destrutivos sem autenticação
File: app.py:28, 47-57, 59-78
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-306 / A01:2021
Evidência: `@app.route("/admin/reset-db", methods=["POST"])` → `cursor.execute("DELETE FROM usuarios")`
Description: `POST /admin/reset-db` apaga as quatro tabelas, `POST /admin/query` executa SQL livre e `GET /relatorios/vendas` expõe faturamento; nenhum verifica identidade.
Impact: um único `POST` anônimo destrói todo o banco; dados financeiros acessíveis a qualquer um.
Recommendation: remover `/admin/query` e exigir perfil administrador em `/admin/reset-db` e `/relatorios/vendas` (Playbook P-05). **Exige contrato** (CT-01, CT-02, CT-03).

### [CRITICAL] F-005 · SEC-04 Execução arbitrária de SQL enviada pelo cliente
File: app.py:59-78
Ocorrências: 1 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-94 / A03:2021
Evidência: `query = dados.get("sql", "")` … `cursor.execute(query)` … `db.commit()`
Description: o campo `sql` do corpo é executado como está e, se não for `SELECT`, confirmado; erros do SQLite voltam ao cliente.
Impact: leitura de todas as senhas, alteração/remoção de qualquer registro e `DROP TABLE`, sem autenticação.
Recommendation: remover a rota; não há uso legítimo de SQL livre via HTTP (Playbook P-05). **Exige contrato** (CT-01).

### [CRITICAL] F-006 · SEC-07 Dados sensíveis expostos em respostas
File: controllers.py:286-289; models.py:83, 99
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-200 / CWE-201 / A02:2021
Evidência: `"secret_key": "minh***"` · `"db_path": "loja.db"` · `"senha": row["senha"]`
Description: `GET /health` (público) devolve `secret_key`, `db_path` e `debug`; `GET /usuarios` e `GET /usuarios/<id>` serializam o campo `senha` de cada usuário.
Impact: qualquer cliente obtém a chave secreta e as senhas (hoje em texto puro, F-007) de todos os usuários, inclusive do admin.
Recommendation: DTO de saída sem campos sensíveis; health sem configuração interna (Playbook P-04). **Exige contrato** (CT-05, CT-06); na Opção 1 a chave é mantida com valor neutralizado.

### [CRITICAL] F-007 · SEC-06 Senhas armazenadas e comparadas em texto puro
File: database.py:75-83; models.py:109-111, 126-129
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-256 / A02:2021
Evidência: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`
Description: o cadastro grava a senha recebida sem transformação, o seed também, e o login compara por igualdade dentro do SQL.
Impact: qualquer leitura do banco (F-005, F-006, F-008 ou o arquivo `loja.db`) revela todas as senhas reutilizáveis.
Recommendation: hash com KDF (`werkzeug.security`, já instalado com o Flask), verificação com `check_password_hash` e migração do texto puro no próximo login (Playbook P-03).

### [CRITICAL] F-008 · SEC-01 SQL Injection
File: models.py:47-50, 57-61, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 289-299
Ocorrências: 10 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-89 / A03:2021
Evidência: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`
Description: valores do corpo JSON (`nome`, `descricao`, `categoria` no PUT, `email`, `senha`, `usuario_id`, `itens[].produto_id`) e da query string (`q`, `categoria`) são concatenados no SQL. Exemplos rastreados: `email = "admin@loja.com' --"` entra como admin sem senha; `usuario_id = "1, 'aprovado', 0) --"` cria pedido aprovado com total 0; `produto_id = "1 OR 1=1"` baixa o estoque de todos os produtos. As demais concatenações (models.py:28, 68, 92, 174, 188, 192, 220, 224, 279-281) recebem inteiros do conversor `<int:...>`, valor em whitelist ou ids internos: não exploráveis hoje, mas seguem o mesmo padrão e serão parametrizadas junto.
Impact: bypass de login, leitura/alteração arbitrária do banco e fraude em pedidos/estoque por cliente anônimo.
Recommendation: placeholders `?` em todas as consultas (Playbook P-02).

### [CRITICAL] F-009 · ARC-01 God File (arquivos com 3+ papéis)
File: app.py:1-88; controllers.py:1-292; models.py:1-314
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: app.py: config (7-9) + rotas (11-32) + handlers com SQL (47-78) + boot (80-88)
Description: app.py acumula entrypoint, configuração, registro de rotas e controllers com acesso direto ao banco; controllers.py mistura HTTP, validação, regra de negócio, notificações e consultas SQL (264-290); models.py mistura SQL, regra de negócio (total/estoque 137-146, faixas de desconto 256-262) e serialização. Não há camada de serviço nem middleware.
Impact: regras não testáveis isoladamente; qualquer mudança atravessa os três arquivos.
Recommendation: separar em config/, database/, models/, services/, controllers/, routes/, middlewares/ com app factory (Playbook P-08, P-09, P-13).

### [HIGH] F-010 · SEC-12 Validação de entrada ausente ou frágil
File: controllers.py:43-46, 81-90, 118-121, 169-170, 195-201, 239-245; models.py:144-146, 163-166
Ocorrências: 8 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-20 / A03:2021
Evidência: `if produto["estoque"] < item["quantidade"]:` (sem checar quantidade > 0)
Description: `itens[].quantidade` negativa ou zero passa pela checagem de estoque, gera `total` negativo e **aumenta** o estoque (models.py:163-166); tipos não são validados (`preco: "abc"` ⇒ `TypeError` ⇒ 500); `preco_min=abc` ⇒ `ValueError` ⇒ 500; corpo ausente em `/login` e `/pedidos/<id>/status` ⇒ `AttributeError` ⇒ 500; PUT de produto não valida categoria nem tamanho do nome (diferente do POST); pedido aceito para `usuario_id` inexistente; status de pedido inexistente responde 200. Severidade HIGH porque chega a regra financeira e de estoque.
Impact: pedidos com valor negativo, estoque inflado, dados inconsistentes e erros 500 evitáveis.
Recommendation: validação de presença/tipo/faixa na borda, mesmas regras em criar/atualizar, checagem de existência das entidades (Playbook P-07). O 404 para pedido inexistente **exige contrato** (CT-09).

### [HIGH] F-011 · SEC-08 Dados pessoais em logs
File: controllers.py:161, 179, 182
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-532 / A09:2021
Evidência: `print("Login falhou: " + email)`
Description: e-mails de usuários (PII) são escritos na saída padrão em cadastro e em cada tentativa de login, com sucesso ou não.
Impact: PII e trilha de tentativas de login em logs sem controle de acesso.
Recommendation: logger estruturado com mascaramento de e-mail (Playbook P-15).

### [HIGH] F-012 · SEC-15 Criação de pedido sem transação / condição de corrida
File: models.py:133-169
Ocorrências: 1 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-362 / CWE-367 / A04:2021
Evidência: checagem `if produto["estoque"] < item["quantidade"]` (144) separada da baixa `UPDATE produtos SET estoque = estoque - ...` (163-166)
Description: a verificação de estoque e a baixa ocorrem em laços separados, sem operação atômica nem bloqueio; não há rollback: uma exceção depois do `INSERT` do pedido (148-151) deixa a escrita pendente na conexão global compartilhada (database.py:10), que será confirmada pelo próximo `commit()` de qualquer outra requisição.
Impact: estoque negativo sob concorrência; pedidos sem itens ou com total divergente persistidos.
Recommendation: transação explícita com rollback e baixa condicional `... WHERE id = ? AND estoque >= ?` checando `rowcount` (Playbook P-10).

### [HIGH] F-013 · ARC-04 Acoplamento forte sem injeção de dependência
File: app.py:3-4, 49, 66; controllers.py:2-3, 266
Ocorrências: 5 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `db = get_db()` dentro de handlers HTTP (app.py:49, 66; controllers.py:266)
Description: handlers de rota obtêm a conexão diretamente e importam módulos concretos; não há app factory nem composition root.
Impact: impossível substituir banco/serviços em teste (os testes precisam copiar o projeto e subir um processo).
Recommendation: app factory (`create_app`), acesso a dados só na camada de models e serviços injetados (Playbook P-13, P-08).

### [HIGH] F-014 · ARC-02 Lógica de negócio em controller/rota
File: app.py:47-57, 59-78; controllers.py:43-54, 208-210, 247-250, 264-290
Ocorrências: 6 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `categorias_validas = ["informatica", "moveis", ...]` e `print("ENVIANDO EMAIL: Pedido " ...)` no handler
Description: regras de domínio (categorias válidas, limites de nome), orquestração de notificações por status e persistência direta (reset, query, contagens do health) estão nos handlers.
Impact: regras duplicadas e não reutilizáveis; handlers difíceis de testar.
Recommendation: mover para services (`ProdutoService`, `PedidoService`, `NotificacaoService`…) e manter handlers finos (Playbook P-09).

### [HIGH] F-015 · ARC-03 Conexão de banco global e mutável
File: database.py:4-10
Ocorrências: 1 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `global db_connection` … `sqlite3.connect(db_path, check_same_thread=False)`
Description: uma única conexão de módulo é compartilhada por todas as threads do servidor, com a verificação de thread desligada.
Impact: transações implícitas de requisições diferentes se misturam (ver F-012); concorrência sem isolamento.
Recommendation: conexão por requisição (`flask.g` + `teardown_appcontext`) criada pela camada de dados (Playbook P-13).

### [MEDIUM] F-016 · SEC-17 Falta de proteções HTTP básicas
File: app.py:6-9, 21
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-770 / CWE-693 / A05:2021
Evidência: `CORS(app)` e nenhum `after_request`/limiter registrado (busca por `limiter|talisman|after_request` sem resultado)
Description: sem limitação de taxa no `/login`, sem cabeçalhos de segurança (`X-Content-Type-Options`, `X-Frame-Options`…) e CORS aberto (ver F-003).
Impact: força bruta de senha sem atrito; respostas sem endurecimento básico.
Recommendation: cabeçalhos de segurança aditivos; rate limit no login (exige dependência nova, classe C) (Playbook P-19).

### [MEDIUM] F-017 · SEC-13 Detalhes internos de exceção nas respostas
File: app.py:77-78; controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Ocorrências: 17 · Confiança: CONFIRMED · Categoria: Segurança
CWE/OWASP: CWE-209 / A05:2021
Evidência: `return jsonify({"erro": str(e)}), 500`
Description: o texto da exceção (mensagens do SQLite, `TypeError`, `KeyError`) é devolvido ao cliente; não há handler central de erros.
Impact: revela schema, consultas e detalhes de implementação, facilitando F-008.
Recommendation: handler central que registra a exceção e responde mensagem genérica no mesmo formato (Playbook P-06). Conteúdo da mensagem 500 listado como CT-07 (formato mantido).

### [MEDIUM] F-018 · SEC-16 Dependências sem auditoria e runtime não declarado
File: requirements.txt:1-2
Ocorrências: 2 · Confiança: SUSPECTED · Categoria: Segurança
CWE/OWASP: CWE-1104 / A06:2021
Evidência: `flask-cors==5.0.1`
Description: versões fixadas sem lockfile/hashes e sem versão de Python declarada; conhecimento prévio indica avisos de segurança para a linha 5.0.x do flask-cors corrigidos na 6.x — **não confirmado** (a skill não consulta rede/CVE). Todas as dependências declaradas são importadas.
Impact: possível exposição a vulnerabilidades conhecidas de CORS.
Recommendation: rodar `pip-audit -r requirements.txt` (classe C) e atualizar conforme o resultado; declarar a versão de Python (Playbook P-18 — recomendação manual).

### [MEDIUM] F-019 · ARC-09 Tratamento de erro ruim e respostas inconsistentes
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Ocorrências: 17 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `except Exception as e:` em todos os handlers; erros ora `{"erro": ...}`, ora `{"erro": ..., "sucesso": False}` (controllers.py:20, 183, 206), ora `{"status": "erro", "detalhes": ...}` (controllers.py:292)
Description: captura genérica em cada handler transforma erros de cliente (JSON inválido, tipo errado) em 500; três formatos de erro diferentes.
Impact: clientes não conseguem tratar erros de forma uniforme; falhas de validação mascaradas como erro de servidor.
Recommendation: exceções de domínio + handler central com formato único (Playbook P-06).

### [MEDIUM] F-020 · ARC-08 Código duplicado
File: controllers.py:28-46, 72-90; models.py:12-21, 31-40, 79-86, 95-102, 177-200, 210-232, 304-313
Ocorrências: 4 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: mapeamento `"id": row["id"], "nome": row["nome"], ...` de produto repetido 3 vezes
Description: serialização de produto (×3), de usuário (×2), montagem de pedido com itens (×2) e validação de criar/atualizar produto (×2) duplicadas.
Impact: correções precisam ser replicadas (ex.: a validação de categoria já divergiu entre criar e atualizar).
Recommendation: funções únicas de serialização e validação (Playbook P-16).

### [MEDIUM] F-021 · ARC-11 Carga total, `SELECT *` e consultas redundantes
File: controllers.py:266-274; models.py:7, 75, 206, 239-254
Ocorrências: 5 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: cinco consultas separadas em `relatorio_vendas` (`COUNT`, `SUM`, três `COUNT ... WHERE status`)
Description: listagens carregam tabelas inteiras com `SELECT *`; o relatório faz 5 consultas onde uma agregação com `CASE` resolve; o health faz 4 consultas (uma delas, `SELECT 1`, descartada).
Impact: custo crescente com o volume; tráfego de colunas desnecessárias (incluindo `senha`).
Recommendation: colunas explícitas e agregação única; paginação apenas como parâmetro opcional (Playbook P-11).

### [MEDIUM] F-022 · ARC-10 Integridade referencial ausente
File: database.py:14-53; models.py:65-70
Ocorrências: 2 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `usuario_id INTEGER,` / `email TEXT,` sem `REFERENCES`, `NOT NULL` ou `UNIQUE`
Description: nenhuma FK, `NOT NULL` ou `UNIQUE(email)`; excluir produto deixa `itens_pedido` órfãos (exibidos como "Desconhecido", models.py:196, 228); e-mails duplicados aceitos.
Impact: dados inconsistentes e ambiguidade no login por e-mail.
Recommendation: checagens de existência/unicidade no serviço e restrições no schema para bancos novos; migração do `loja.db` existente é recomendação manual (Playbook P-10).

### [MEDIUM] F-023 · ARC-12 Dinheiro em ponto flutuante
File: database.py:19, 41, 51; models.py:146, 256-262
Ocorrências: 4 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `preco REAL,` · `total = total + (produto["preco"] * item["quantidade"])`
Description: preço, total e preço unitário em `REAL`; total e descontos calculados em `float`.
Impact: erros de arredondamento acumulados em totais e no relatório.
Recommendation: cálculo com `Decimal` e arredondamento a 2 casas, mantendo o formato numérico da resposta; troca do tipo armazenado exige migração (Playbook P-17).

### [MEDIUM] F-024 · ARC-07 Queries N+1
File: models.py:139-141, 154-156, 187-199, 219-231
Ocorrências: 4 · Confiança: CONFIRMED · Categoria: Arquitetura
CWE/OWASP: n/a
Evidência: `cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))` e `cursor3` por item dentro do laço
Description: `GET /pedidos` e `GET /pedidos/usuario/<id>` executam 1 + P + I consultas; criar pedido consulta cada produto duas vezes.
Impact: latência proporcional ao número de pedidos e itens.
Recommendation: `JOIN` de pedidos, itens e produtos em uma consulta; leitura única por produto (Playbook P-11).

### [MEDIUM] F-025 · OUTRO-01 Regra de status de pedido incompleta
File: controllers.py:242-250; models.py:275-283
Ocorrências: 2 · Confiança: LIKELY · Categoria: Outro
CWE/OWASP: CWE-840 / A04:2021
Evidência: `print("NOTIFICAÇÃO: Pedido " + str(pedido_id) + " cancelado. Devolver estoque.")`
Description: qualquer transição de status é aceita (ex.: `entregue` → `pendente`, `cancelado` → `aprovado`) e o cancelamento não devolve o estoque, embora a própria mensagem indique essa intenção (intenção inferida, não confirmada).
Impact: estoque perdido em cancelamentos; histórico de pedido incoerente.
Recommendation: definir máquina de estados e devolução de estoque no serviço de pedidos após decisão do dono do produto (muda comportamento; recomendação manual, padrão equivalente P-09/P-10).

### [LOW] F-026 · TST-02 Instruções de teste ausentes
File: README.md:5-12
Ocorrências: 1 · Confiança: CONFIRMED · Categoria: Testes
CWE/OWASP: n/a
Evidência: README tem só `pip install -r requirements.txt` e `python app.py`
Description: o README documenta instalar e rodar, mas não como executar a suíte (`requirements-dev.txt`, `pytest`, porta 5000 livre); não há CI (ausência — referência no README).
Impact: novos colaboradores não sabem validar mudanças.
Recommendation: documentar `pip install -r requirements-dev.txt` e `python -m pytest` (recomendação manual).

### [LOW] F-027 · QLT-04 `print` no lugar de logger
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Ocorrências: 19 · Confiança: CONFIRMED · Categoria: Qualidade
CWE/OWASP: n/a
Evidência: `print("ERRO CRITICO ao criar pedido: " + str(e))`
Description: todo o log é feito por `print`, sem nível nem formato.
Impact: impossível filtrar/configurar logs por ambiente.
Recommendation: módulo `logging` configurado na inicialização (Playbook P-15).

### [LOW] F-028 · QLT-02 Nomes ruins / que sombreiam builtins
File: controllers.py:14, 56, 64, 98, 136, 160; models.py:24, 54, 65, 89, 187, 191, 219, 223
Ocorrências: 14 · Confiança: CONFIRMED · Categoria: Qualidade
CWE/OWASP: n/a
Evidência: `id = models.criar_produto(...)` · `cursor2`, `cursor3`
Description: `id` sombreia o builtin; `cursor2`/`cursor3` não descrevem o conteúdo.
Impact: legibilidade.
Recommendation: nomes descritivos (`produto_id`, `itens_cursor`) (Playbook P-16).

### [LOW] F-029 · QLT-01 Magic numbers e strings soltas
File: app.py:36; controllers.py:47-50, 52, 242, 285; models.py:256-262
Ocorrências: 5 · Confiança: CONFIRMED · Categoria: Qualidade
CWE/OWASP: n/a
Evidência: `if faturamento > 10000: desconto = faturamento * 0.1`
Description: faixas de desconto, limites de nome (2/200), lista de categorias, lista de status e versão `"1.0.0"` (duplicada em app.py:36 e controllers.py:285) como literais.
Impact: regras escondidas e sujeitas a divergência.
Recommendation: constantes nomeadas no domínio/config (Playbook P-16).

### [LOW] F-030 · QLT-05 Estilo inconsistente
File: controllers.py:200; models.py:63, 70, 283
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Qualidade
CWE/OWASP: n/a
Evidência: `if not itens or len(itens) == 0:`
Description: condição redundante; funções que sempre `return True` sem que o valor seja usado; concatenação com `str()` em vez de f-strings em todo o código.
Impact: ruído de leitura.
Recommendation: simplificar (Playbook P-16).

### [LOW] F-031 · QLT-03 Imports e código mortos
File: controllers.py:268; database.py:2; models.py:2
Ocorrências: 3 · Confiança: CONFIRMED · Categoria: Qualidade
CWE/OWASP: n/a
Evidência: `import os` (database.py:2) e `import sqlite3` (models.py:2) sem uso; `cursor.execute("SELECT 1")` com resultado descartado
Description: confirmados por busca de uso no projeto.
Impact: ruído; dependências aparentes falsas.
Recommendation: remover (Playbook P-16).

## Descartados / falsos positivos
- SEC-10 em controllers.py:146-162 — descartado porque `tipo` não é lido do corpo; `models.criar_usuario` usa o padrão `"cliente"`.
- SEC-11 (IDOR) em controllers.py:222 — descartado porque não existe identidade no fluxo; coberto por F-003 (regra do catálogo).
- SEC-14 em models.py:146 — descartado porque o total é calculado no servidor com o preço do banco; não há pagamento simulado.
- SEC-01 em models.py:28, 68, 92, 174, 188, 192, 220, 224, 279-281 — não exploráveis hoje (conversor `<int:...>`, whitelist de status em controllers.py:242, ids internos); serão parametrizadas junto com F-008 por consistência.
- SEC-04 fora de app.py:59-78 — nenhum `eval`/`exec`/`subprocess`/`pickle`/`yaml` encontrado.
- ARC-05 — código síncrono, sem callbacks.
- ARC-06 — nenhum handler de um domínio dentro de módulo de outro; mistura de papéis tratada em F-009/F-014.
- DEP: nenhuma encontrada para Python 3.14.0 / Flask 3.1.1 / flask-cors 5.0.1 (busca por `utcnow`, `utcfromtimestamp`, `before_first_request`, `JSONEncoder`, `flask.escape`, `imp`, `distutils`, adaptadores de datetime do `sqlite3`/`detect_types`: sem resultado).
- TST-01 — existe suíte (23 testes de integração HTTP em tests/).
- TST-03 — testes importam apenas pytest, requests e stdlib, presentes no `.venv`; nenhum import de módulo inexistente.

## Correções que exigem mudança de contrato
| ID | Rota/campo | Mudança | Sev. | Motivo (Finding) | Impacto para clientes | Resolvido na Opção 1? | Prova prevista na Opção 2 |
|---|---|---|---|---|---|---|---|
| CT-01 | POST /admin/query | remover a rota (404) | CRITICAL | F-005, F-004 | deixa de existir execução de SQL via HTTP | não (fica residual) | teste novo: rota ⇒ 404 |
| CT-02 | POST /admin/reset-db | exigir token de administrador (sem token 401; não-admin 403) | CRITICAL | F-004 | enviar `Authorization: Bearer <token admin>` | não (fica residual) | teste novo: 401 e 403 (caminho de sucesso não exercitado: destrutivo) |
| CT-03 | GET /relatorios/vendas | exigir token de administrador | CRITICAL | F-004 | enviar token de admin | não (fica residual) | teste novo: 401/403/200 |
| CT-04 | POST /login + rotas de dados (escrita de produtos; /usuarios GET; /pedidos; /pedidos/usuario/<id>; /pedidos/<id>/status) | login passa a devolver `token` em `dados` (aditivo); rotas exigem Bearer; perfil admin para escrita de produtos, listagem de usuários/pedidos e status; dono ou admin para pedidos do usuário. Continuam públicas: GET /, GET /produtos*, GET /health, POST /usuarios, POST /login | CRITICAL | F-003 | autenticar via `/login` e enviar o token | não (fica residual) | testes novos: 401 sem token, 403 sem perfil/propriedade, 200 com token |
| CT-05 | GET /usuarios, GET /usuarios/<id> · campo `senha` | omitir o campo | CRITICAL | F-006 | deixa de receber `senha` | sim (chave mantida com `null`) | teste novo: `senha` ausente |
| CT-06 | GET /health · `secret_key`, `db_path`, `debug` | omitir os campos | CRITICAL | F-006 | deixa de receber configuração interna | sim (chaves mantidas com `null`) | teste novo: campos ausentes |
| CT-07 | respostas 500 (todas as rotas) · `erro` | texto da exceção → mensagem genérica; formato mantido | MEDIUM | F-017 | não depender do texto do erro | sim (formato mantido) | não comprovável por teste sem provocar falha interna (verificação estática) |
| CT-08 | CORS (todas as rotas) | origens restritas por `CORS_ORIGINS` | HIGH | F-003, F-016 | origens não configuradas deixam de receber `Access-Control-Allow-Origin` | não (fica residual) | teste novo: `Origin` não permitida ⇒ sem cabeçalho |
| CT-09 | PUT /pedidos/<id>/status | pedido inexistente: 200 → 404 | HIGH | F-010 | tratar 404 | não (fica residual parcial em F-010) | teste novo: id inexistente ⇒ 404 |

Resumo para a pergunta: 9 correções exigem contrato; na Opção 1 ficam residuais 3 CRITICAL (F-003, F-004, F-005) e 1 HIGH parcial (F-010, só o 404 de pedido inexistente).

## Testes afetados
| Teste | Motivo (C-xx/CT-xx) | Classe (T1/T2/T4) | Ajuste previsto |
|---|---|---|---|
| tests/conftest.py::api | C-01 (senhas de seed por variável de ambiente) | T1 | definir `SEED_ADMIN_PASSWORD`/`SEED_CLIENTE_PASSWORD` no `env` do processo da aplicação; asserções inalteradas |
| tests/conftest.py::api (Opção 2) | CT-02, CT-03, CT-04 | T1 | cliente faz login como admin e envia `Authorization`; fixture adicional de cliente anônimo |
| tests/test_api.py: test_listar_usuarios_seed, test_buscar_usuario, test_criar_usuario, test_crud_produto, test_atualizar_e_deletar_produto_inexistente, test_criar_produto_validacoes, test_criar_pedido_* (4), test_atualizar_status_pedido, test_relatorio_vendas (Opção 2) | CT-03, CT-04 | T1 | só autenticação via fixture; asserções idênticas |
| tests/test_contratos.py (novo, Opção 2) | CT-01…CT-06, CT-08, CT-09 | T4 | provas 401/403/404/campos ausentes/CORS, com execução vermelha no checkpoint |

## Plano de mudanças
| ID | Mudança | Sev. | Resolve | Arquivos | Padrão | Afeta contrato | Depende de |
|---|---|---|---|---|---|---|---|
| C-01 | Módulo de config por ambiente (`SECRET_KEY`, `APP_DEBUG`, `APP_HOST`, `APP_PORT`, `DB_PATH`, `CORS_ORIGINS`, senhas de seed); debug desligado e bind `127.0.0.1` por padrão; seed sem senha literal; `.env.example` | CRITICAL | F-001, F-002 | app.py, config/settings.py (novo), database/seed.py, .env.example (novo), tests/conftest.py (T1) | P-01 | não | — |
| C-02 | Extrair `database/` (conexão, schema, seed) e `models/` por entidade com consultas parametrizadas; pedido em transação com rollback e baixa condicional de estoque; `NOT NULL`/`UNIQUE(email)` no schema de bancos novos | CRITICAL | F-008, F-012, F-022 (parcial), F-009 (parcial) | database.py → database/, models.py → models/ | P-08, P-02, P-10 | não | C-01 |
| C-03 | Hash de senha com `werkzeug.security`; rehash de texto puro no login; seed com hash | CRITICAL | F-007 | models/usuario_model.py, services/usuario_service.py, database/seed.py | P-03 | não | C-02 |
| C-04 | Camada `services/` (produtos, usuários, pedidos, relatório, notificações); regras de total, estoque e descontos com `Decimal` fora de controllers/models | CRITICAL | F-014, F-009, F-023 (parcial) | services/ (novo), controllers | P-09 | não | C-02 |
| C-05 | Validação na borda: tipos, faixas, `quantidade` inteira > 0, existência de usuário/produto, mesmas regras em criar/atualizar, JSON ausente ⇒ 400, e-mail único ⇒ 400 | HIGH | F-010 | controllers/, services/ | P-07 | CT-09 (só o 404 de pedido inexistente) | C-04 |
| C-06 | DTOs de saída: sem `senha`; health sem configuração interna (Opção 1: chaves com `null`; Opção 2: omitidas) | CRITICAL | F-006 | models/, controllers/ | P-04 | CT-05, CT-06 | C-02 |
| C-07 | Autenticação por token assinado (`itsdangerous`, já dependência do Flask), decorators de perfil/propriedade, remoção de `/admin/query`, proteção de `/admin/reset-db` e `/relatorios/vendas` (**só Opção 2**) | CRITICAL | F-003, F-004, F-005 | middlewares/auth.py (novo), routes/, controllers/ | P-05 | CT-01, CT-02, CT-03, CT-04 | C-01, C-03, C-06 |
| C-08 | Handler central de erros, exceções de domínio, formato único; fim do `str(e)` nas respostas | MEDIUM | F-017, F-019 | middlewares/error_handler.py (novo), controllers/ | P-06 | CT-07 (formato mantido) | C-04 |
| C-09 | `logging` configurado; e-mail mascarado; fim dos `print` | HIGH | F-011, F-027 | config/, controllers/, services/ | P-15 | não | C-04 |
| C-10 | `JOIN` em pedidos/itens, leitura única por produto, agregação única no relatório e no health, colunas explícitas | MEDIUM | F-024, F-021 (parcial: sem paginação) | models/ | P-11 | não | C-02 |
| C-11 | App factory `create_app()`, blueprints em `routes/`, controllers em `controllers/`, conexão por requisição (`flask.g` + teardown) | HIGH | F-015, F-013, F-009 | app.py, routes/ (novo), controllers/ (novo), database/ | P-13 | não | C-02, C-04 |
| C-12 | Cabeçalhos de segurança aditivos; CORS restrito por `CORS_ORIGINS` (**só Opção 2**) | MEDIUM | F-016 (parcial), F-003 (CORS) | middlewares/security.py (novo), app.py | P-19 | CT-08 | C-01, C-11 |
| C-13 | Constantes de domínio, nomes descritivos, remoção de imports/código mortos, serialização/validação únicas | MEDIUM | F-020, F-028, F-029, F-030, F-031 | todos os módulos novos | P-16 | não | C-02…C-12 |

Ordem de aplicação: C-01 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07 → C-08 → C-09 → C-10 → C-11 → C-12 → C-13 (P-14: nenhuma API deprecated; P-18: só recomendação).

Recomendações manuais (sem `C-xx`):
- F-018: rodar `pip-audit -r requirements.txt` (classe C) e atualizar `flask-cors` conforme o resultado; declarar a versão de Python.
- F-025: definir máquina de estados de pedido e devolução de estoque no cancelamento (decisão de negócio).
- F-026: documentar no README como instalar dependências de desenvolvimento e rodar `python -m pytest`.
- F-016 (parcial): rate limit no `/login` exige dependência nova (ex.: `flask-limiter`, classe C).
- F-021 (parcial): paginação com limite padrão muda o contrato das listagens.
- F-022/F-023 (parcial): migrar o `loja.db` existente para FKs com enforcement e valores monetários em tipo exato (comando destrutivo, classe D).
- F-001: rotacionar a `SECRET_KEY` e a senha do admin já presentes no histórico git.

## Plano de comandos
| ID | Comando | Finalidade | Origem | Classe | Efeitos colaterais |
|---|---|---|---|---|---|
| K-00 | `git branch refactor-arch/checkpoint-20261105-175512` | checkpoint do código original (árvore limpa, HEAD 5303107) | 07 §2.2 | C | cria ref de branch local; sem commit |
| K-01 | `git worktree add "<scratchpad>/checkpoint-original" refactor-arch/checkpoint-20261105-175512` | cópia do código original para a prova vermelha (só Opção 2) | 06 §8.9 | C | diretório fora do projeto + metadados em `.git/worktrees` |
| K-02 | listar `.venv/Lib/site-packages` / `pip show flask flask-cors pytest requests` | confirmar dependências | requirements.txt, requirements-dev.txt | A | nenhum (já presentes; nenhuma instalação prevista) |
| K-03 | `.venv/Scripts/python.exe -m pytest` | baseline V1 e validação final (a fixture sobe `python app.py` numa cópia temporária, porta 5000) | pytest.ini:1-3; tests/conftest.py:79-83 | B | `.pytest_cache`, `__pycache__`, cópia em diretório temporário do pytest |
| K-04 | `.venv/Scripts/python.exe -m compileall -q <arquivos/pacotes>` | V5 após cada bloco | toolchain Python | B | `__pycache__` |
| K-05 | `.venv/Scripts/python.exe -c "from app import app; print(sorted(r.rule for r in app.url_map.iter_rules()))"` | V5: rotas registram | app.py | B | nenhum (importar não toca o banco) |
| K-06 | `netstat -ano \| findstr :5000` | porta livre antes/depois | 06 §5 | A | nenhum |
| K-07 | `.venv/Scripts/python.exe -m pytest tests/test_contratos.py` na cópia do checkpoint | prova vermelha (só Opção 2) | 06 §8.9 | B (na cópia) | copia o teste novo para a cópia do checkpoint |
| K-08 | `git worktree remove "<scratchpad>/checkpoint-original"` | limpeza da cópia (só Opção 2) | — | C | remove a cópia |
| — | `pip-audit -r requirements.txt` | auditoria de dependências (F-018) | catálogo SEC-16 | C | rede + instalação de ferramenta; **não planejado** (recomendação) |
| — | `POST /admin/reset-db` | rota destrutiva do projeto | app.py:47 | D | apaga todas as tabelas; **nunca** executada automaticamente |

## Plano de validação
| Degrau | Disponível? | Comando (origem, classe) | Observação |
|---|---|---|---|
| V1 Testes do projeto | sim | `.venv/Scripts/python.exe -m pytest` (pytest.ini:1-3, B) | 23 testes de integração caixa-preta via HTTP; sobem a aplicação real |
| V2 Script de verificação do projeto | não | — | sem lint/check/CI no repositório |
| V3 Boot + requisições existentes | parcial | boot `python app.py` coberto pela fixture de V1 (conftest.py:79-96, espera `/health`) | não há coleção/`curl` versionados |
| V4 Sondagem ad hoc | não aplicável | — | V1 cobre as 16 rotas não administrativas + `/` (P4 não será perguntada) |
| V5 Estático | sempre | K-04, K-05 (B) | compilar e listar rotas |
| Pré-requisitos | | nenhum (dependências presentes no `.venv`) | — |
| Testes afetados previstos | | conftest.py (T1, C-01); Opção 2: T1 de autenticação + T4 em tests/test_contratos.py | seção "Testes afetados" |
| Prova prevista por `CT-xx` (Opção 2) | | teste novo para CT-01…CT-06, CT-08, CT-09; CT-07 verificação estática | vermelho no checkpoint (K-01/K-07) |
| Não exercitável | | `POST /admin/reset-db` (destrutiva), `POST /admin/query` (execução de SQL) | fora da bateria automática |

## Decisões do usuário
- P1 Escopo: "Sim, aplicar todas" (C-01…C-13)
- P2 Modo de comandos: "Equilibrado (recomendado)"
- P3 Contrato: "Atualizar contrato" — Opção 2 (CT-01…CT-09 aplicados com testes que comprovem)
- P4 Sondagem ad hoc: não aplicável (V1 cobre as rotas)

================================
Total: 31 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

---
# ANEXO — FASE 3 (Run id: 20261105-175512)

## Decisões do usuário (registro)
- Escopo: todas (C-01…C-13)
- Modo de comandos: Equilibrado
- Contrato: Opção 2 — atualizar (CT-01, CT-02, CT-03, CT-04, CT-05, CT-06, CT-07, CT-08, CT-09 aplicados)
- Sondagem ad hoc: não aplicável (V1 cobre as rotas)
- Lote classe C (K-00, K-01, K-08): "Executar todos"

## Estrutura DEPOIS
```
code-smells-project/
├── app.py                      composition root: create_app(), montagem de dependências, boot
├── .env.example                nomes das variáveis (valores fictícios)
├── config/        settings.py (ambiente), logging_config.py (logger + máscara de e-mail)
├── database/      connection.py (conexão por requisição), schema.py (DDL), seed.py
├── models/        produto_model.py, usuario_model.py, pedido_model.py, sistema_model.py
├── services/      produto_, usuario_, pedido_, relatorio_, notificacao_, sistema_, auth_service.py,
│                  constantes.py, dinheiro.py, excecoes.py
├── controllers/   produto_, usuario_, pedido_, relatorio_, sistema_controller.py, validacao.py
├── views/         serializers.py (DTOs), respostas.py (envelope)
├── routes/        blueprints por domínio (produto_, usuario_, pedido_, relatorio_, sistema_routes.py)
├── middlewares/   auth.py, error_handler.py, security.py
└── tests/         conftest.py (T1), test_api.py (inalterado), test_contratos.py (T4)
```

| Métrica | ANTES | DEPOIS |
|---|---|---|
| Arquivos-fonte | 4 | 44 (6 `__init__.py` vazios) |
| Linhas de código (aprox.) | ~780 | ~1257 (mesmo método: contagem de linhas por arquivo) |
| Camadas presentes | entrypoint, controllers, models (misturados) | config, database, models, services, controllers, views, routes, middlewares, composition root |
| Maior arquivo | models.py (314) | controllers/validacao.py (134) |
| Arquivos com 3+ papéis | 3 | 0 |

### Mapa antigo → novo
| Arquivo original | Destino(s) |
|---|---|
| app.py | app.py (composition root), config/settings.py, routes/*.py, controllers/sistema_controller.py, middlewares/security.py; `POST /admin/query` removida (CT-01) |
| controllers.py (removido) | controllers/*_controller.py, controllers/validacao.py, services/notificacao_service.py, views/respostas.py, views/serializers.py |
| models.py (removido) | models/*_model.py (SQL parametrizado), services/*_service.py (regras), views/serializers.py |
| database.py (removido) | database/connection.py, database/schema.py, database/seed.py, config/settings.py |
| — (novos) | services/auth_service.py, middlewares/auth.py, middlewares/error_handler.py, services/excecoes.py, services/constantes.py, services/dinheiro.py, config/logging_config.py, .env.example |

## Mudanças aplicadas
| ID | Status | Observação |
|---|---|---|
| C-01 | aplicada | config/settings.py lê tudo do ambiente; debug desligado e bind `127.0.0.1` por padrão; sem `SECRET_KEY` ⇒ chave aleatória por processo + aviso em log; seed de usuários só com `SEED_ADMIN_PASSWORD`/`SEED_CLIENTE_PASSWORD`; `.env.example` criado |
| C-02 | aplicada | models por domínio com placeholders `?`; pedido em transação (`with conexao`) com baixa condicional `estoque >= ?` + `rowcount`; `NOT NULL`/`UNIQUE(email)` no DDL de bancos novos |
| C-03 | aplicada | `werkzeug.security` (scrypt); senha legada em texto puro migra para hash no próximo login (`hmac.compare_digest`) |
| C-04 | aplicada | services para produtos, usuários, pedidos, relatório, notificações e sistema; total e descontos em `Decimal` com `ROUND_HALF_UP`, mantendo saída numérica |
| C-05 | aplicada | validação de tipo/faixa (quantidade inteira > 0, ids inteiros, preço numérico, estoque inteiro), mesmas regras no POST e no PUT, JSON ausente/inválido ⇒ 400, e-mail inválido/duplicado ⇒ 400, usuário inexistente no pedido ⇒ 400, status de pedido inexistente ⇒ 404 (CT-09) |
| C-06 | aplicada | DTOs com lista branca; `senha` e `secret_key`/`db_path`/`debug` omitidos (CT-05, CT-06) |
| C-07 | aplicada | token assinado (`itsdangerous`, expira em `TOKEN_MAX_AGE`); `requer_autenticacao(perfis)` + `garantir_dono_ou_admin`; `/admin/query` removida; `/admin/reset-db` exige admin **e** `ALLOW_DESTRUCTIVE=true` |
| C-08 | aplicada | `AppError` + handler global; 500 com mensagem genérica e detalhe só no log (CT-07); todo corpo de erro passa a ter `"sucesso": false` (chave aditiva); `HTTPException` mantém a resposta padrão do Flask |
| C-09 | aplicada | `logging` configurado; nenhum `print`; e-mail mascarado (`jo***@dominio`) e ids no lugar de PII |
| C-10 | aplicada (parcial) | `LEFT JOIN` em pedidos/itens/produtos, uma leitura de produtos por pedido, agregação única no relatório e no health, colunas explícitas; paginação não aplicada (residual F-021) |
| C-11 | aplicada | `create_app()`, blueprints, serviços montados no composition root e injetados por construtor; conexão por requisição (`flask.g` + `teardown_appcontext`); schema/seed na primeira conexão (com trava) |
| C-12 | aplicada (parcial) | cabeçalhos `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`; CORS restrito a `CORS_ORIGINS` (CT-08); rate limit não aplicado (exige dependência nova; residual F-016) |
| C-13 | aplicada | constantes de domínio, nomes descritivos (`produto_id`, `usuario_id`), serialização e validação únicas, imports mortos removidos |

## Contratos — resultado
**Opção 2 (atualizar):**

| CT | Rota/campo | Antes → Depois | Por que (F-xxx, CWE/OWASP) | Impacto e como adaptar o cliente | Prova (E-nn) |
|---|---|---|---|---|---|
| CT-01 | POST /admin/query | executa SQL livre → removida (404) | F-005, F-004 · CWE-94/306 · A03/A01 | nenhuma alternativa via HTTP | E-03 verde; E-05 vermelho (200 no original) |
| CT-02 | POST /admin/reset-db | anônimo apaga o banco → 401 sem token, 403 não-admin, 403 admin sem `ALLOW_DESTRUCTIVE=true` | F-004 · CWE-306 · A01 | enviar token de admin e habilitar a flag no ambiente; sucesso não exercitado (destrutivo) | E-03 verde; E-05 vermelho (200 no original) |
| CT-03 | GET /relatorios/vendas | aberta → só admin (401/403) | F-004 · CWE-306 · A01 | `Authorization: Bearer <token admin>` | E-03 verde; E-05 vermelho |
| CT-04 | POST /login · rotas de dados | login devolve também `dados.token`; escrita de produtos, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status` só admin; `GET /usuarios/<id>`, `GET /pedidos/usuario/<id>`, `POST /pedidos` só dono ou admin; públicas: `/`, `/health`, `GET /produtos*`, `POST /usuarios`, `POST /login` | F-003 · CWE-306/862 · A01/A07 | autenticar via `/login` e enviar `Authorization: Bearer <token>` | E-03 verde (5 testes); E-05 vermelho (4) + guarda de rotas públicas verde nos dois |
| CT-05 | GET /usuarios, GET /usuarios/<id> · `senha` | devolvida → omitida | F-006 · CWE-200 · A02 | não depender do campo | E-03 verde; E-05 vermelho |
| CT-06 | GET /health · `secret_key`, `db_path`, `debug` | devolvidos → omitidos | F-006 · CWE-200 · A02 | não depender dos campos | E-03 verde; E-05 vermelho |
| CT-07 | respostas 500 · `erro` | `str(e)` → "Erro interno do servidor" (formato mantido) | F-017 · CWE-209 · A05 | não depender do texto | verificação estática (busca por `str(e)` vazia); não comprovável por teste sem provocar falha interna |
| CT-08 | CORS | qualquer origem (refletida) → só `CORS_ORIGINS` (vazio por padrão) | F-003, F-016 · CWE-942 · A05 | configurar `CORS_ORIGINS` com as origens do front | E-03 verde; E-05 vermelho (origem refletida no original) |
| CT-09 | PUT /pedidos/<id>/status | inexistente 200 → 404 | F-010 · CWE-20 · A03 | tratar 404 | E-03 verde; E-05 vermelho |

**Texto-base para o README (seção Resultados):**
> A refatoração (refactor-arch, Run id 20261105-175512) alterou o contrato de 14 rotas por razões de segurança, com aprovação do usuário na rodada de perguntas (Opção 2). `POST /admin/query`, que executava SQL arbitrário, foi removida. As rotas de dados e as administrativas passaram a exigir `Authorization: Bearer <token>`, emitido por `POST /login`, com checagem de perfil e de propriedade. `senha`, `secret_key`, `db_path` e `debug` deixaram de sair nas respostas, e o CORS passou a aceitar só as origens de `CORS_ORIGINS`. A justificativa de cada mudança está em `reports/audit-project-1.md` ("Contratos — resultado"). As provas estão em `tests/test_contratos.py`, verdes no código novo (E-03) e vermelhas no código original (E-05).

## Alterações em testes
| Teste | Motivo | Classe | Antes/Depois (trecho do diff) | Asserções | Reexecução | Snapshot |
|---|---|---|---|---|---|---|
| tests/conftest.py::api (fixture) | C-01 (senhas de seed por ambiente), CT-02/03/04 (autenticação) | T1 | `def api(tmp_path_factory)` → `servidor` (sobe o app com `SEED_ADMIN_PASSWORD`/`SEED_CLIENTE_PASSWORD` no `env`) + `api` (cliente com token de admin) + `api_anonimo`; `Cliente(base)` → `Cliente(base, token=None)` | nenhuma asserção no arquivo; tests/test_api.py **inalterado** (23 testes, mesmas asserções) | E-03 (35 passed) | `tests-before/tests/conftest.py` |
Diff completo: `E-06-diff-testes.patch`. Integridade: `git status -- tests/` mostra só `M tests/conftest.py` e `?? tests/test_contratos.py`, igual ao registrado.

## Testes adicionados (Opção 2)
| Teste | CT/F | O que comprova | Verde (código refatorado) | Vermelho (checkpoint original) |
|---|---|---|---|---|
| test_contratos.py::test_ct01_admin_query_removida | CT-01 / F-005 | rota ⇒ 404 (anônimo e admin) | E-03 | E-05 (falhou) |
| ::test_ct03_relatorio_exige_admin | CT-03 / F-004 | sem token 401, token inválido 401, cliente 403, admin 200 | E-03 | E-05 (falhou) |
| ::test_ct04_login_emite_token | CT-04 / F-003 | `dados.token` presente | E-03 | E-05 (falhou) |
| ::test_ct04_rotas_de_dados_exigem_token | CT-04 / F-003 | 9 chamadas sem token ⇒ 401 | E-03 | E-05 (falhou) |
| ::test_ct04_cliente_sem_perfil_admin | CT-04 / F-003 | cliente ⇒ 403 em rotas de admin | E-03 | E-05 (falhou) |
| ::test_ct04_cliente_acessa_apenas_os_proprios_dados | CT-04 / F-003 | dados de terceiros 403; próprios 200/201 | E-03 | E-05 (falhou) |
| ::test_ct04_rotas_publicas_continuam_abertas | CT-04 (limite) | rotas públicas seguem 200 sem token | E-03 | E-05 passou — guarda de regressão, verde nos dois por definição (sensibilidade não aplicável) |
| ::test_ct05_usuarios_sem_senha | CT-05 / F-006 | `senha` ausente na listagem e no detalhe | E-03 | E-05 (falhou) |
| ::test_ct06_health_sem_configuracao_interna | CT-06 / F-006 | campos de configuração ausentes | E-03 | E-05 (falhou) |
| ::test_ct08_cors_nao_libera_origem_desconhecida | CT-08 / F-003 | sem `Access-Control-Allow-Origin` para origem não permitida | E-03 | E-05 (falhou) |
| ::test_ct09_status_de_pedido_inexistente_404 | CT-09 / F-010 | 404 + `sucesso: false` | E-03 | E-05 (falhou) |
| ::test_ct02_reset_db_exige_admin | CT-02 / F-004 | 401/401/403/403 e banco preservado | E-03 | E-05 (falhou) |

## Evidências de execução
(`E-00` — Fase 1 — foi gravado na Fase 2; ver `06-protocolo-validacao.md`, seção 7.)

### E-01 · Suíte pytest (baseline)
Comando:      `.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider`      Diretório: code-smells-project
Origem:       K-03 · pytest.ini:1-3 · Classe B · Autorização: automática (classe B)
Início/Fim:   2026-11-05T18:06:29-03:00 → 2026-11-05T18:06:34-03:00 (duração 3,90 s)        Exit code: 0
Ambiente:     Python 3.14.0, pytest 9.2.0, Flask 3.1.1, flask-cors 5.0.1 (.venv)
Resultado:    passed 23 | failed 0 | skipped 0
Saída (fim):
  tests/test_api.py::test_atualizar_status_pedido PASSED                   [ 95%]
  tests/test_api.py::test_relatorio_vendas PASSED                          [100%]
  ============================= 23 passed in 3.90s ==============================
Bruto:        reports/evidence/project-1/20261105-175512/E-01-baseline-pytest.log
Integridade:  testes alterados/adicionados: 0 (verificado por: git diff HEAD -- tests/ vazio)

### E-02 · Rotas registradas (baseline, V5)
Comando:      `.venv/Scripts/python.exe -B -c "from app import app; ...url_map"`      Diretório: code-smells-project
Origem:       K-05 · Classe B · Autorização: automática
Início/Fim:   2026-11-05T18:06:42-03:00 → 2026-11-05T18:06:42-03:00        Exit code: 0
Resultado:    19 rotas da API (+ `/static`), incluindo `POST /admin/query`
Bruto:        reports/evidence/project-1/20261105-175512/E-02-baseline-rotas.log

### E-03 · Suíte pytest (após refatoração)
Comando:      `.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider`      Diretório: code-smells-project
Origem:       K-03 · pytest.ini:1-3 · Classe B · Autorização: automática (classe B)
Início/Fim:   2026-11-05T18:16:48-03:00 → 2026-11-05T18:16:55-03:00 (duração 6,04 s)        Exit code: 0
Ambiente:     Python 3.14.0, pytest 9.2.0, Flask 3.1.1, flask-cors 5.0.1 (.venv)
Resultado:    passed 35 | failed 0 | skipped 0   (baseline E-01: passed 23 | failed 0 | skipped 0; os 23 originais continuam passando + 12 novos)
Saída (fim):
  tests/test_contratos.py::test_ct09_status_de_pedido_inexistente_404 PASSED [ 97%]
  tests/test_contratos.py::test_ct02_reset_db_exige_admin PASSED           [100%]
  ============================= 35 passed in 6.04s ==============================
Bruto:        reports/evidence/project-1/20261105-175512/E-03-final-pytest.log
Integridade:  testes alterados/adicionados: 2 (conftest.py T1; test_contratos.py T4) — ver "Alterações em testes" / "Testes adicionados" (verificado por: git status/diff -- tests/ e tests-before/)

### E-04 · Compilação e rotas registradas (após refatoração, V5)
Comando:      `.venv/Scripts/python.exe -m compileall -q app.py config database models services controllers views middlewares routes` + listagem do `url_map`      Diretório: code-smells-project
Origem:       K-04, K-05 · Classe B · Autorização: automática
Início/Fim:   2026-11-05T18:17:00-03:00 → 2026-11-05T18:17:01-03:00        Exit code: 0 / 0
Resultado:    compila; 18 rotas da API (+ `/static`) — mesmas do baseline menos `POST /admin/query` (CT-01); aviso esperado de `SECRET_KEY` ausente
Bruto:        reports/evidence/project-1/20261105-175512/E-04-final-v5-rotas.log

### E-05 · Testes de contrato contra o checkpoint original (prova de sensibilidade)
Comando:      `<.venv>/Scripts/python.exe -m pytest tests/test_contratos.py -v -p no:cacheprovider --tb=line`      Diretório: worktree do checkpoint (`refactor-arch/checkpoint-20261105-175512`, HEAD 5303107), com conftest.py e test_contratos.py novos copiados
Origem:       K-07 · 06 §8.9 · Classe B (na cópia) · Autorização: lote C aprovado (K-01) + automática
Início/Fim:   2026-11-05T18:17:14-03:00 → 2026-11-05T18:17:18-03:00        Exit code: 1 (esperado)
Resultado:    failed 11 | passed 1 (test_ct04_rotas_publicas_continuam_abertas — guarda verde por definição)
Saída (fim):
  E   AssertionError: assert 200 == 401   (POST /admin/reset-db anônimo no original)
  ======================== 11 failed, 1 passed in 3.28s =========================
Bruto:        reports/evidence/project-1/20261105-175512/E-05-vermelho-checkpoint.log

### E-06 · Diff dos testes
Comando:      `git diff HEAD -- tests/conftest.py tests/test_api.py` + `git diff --no-index <vazio> tests/test_contratos.py`
Origem:       06 §8.5 · Classe A
Resultado:    conftest.py: +28/−4 (T1); test_api.py: sem diferenças; test_contratos.py: novo (T4)
Bruto:        reports/evidence/project-1/20261105-175512/E-06-diff-testes.patch · snapshots em `tests-before/tests/`

### Comparação antes/depois (rotas)
| Método | Rota | ANTES | DEPOIS | Resultado | Prova |
|---|---|---|---|---|---|
| GET | / | 200 {endpoints, mensagem, versao} | 200 {mesmas chaves} | igual | E-01, E-03 (test_raiz) |
| GET | /produtos | 200 | 200 (público) | igual | E-01, E-03 |
| GET | /produtos/busca | 200 | 200 (público) | igual | E-01, E-03 |
| GET | /produtos/<id> | 200/404 | 200/404 (público) | igual | E-01, E-03 |
| POST | /produtos | 201/400 anônimo | 201/400 com admin; 401/403 sem token/cliente | ALTERADO (aprovado CT-04) | E-03, E-05 |
| PUT | /produtos/<id> | 200/404 anônimo | 200/404 com admin; 401/403 | ALTERADO (aprovado CT-04) | E-03, E-05 |
| DELETE | /produtos/<id> | 200/404 anônimo | 200/404 com admin; 401/403 | ALTERADO (aprovado CT-04) | E-03, E-05 |
| GET | /usuarios | 200 com `senha` | 200 admin sem `senha`; 401/403 | ALTERADO (aprovado CT-04, CT-05) | E-03, E-05 |
| GET | /usuarios/<id> | 200/404 com `senha` | 200/404 dono ou admin sem `senha`; 401/403 | ALTERADO (aprovado CT-04, CT-05) | E-03, E-05 |
| POST | /usuarios | 201/400 | 201/400 (público) | igual (P-07: e-mail inválido/duplicado também ⇒ 400) | E-01, E-03 |
| POST | /login | 200 {id,nome,email,tipo}/401/400 | 200 + `token`/401/400 | ALTERADO (aprovado CT-04, aditivo) | E-03, E-05 |
| POST | /pedidos | 201/400 anônimo | 201/400 dono ou admin; 401/403 | ALTERADO (aprovado CT-04) | E-03, E-05 |
| GET | /pedidos | 200 | 200 admin; 401/403 | ALTERADO (aprovado CT-04) | E-03, E-05 |
| GET | /pedidos/usuario/<id> | 200 | 200 dono ou admin; 401/403 | ALTERADO (aprovado CT-04) | E-03, E-05 |
| PUT | /pedidos/<id>/status | 200/400 (200 até para inexistente) | 200/400/404 admin; 401/403 | ALTERADO (aprovado CT-04, CT-09) | E-03, E-05 |
| GET | /relatorios/vendas | 200 | 200 admin; 401/403 | ALTERADO (aprovado CT-03) | E-03, E-05 |
| GET | /health | 200 com `secret_key`, `db_path`, `debug` | 200 sem esses campos | ALTERADO (aprovado CT-06) | E-03, E-05 |
| POST | /admin/reset-db | 200 anônimo (apaga o banco) | 401/403; admin + `ALLOW_DESTRUCTIVE=true` | ALTERADO (aprovado CT-02); caminho de sucesso NÃO EXERCITADO (destrutivo) | E-03, E-05 |
| POST | /admin/query | 200 (SQL arbitrário) | 404 (removida) | ALTERADO (aprovado CT-01) | E-03, E-04, E-05 |
Divergências não aprovadas: nenhuma. Os 23 testes de caracterização originais passam sem alteração de asserções (E-03).

### Resumo da validação
| Degrau | Comando | Resultado | Evidência |
|---|---|---|---|
| V1 (baseline) | `.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider` | passed 23 / failed 0 / skipped 0 | E-01 |
| V1 (final) | mesmo comando | passed 35 / failed 0 / skipped 0 | E-03 |
| V3 | boot real `python app.py` pela fixture (espera `/health` 200) | subiu nas duas execuções | E-01, E-03 |
| V5 | compileall + `url_map` | compila; 19 → 18 rotas (CT-01) | E-02, E-04 |
| Prova vermelha | testes de contrato no checkpoint | failed 11 / passed 1 (guarda) | E-05 |
Veredito: VALIDADO (V1) — V3 coberto pelo boot da fixture; sem coleção de requisições no projeto.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — Python 3.14.0 (.venv/pyvenv.cfg; pytest relata Python 3.14.0) (E-00, E-01)
- [x] Framework detectado corretamente — Flask 3.1.1 (requirements.txt:1 + `Flask(__name__)` + site-packages flask-3.1.1) (E-00)
- [x] Domínio da aplicação descrito corretamente — e-commerce: produtos, usuários, pedidos, relatório (tabelas e rotas) (E-00)
- [x] Número de arquivos analisados condiz com a realidade — 4 arquivos-fonte, 780 linhas por `wc -l`; `git ls-files` confirma os mesmos 4 `.py` fora de tests/ (E-00)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência — seções e ordem do `03-template-relatorio.md` §3 neste arquivo
- [x] Cada finding tem arquivo e linhas exatos — linhas relidas no Read/cat -n da Fase 1 (ex.: F-008 models.py:109-111; F-002 app.py:8, 88)
- [x] Findings ordenados por severidade (CRITICAL → LOW) — F-001…F-009 CRITICAL, F-010…F-015 HIGH, F-016…F-025 MEDIUM, F-026…F-031 LOW
- [x] Mínimo de 5 findings identificados — 31
- [x] Detecção de APIs deprecated incluída (se aplicável) — buscada; "DEP: nenhuma encontrada para Python 3.14.0 / Flask 3.1.1 / flask-cors 5.0.1" em "Descartados"
- [x] Skill pausa e pede confirmação antes da Fase 3 — linha `Phase 2 complete...` + perguntas P1–P3 respondidas ("Decisões do usuário")

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — config/, database/, models/, services/, controllers/, views/, routes/, middlewares/, app.py; 0 arquivos com 3+ papéis (E-04)
- [x] Configuração extraída para módulo de config (sem hardcoded) — config/settings.py; busca por `minha-chave|admin123|debug=True|0.0.0.0` no código-fonte vazia (literal de teste só em tests/conftest.py)
- [x] Models criados para abstrair dados — models/*_model.py; SQL só em models/ e database/, todo parametrizado (concatenações restantes só de constantes internas)
- [x] Views/Routes separadas para visualização ou roteamento — routes/*_routes.py (mapeamento + middleware por rota) e views/ (DTOs e envelope)
- [x] Controllers concentram o fluxo da aplicação — controllers/*_controller.py validam, chamam services e escolhem a resposta; sem SQL (busca por `sqlite3|.conexao()` vazia em controllers/)
- [x] Error handling centralizado — middlewares/error_handler.py:11-22; busca por `str(e)|except Exception|except:` vazia fora dele
- [x] Entry point claro — app.py:53-85 (`create_app()` + `python app.py`, mesmo comando do README)
- [x] Aplicação inicia sem erros — boot pela fixture com `/health` 200 (E-03); import e rotas ok (E-04)
- [x] Endpoints originais respondem corretamente — 5 de 19 rotas iguais; 14 alteradas por contrato aprovado (CT-01…CT-09) com prova E-03/E-05; 0 divergências; os 23 testes originais passam (E-03)

## Itens residuais (reauditoria)
Varredura do catálogo reaplicada ao código novo (busca por sinais + releitura): 0 CRITICAL, 0 HIGH. Residuais:
- F-016 (MEDIUM, parcial) — sem rate limit no `/login`; exige dependência nova (ex.: `flask-limiter`, classe C). Cabeçalhos e CORS foram corrigidos.
- F-018 (MEDIUM, SUSPECTED) — dependências não auditadas; rodar `pip-audit -r requirements.txt` (classe C) e declarar a versão de Python.
- F-021 (MEDIUM, parcial) — listagens sem paginação (limite padrão mudaria o contrato); N+1, `SELECT *` e consultas redundantes resolvidos.
- F-022 (MEDIUM, parcial) — sem FKs com enforcement; `NOT NULL`/`UNIQUE` só em bancos novos; o `loja.db` existente exige migração (classe D).
- F-023 (MEDIUM, parcial) — colunas monetárias continuam `REAL` (migração classe D); os cálculos usam `Decimal`.
- F-025 (MEDIUM) — máquina de estados do pedido e devolução de estoque no cancelamento: decisão de negócio, não aplicada.
- F-026 (LOW) — README sem instruções de teste e sem as novas variáveis de ambiente (recomendação manual; texto-base acima).
Recomendação adicional: rotacionar a `SECRET_KEY` e a senha do admin que seguem no histórico git (F-001). No `loja.db` local já existente, as senhas antigas continuam em texto puro até o próximo login de cada usuário, quando migram para hash.

## Observações da execução
- Stack detectada e confiança: Python 3.14.0 + Flask 3.1.1, confiança alta (manifesto + import + instanciação).
- Dicas específicas usadas × derivadas do sinal abstrato: todas com dicas Python/Flask do catálogo; OUTRO-01 (F-025) fora do catálogo.
- Nível de organização encontrado e como a Fase 3 se adaptou: `parcialmente-em-camadas`; os papéis misturados foram movidos para camadas próprias, e services, views e middlewares, que não existiam, foram criados. Foram reaproveitados os diretórios não versionados que só tinham `__pycache__` de execução anterior. Os módulos `controllers.py`, `models.py` e `database.py` foram removidos e substituídos pelos pacotes.
- Falsos positivos descartados: 10 (seção "Descartados").
- Limitações da validação: o caminho de sucesso de `POST /admin/reset-db` não foi exercitado (destrutivo). CT-07 foi verificado só estaticamente. Não há coleção de requisições, então V3 = boot da fixture.
- Tentativas/iterações na Fase 3 e reversões: suíte verde na primeira execução; 1 ajuste de nomenclatura em routes/ (`as c` → `as controller`) antes da validação final; nenhuma reversão.
- Arquivos criados pela execução fora do código-fonte: branch local `refactor-arch/checkpoint-20261105-175512` (mantido; o usuário decide removê-lo). Worktree temporária no scratchpad, removida com `git worktree remove --force`; o `--force` foi necessário porque os testes novos tinham sido copiados para ela. `__pycache__` gerados por compileall/pytest (ignorados pelo git). Diretórios temporários do pytest. Nenhuma instalação de pacote.
- Ambiente: no Bash do agente, comandos com variáveis de shell ou `mkdir` falharam (exit 127) sem executar nada; cópias e criação de pasta foram feitas via PowerShell. Isso não afetou nenhuma evidência.
- Nada foi commitado; alterações ficam no working tree da branch `code-smells-20261105-v2`.
