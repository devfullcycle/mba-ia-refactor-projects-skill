# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

---

## Análise Manual

### CRITICAL

#### 1. Hardcoded SECRET_KEY
- **Arquivo:** `app.py:13`
- **Problema:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` — chave secreta do Flask hardcoded no código-fonte.
- **Impacto:** Qualquer pessoa com acesso ao repo pode forjar sessões e tokens.
- **Severidade:** CRITICAL

#### 2. Hardcoded SMTP Credentials
- **Arquivo:** `services/notification_service.py:9-10`
- **Problema:** `self.email_user = 'taskmanager@gmail.com'` e `self.email_password = 'senha123'` — credenciais de email hardcoded.
- **Impacto:** Credenciais de email expostas no código-fonte. Vazamento no Git compromete a conta de email.
- **Severidade:** CRITICAL

#### 3. Weak Cryptography (MD5)
- **Arquivo:** `models/user.py:29, 32`
- **Problema:** `hashlib.md5(pwd.encode()).hexdigest()` usado para hashing de senhas. MD5 é criptograficamente quebrado e não tem salt.
- **Impacto:** Senhas podem ser recuperadas via rainbow tables em segundos. Database leak expõe todas as senhas.
- **Severidade:** CRITICAL

### HIGH

#### 4. Password in to_dict()
- **Arquivo:** `models/user.py:23`
- **Problema:** O método `to_dict()` do User inclui o campo `password` (hash da senha). Esse método é usado nas respostas da API em `routes/user_routes.py:85` (após criação) e `routes/user_routes.py:129` (após update).
- **Impacto:** Hash de senha retornado em endpoints de criação/atualização de usuário. Facilita ataques de força bruta offline.
- **Severidade:** HIGH

#### 5. Fake JWT Token
- **Arquivo:** `routes/user_routes.py:211`
- **Problema:** Após login, retorna `'token': 'fake-jwt-token-' + str(user.id)` — não é um JWT real, não tem assinatura, não tem expiração.
- **Impacto:** Sistema de autenticação é simbólico. Qualquer pessoa pode forjar tokens sabendo o ID do usuário.
- **Severidade:** HIGH

#### 6. Password Returned on User Creation
- **Arquivo:** `routes/user_routes.py:85`
- **Problema:** Após criar usuário, retorna `user.to_dict()` que inclui o hash da senha no response.
- **Impacto:** Hash de senha exposto na resposta do POST `/users`.
- **Severidade:** HIGH

### MEDIUM

#### 7. Deprecated datetime.utcnow()
- **Arquivo:** `models/task.py:15-16, 52`, `models/user.py:14`, `routes/report_routes.py:35,42,45,71`
- **Problema:** `datetime.utcnow()` está deprecated desde Python 3.12. O correto é `datetime.now(timezone.utc)`.
- **Impacto:** Gera warnings em Python 3.12+ e pode quebrar em versões futuras. Retorna naive datetime sem timezone.
- **Severidade:** MEDIUM

#### 8. Deprecated Model.query.get()
- **Arquivo:** `routes/user_routes.py:29`, `routes/report_routes.py:105, 192, 216`
- **Problema:** `User.query.get(id)` e `Category.query.get(id)` estão deprecated no SQLAlchemy 2.x. O correto é `db.session.get(Model, id)`.
- **Impacto:** Gera deprecation warnings e será removido em versão futura do SQLAlchemy.
- **Severidade:** MEDIUM

#### 9. Duplicated Overdue Logic
- **Arquivo:** `routes/task_routes.py:30-39`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`
- **Problema:** A mesma lógica de verificação de overdue (due_date < now E status != done/cancelled) está copiada 3 vezes em arquivos diferentes. Existe `Task.is_overdue()` no model mas não é usado nos routes.
- **Impacto:** Mudança na regra de overdue precisa ser replicada em 3 arquivos. O model tem o método mas os routes reimplementam a lógica.
- **Severidade:** MEDIUM

#### 10. Business Logic in Routes (sem Controllers)
- **Arquivo:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Problema:** Apesar da separação em models/routes/services, não existe camada de controllers. Os routes contêm validação, lógica de negócio, serialização manual e chamadas diretas ao banco.
- **Impacto:** Lógica de negócio acoplada ao HTTP. Impossível reutilizar em outro contexto (CLI, tests, etc.).
- **Severidade:** MEDIUM

#### 11. N+1 Queries
- **Arquivo:** `routes/report_routes.py:53-68`, `routes/task_routes.py:42-57`
- **Problema:** No summary_report, para cada usuário faz query de tasks; no get_tasks, para cada task faz query de user e category. Com 50 usuários de 20 tasks = 1.000+ queries.
- **Impacto:** Performance degrada com o volume de dados. Relatórios ficam lentos.
- **Severidade:** MEDIUM

### LOW

#### 12. Bare Except Clauses
- **Arquivo:** `routes/task_routes.py:62`, `routes/user_routes.py:130`, `routes/report_routes.py:186, 188, 222`
- **Problema:** Múltiplos `except:` sem tipo específico de exceção. Podem capturar `SystemExit`, `KeyboardInterrupt` e esconder bugs.
- **Impacto:** Erros reais podem ser engolidos silenciosamente, dificultando debug.
- **Severidade:** LOW

#### 13. Debug Mode Enabled
- **Arquivo:** `app.py:34`
- **Problema:** `app.run(debug=True)` habilita o debugger interativo do Flask.
- **Impacto:** Em produção, expõe stack traces detalhados e permite execução arbitrária de código.
- **Severidade:** LOW

#### 14. Unused Imports
- **Arquivo:** `routes/task_routes.py:7` (`os`, `sys`, `time`), `app.py:7` (`sys`, `json`), `routes/user_routes.py:6` (`json`)
- **Problema:** Módulos importados mas não utilizados no código.
- **Impacto:** Polui o código e pode causar confusão sobre dependências reais.
- **Severidade:** LOW
