# MBA IA - Refactor Projects Skill

## A) Análise Manual

### code-smells-project (Python/Flask — E-commerce API)

#### CRITICAL

**1. SQL Injection**
- **Arquivo:** `models.py:28, 48-49, 58-60, 68, 92, 109-110, 127-128, 140, 155, 159, 163-165, 174, 187-199, 220, 279, 291-297`
- **Problema:** Todas as queries SQL usam string concatenation em vez de parâmetros preparados. Exemplo: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` e `cursor.execute("INSERT INTO ... VALUES ('" + nome + "', ...")`.
- **Impacto:** Qualquer input do usuário pode injetar SQL arbitrário no banco. Um atacante pode ler, modificar ou deletar todos os dados.

**2. Hardcoded SECRET_KEY**
- **Arquivo:** `app.py:7`
- **Problema:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — a chave secreta do Flask está hardcoded no código-fonte.
- **Impacto:** Qualquer pessoa com acesso ao código pode forjar sessões e tokens do Flask.

**3. Hardcoded Passwords no Seed**
- **Arquivo:** `database.py:76-83`
- **Problema:** Senhas de usuários seed hardcoded: `"admin123"`, `"123456"`, `"senha123"`. Senhas armazenadas em plaintext no banco.
- **Impacto:** Credenciais expostas no código-fonte, senhas fracas e sem hash.

**4. SQL Execution Endpoint (sem autenticação)**
- **Arquivo:** `app.py:59-78`
- **Problema:** Endpoint `/admin/query` aceita SQL arbitrário via body (`dados.get("sql")`) e executa diretamente no banco, sem nenhuma autenticação.
- **Impacto:** Qualquer pessoa pode executar qualquer SQL no banco — DROP TABLE, DELETE, SELECT em dados sensíveis.

**5. Unauthenticated Admin Routes**
- **Arquivo:** `app.py:47-78`
- **Problema:** `/admin/reset-db` e `/admin/query` não possuem qualquer middleware de autenticação ou autorização.
- **Impacto:** Qualquer usuário anônimo pode resetar o banco inteiro ou executar queries arbitrárias.

#### HIGH

**6. God File (models.py)**
- **Arquivo:** `models.py:1-315`
- **Problema:** Arquivo único de 315 linhas contém toda a lógica de acesso ao banco para 4 domínios diferentes (produtos, usuários, pedidos, relatórios). Mistura queries SQL, serialização e regras de negócio.
- **Impacto:** Impossível testar em isolamento. Qualquer mudança em um domínio pode quebrar outro. Violação total do SRP (Single Responsibility Principle).

**7. Password Exposure em API Responses**
- **Arquivo:** `models.py:83-86` (get_todos_usuarios), `models.py:94-102` (get_usuario_por_id), `controllers.py:289-290` (health_check)
- **Problema:** Os endpoints de listagem/busca de usuários retornam o campo `senha`. O health check expõe `secret_key` e `debug` no response.
- **Impacto:** Senhas e secrets visíveis para qualquer consumidor da API.

**8. Business Logic in Controllers**
- **Arquivo:** `controllers.py:208-210` (notificações), `controllers.py:247-251` (notificações de status)
- **Problema:** Notificações (email, SMS, push) são simuladas via `print()` diretamente nos controllers. Lógica de negócio misturada com apresentação.
- **Impacto:** Impossível testar notificações, impossível trocar o mecanismo sem alterar o controller.

#### MEDIUM

**9. N+1 Query Problem**
- **Arquivo:** `models.py:186-201` (get_pedidos_usuario), `models.py:218-231` (get_todos_pedidos)
- **Problema:** Para cada pedido, uma query busca os itens; para cada item, outra query busca o nome do produto. Com 100 pedidos de 5 itens cada = 600 queries ao invés de 1 JOIN.
- **Impacto:** Performance degrada linearmente com o volume de pedidos.

**10. Duplicated Code**
- **Arquivo:** `models.py:171-201` vs `models.py:203-233`
- **Problema:** `get_pedidos_usuario()` e `get_todos_pedidos()` são quase idênticas — só diferem no WHERE. A serialização de produtos em dicts está repetida 5+ vezes (linhas 10-21, 29-40, 78-87, 93-102, 302-313).
- **Impacto:** Manutenção difícil — mudanças precisam ser replicadas em múltiplos lugares.

**11. Duplicated Validation Logic**
- **Arquivo:** `controllers.py:28-55` vs `controllers.py:64-95`
- **Problema:** A validação de produto (nome obrigatório, preco obrigatório, estoque obrigatório, preço negativo, etc.) está duplicada entre `criar_produto` e `atualizar_produto`.
- **Impacto:** Mudança de regra de negócio precisa ser feita em 2+ lugares.

#### LOW

**12. Debug Mode Enabled**
- **Arquivo:** `app.py:8`, `app.py:88`
- **Problema:** `app.config["DEBUG"] = True` e `app.run(debug=True)`.
- **Impacto:** Em produção, expõe stack traces detalhados e permite execução de código via debugger.

**13. Magic Numbers**
- **Arquivo:** `models.py:257-262`
- **Problema:** Thresholds de desconto hardcoded: `> 10000` (10%), `> 5000` (5%), `> 1000` (2%). Sem constantes nomeadas.
- **Impacto:** Difícil entender a regra de negócio sem ler o código. Mudanças exigem caça aos números.

**14. print() como Logging**
- **Arquivo:** `controllers.py:8, 57, 106, 161, 179, 208-210, 218, 248-250` e `database.py:56`
- **Problema:** Uso de `print()` em vez de um framework de logging estruturado. Mensagens como `"ERRO: " + str(e)` sem nível ou contexto.
- **Impacto:** Impossível filtrar logs por nível, enviar para sistema externo ou rastrear em produção.

---

### ecommerce-api-legacy (Node.js/Express — LMS API com Checkout)

#### CRITICAL

**1. Hardcoded Credentials**
- **Arquivo:** `src/utils.js:2-5`
- **Problema:** Senha do banco (`"senha_super_secreta_prod_123"`), chave do gateway de pagamento (`"pk_live_1234567890abcdef"`), credenciais SMTP — tudo hardcoded no código-fonte.
- **Impacto:** Qualquer pessoa com acesso ao repo tem credenciais de produção. Vazamento no Git expõe todos os sistemas integrados.

**2. Weak Cryptography**
- **Arquivo:** `src/utils.js:17-23`
- **Problema:** Função `badCrypto()` faz um loop de 10.000 iterações concatenando os 2 primeiros chars de base64, depois trunca para 10 chars. Não é hash, não tem salt, é trivialmente reversível.
- **Impacto:** Senhas dos usuários não estão protegidas. Qualquer database leak expõe todas as senhas.

**3. Credit Card Logging**
- **Arquivo:** `src/AppManager.js:45`
- **Problema:** `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` — loga o número completo do cartão de crédito e a chave do gateway no console.
- **Impacto:** Violação de PCI-DSS. Números de cartão ficam em logs accessíveis a qualquer operador do sistema.

#### HIGH

**4. God Class (AppManager)**
- **Arquivo:** `src/AppManager.js:1-141`
- **Problema:** Classe única responsável por: inicializar o banco, criar tabelas, popular seeds, definir todas as rotas, processar pagamentos, gerenciar matrículas, gerar relatórios, deletar usuários. 141 linhas fazendo tudo.
- **Impacto:** Impossível testar qualquer funcionalidade isoladamente. Qualquer mudança afeta o sistema inteiro.

**5. Business Logic in Route Handler**
- **Arquivo:** `src/AppManager.js:28-78`
- **Problema:** O handler do `/api/checkout` faz tudo: valida input, busca curso, busca/cria usuário, processa pagamento (com lógica de cartão), cria matrícula, cria pagamento, cria audit log, faz cache. Tudo em um único handler.
- **Impacto:** Impossível reutilizar lógica de pagamento, matrícula ou criação de usuário em outro contexto. Impossível testar unitariamente.

**6. Callback Hell**
- **Arquivo:** `src/AppManager.js:37-77`
- **Problema:** 4-5 níveis de callbacks aninhadas: `db.get()` → `db.get()` → `db.run()` → `db.run()` → `db.run()`. Usa `let self = this` para contornar escopo.
- **Impacto:** Código difícil de ler e manter. Erros em callbacks internas são difíceis de rastrear. Impossível usar try/catch para error handling.

**7. No Cascade Delete**
- **Arquivo:** `src/AppManager.js:131-137`
- **Problema:** DELETE de usuário remove da tabela `users` mas não limpa `enrollments` nem `payments`. A própria resposta diz: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`
- **Impacto:** Dados órfãos no banco. Relatórios financeiros quebram (referenciam usuários inexistentes).

#### MEDIUM

**8. N+1 Query Problem**
- **Arquivo:** `src/AppManager.js:83-128`
- **Problema:** O financial-report faz: para cada curso → query matrículas; para cada matrícula → query user; para cada matrícula → query payment. Com 10 cursos de 50 matrículas cada = 500+ queries ao invés de 1 JOIN.
- **Impacto:** Relatório financeiro fica cada vez mais lento conforme o sistema cresce.

**9. Global Mutable State**
- **Arquivo:** `src/utils.js:9-10`
- **Problema:** `let globalCache = {}` e `let totalRevenue = 0` — variáveis globais mutáveis exportadas como módulo. `totalRevenue` nunca é atualizado, `globalCache` é preenchido mas nunca lido de forma útil.
- **Impacto:** Estado compartilhado entre requests pode causar race conditions e comportamento imprevisível sob concorrência.

**10. In-Memory Database**
- **Arquivo:** `src/AppManager.js:8`
- **Problema:** `this.db = new sqlite3.Database(':memory:')` — todos os dados são perdidos quando o servidor reinicia.
- **Impacto:** Impossível usar em produção. Dados de matrículas, pagamentos e usuários desaparecem a cada restart.

#### LOW

**11. Poor Variable Naming**
- **Arquivo:** `src/AppManager.js:29-33`
- **Problema:** Variáveis com nomes obscuros: `u` (usuário), `e` (email), `p` (password), `cid` (course_id), `cc` (cartão de crédito). No financial-report: `enrPending`, `coursesPending` como contadores de callback.
- **Impacto:** Código difícil de entender. Novos desenvolvedores precisam decifrar o que cada variável representa.

**12. sqlite3 Verbose Mode**
- **Arquivo:** `src/AppManager.js:1`
- **Problema:** `require('sqlite3').verbose()` habilita tracing detalhado do SQLite, gerando logs excessivos em produção.
- **Impacto:** Polui logs com informações internas do driver SQLite.

**13. Generic Error Responses**
- **Arquivo:** `src/AppManager.js:passim`
- **Problema:** Erros retornam strings genéricas como `"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`. Sem códigos de erro estruturados, sem logs do erro real para o cliente.
- **Impacto:** Difícil debugar problemas. Clientes da API não têm informação útil para reportar.

---

### task-manager-api (Python/Flask — Task Manager)

#### CRITICAL

**1. Hardcoded SECRET_KEY**
- **Arquivo:** `app.py:13`
- **Problema:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` — chave secreta do Flask hardcoded no código-fonte.
- **Impacto:** Qualquer pessoa com acesso ao repo pode forjar sessões e tokens.

**2. Hardcoded SMTP Credentials**
- **Arquivo:** `services/notification_service.py:9-10`
- **Problema:** `self.email_user = 'taskmanager@gmail.com'` e `self.email_password = 'senha123'` — credenciais de email hardcoded.
- **Impacto:** Credenciais de email expostas no código-fonte. Vazamento no Git compromete a conta de email.

**3. Weak Cryptography (MD5)**
- **Arquivo:** `models/user.py:29, 32`
- **Problema:** `hashlib.md5(pwd.encode()).hexdigest()` usado para hashing de senhas. MD5 é criptograficamente quebrado e não tem salt.
- **Impacto:** Senhas podem ser recuperadas via rainbow tables em segundos. Database leak expõe todas as senhas.

#### HIGH

**4. Password in to_dict()**
- **Arquivo:** `models/user.py:23`
- **Problema:** O método `to_dict()` do User inclui o campo `password` (hash da senha). Esse método é usado nas respostas da API em `routes/user_routes.py:85` (após criação) e `routes/user_routes.py:129` (após update).
- **Impacto:** Hash de senha retornado em endpoints de criação/atualização de usuário. Facilita ataques de força bruta offline.

**5. Fake JWT Token**
- **Arquivo:** `routes/user_routes.py:211`
- **Problema:** Após login, retorna `'token': 'fake-jwt-token-' + str(user.id)` — não é um JWT real, não tem assinatura, não tem expiração.
- **Impacto:** Sistema de autenticação é simbólico. Qualquer pessoa pode forjar tokens sabendo o ID do usuário.

**6. Password Returned on User Creation**
- **Arquivo:** `routes/user_routes.py:85`
- **Problema:** Após criar usuário, retorna `user.to_dict()` que inclui o hash da senha no response.
- **Impacto:** Hash de senha exposto na resposta do POST `/users`.

#### MEDIUM

**7. Deprecated datetime.utcnow()**
- **Arquivo:** `models/task.py:15-16, 52`, `models/user.py:14`, `routes/report_routes.py:35,42,45,71`
- **Problema:** `datetime.utcnow()` está deprecated desde Python 3.12. O correto é `datetime.now(timezone.utc)`.
- **Impacto:** Gera warnings em Python 3.12+ e pode quebrar em versões futuras. Retorna naive datetime sem timezone.

**8. Deprecated Model.query.get()**
- **Arquivo:** `routes/user_routes.py:29`, `routes/report_routes.py:105, 192, 216`
- **Problema:** `User.query.get(id)` e `Category.query.get(id)` estão deprecated no SQLAlchemy 2.x. O correto é `db.session.get(Model, id)`.
- **Impacto:** Gera deprecation warnings e será removido em versão futura do SQLAlchemy.

**9. Duplicated Overdue Logic**
- **Arquivo:** `routes/task_routes.py:30-39`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`
- **Problema:** A mesma lógica de verificação de overdue (due_date < now E status != done/cancelled) está copiada 3 vezes em arquivos diferentes. Existe `Task.is_overdue()` no model mas não é usado nos routes.
- **Impacto:** Mudança na regra de overdue precisa ser replicada em 3 arquivos. O model tem o método mas os routes reimplementam a lógica.

**10. Business Logic in Routes (sem Controllers)**
- **Arquivo:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Problema:** Apesar da separação em models/routes/services, não existe camada de controllers. Os routes contêm validação, lógica de negócio, serialização manual e chamadas diretas ao banco.
- **Impacto:** Lógica de negócio acoplada ao HTTP. Impossível reutilizar em outro contexto (CLI, tests, etc.).

**11. N+1 Queries**
- **Arquivo:** `routes/report_routes.py:53-68`, `routes/task_routes.py:42-57`
- **Problema:** No summary_report, para cada usuário faz query de tasks; no get_tasks, para cada task faz query de user e category. Com 50 usuários de 20 tasks = 1.000+ queries.
- **Impacto:** Performance degrada com o volume de dados. Relatórios ficam lentos.

#### LOW

**12. Bare Except Clauses**
- **Arquivo:** `routes/task_routes.py:62`, `routes/user_routes.py:130`, `routes/report_routes.py:186, 188, 222`
- **Problema:** Múltiplos `except:` sem tipo específico de exceção. Podem capturar `SystemExit`, `KeyboardInterrupt` e esconder bugs.
- **Impacto:** Erros reais podem ser engolidos silenciosamente, dificultando debug.

**13. Debug Mode Enabled**
- **Arquivo:** `app.py:34`
- **Problema:** `app.run(debug=True)` habilita o debugger interativo do Flask.
- **Impacto:** Em produção, expõe stack traces detalhados e permite execução arbitrária de código.

**14. Unused Imports**
- **Arquivo:** `routes/task_routes.py:7` (`os`, `sys`, `time`), `app.py:7` (`sys`, `json`), `routes/user_routes.py:6` (`json`)
- **Problema:** Módulos importados mas não utilizados no código.
- **Impacto:** Polui o código e pode causar confusão sobre dependências reais.

---

## B) Construção da Skill

*A ser preenchido.*

## C) Resultados

*A ser preenchido.*

## D) Como Executar

*A ser preenchido.*
