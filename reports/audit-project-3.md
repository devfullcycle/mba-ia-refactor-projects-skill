# Architecture Audit Report — Projeto 3

> Gerado pela skill `/refactor-arch` — Fase 2: Auditoria

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy 3.1.1
Files:   11 analyzed | ~900 linhas de código
         app.py, database.py, seed.py
         models/task.py, models/user.py, models/category.py
         routes/task_routes.py, routes/user_routes.py, routes/report_routes.py
         services/notification_service.py, utils/helpers.py

## Summary
CRITICAL: 2 | HIGH: 3 | MEDIUM: 4 | LOW: 3
Total findings: 12

================================
PHASE 1: PROJECT ANALYSIS (recap)
================================
Language:      Python
Framework:     Flask 3.0.0 + SQLAlchemy 3.1.1
Database:      SQLite via SQLAlchemy ORM (tasks.db)
Domain:        Task Manager API (tarefas, usuários, categorias, relatórios)
Architecture:  Partial MVC — separação de camadas existe (models/, routes/, services/, utils/)
               mas contém problemas de segurança, duplicação e N+1 queries
Source files:  11 files analyzed
DB tables:     tasks, users, categories (via SQLAlchemy ORM)
================================
```

---

## Findings

### [CRITICAL] Hash de Senha com MD5 (Algoritmo Obsoleto e Inseguro)
**ID:** AP-05  
**File:** `models/user.py`  
**Lines:** 23–26  
**Description:** `set_password()` usa `hashlib.md5(password.encode()).hexdigest()` para armazenar senhas. MD5 não é adequado para hashing de senhas: é reversível via rainbow tables em segundos, não suporta salt, e está oficialmente deprecado para uso criptográfico desde 2004. `check_password()` compara MD5s diretamente.  
**Impact:** Qualquer banco comprometido expõe todas as senhas imediatamente. Ataques de dicionário são triviais.  
**Fix:** PT-04  
**Recommendation:** Substituir por `werkzeug.security.generate_password_hash()` com pbkdf2 e `check_password_hash()` no método `check_password()`.

---

### [CRITICAL] Credenciais SMTP Hardcoded no Serviço de Notificação
**ID:** AP-02  
**File:** `services/notification_service.py`  
**Lines:** 8–12 (estimado)  
**Description:** As credenciais de SMTP (`smtp_user`, `smtp_password`, servidor) estão hardcoded diretamente no código-fonte da classe `NotificationService`. Essas credenciais ficam expostas no repositório.  
**Impact:** Acesso não autorizado ao servidor de email; envio de spam ou phishing usando as credenciais comprometidas.  
**Fix:** PT-02  
**Recommendation:** Mover credenciais para variáveis de ambiente via `python-dotenv`.

---

### [HIGH] Password Exposto no to_dict() do Modelo User
**ID:** AP-06  
**File:** `models/user.py`  
**Lines:** 15–20 (estimado)  
**Description:** O método `to_dict()` do modelo `User` inclui o campo `password` no dicionário retornado. Este método é chamado nas rotas para serializar responses, expondo o hash da senha (mesmo que seja MD5) para qualquer cliente da API.  
**Impact:** Exposição de hashes de senha em todas as respostas que incluem objetos User.  
**Fix:** PT-11  
**Recommendation:** Remover `password` de `to_dict()`. Se necessário para uso interno, criar método separado `to_dict_admin()`.

---

### [HIGH] Lógica de "Overdue" Duplicada em 4 Locais
**ID:** AP-11  
**File:** `routes/task_routes.py`, `routes/report_routes.py`  
**Lines:** `task_routes.py:30–39, 71–80, ~150`; `report_routes.py:33–43, 132–135`  
**Description:** O cálculo de se uma tarefa está em atraso (`is_overdue`) é implementado com blocos if/else idênticos em pelo menos 4 locais diferentes nas routes. O modelo `Task` já tem um método `is_overdue()` mas as routes duplicam a lógica em vez de chamá-lo.  
**Impact:** Qualquer mudança na regra de "overdue" deve ser feita em 4 lugares; divergência silenciosa entre endpoints.  
**Fix:** PT-07  
**Recommendation:** Remover toda duplicação das routes e usar `task.is_overdue()` do modelo exclusivamente.

---

### [HIGH] N+1 Queries no Relatório e Contagem de Tarefas
**ID:** AP-10  
**File:** `routes/report_routes.py`  
**Lines:** `report_routes.py:~20–80` (GET /reports/summary)  
**Description:** O relatório de summary carrega TODAS as tasks do banco (`Task.query.all()`) em Python e itera sobre elas para calcular contagens por status, prioridade e atraso — em vez de usar `GROUP BY` e `COUNT()` direto no banco. Para 10.000 tasks, isso carrega e processa 10.000 objetos Python desnecessariamente.  
**Impact:** Degradação severa de performance com volumes maiores de dados; consumo excessivo de memória.  
**Fix:** PT-06 (adaptar para SQLAlchemy com `func.count()` e `group_by()`)  
**Recommendation:** Usar `db.session.query(Task.status, func.count()).group_by(Task.status).all()` em vez de iterar em Python.

---

### [MEDIUM] Serviço de Notificação Definido mas Nunca Chamado
**ID:** AP-11  
**File:** `services/notification_service.py`, `routes/task_routes.py`, `routes/user_routes.py`  
**Lines:** Serviço: arquivo completo; Rotas: sem imports do serviço  
**Description:** A classe `NotificationService` com métodos `notify_task_assigned()`, `notify_task_overdue()` e `send_email()` está definida mas não é importada nem chamada em nenhuma rota. É código morto que aumenta a superfície de ataque sem trazer benefício.  
**Impact:** Credenciais hardcoded em código não utilizado; dead code dificulta manutenção.  
**Fix:** Ou conectar o serviço às routes (chamá-lo na criação/atribuição de task) ou remover e mover a lógica para o futuro.  
**Recommendation:** Importar e chamar `notification_service.notify_task_assigned()` em `POST /tasks` quando `user_id` for fornecido.

---

### [MEDIUM] Validação de Email Duplicada em Dois Locais
**ID:** AP-12  
**File:** `routes/user_routes.py`, `utils/helpers.py`  
**Lines:** `user_routes.py:~40`; `helpers.py:validate_email()`  
**Description:** A regex de validação de email está implementada duas vezes: na função `validate_email()` em `helpers.py` E inline em `user_routes.py`. As routes não usam a função helper disponível.  
**Impact:** Regras de validação podem divergir; manutenção duplicada.  
**Fix:** PT-07  
**Recommendation:** Remover validação inline de `user_routes.py` e usar `from utils.helpers import validate_email` consistentemente.

---

### [MEDIUM] Token JWT Falso Retornado no Login
**ID:** AP-15  
**File:** `routes/user_routes.py`  
**Lines:** `POST /login` handler  
**Description:** O endpoint `/login` retorna um "token" que é apenas uma string gerada sem ser um JWT real assinado. Nenhuma outra rota valida esse token — o campo existe apenas para simular autenticação sem realmente implementá-la.  
**Impact:** Falsa sensação de segurança; todas as rotas estão efetivamente abertas.  
**Fix:** PT-09  
**Recommendation:** Implementar JWT real com `PyJWT`, assinar com `SECRET_KEY` do ambiente e validar em middleware.

---

### [MEDIUM] Unused Imports em utils/helpers.py
**ID:** AP-15  
**File:** `utils/helpers.py`  
**Lines:** 1–6  
**Description:** `helpers.py` importa `sys`, `json`, `hashlib`, `os` e `math` mas nenhum desses módulos é usado no código do arquivo. `process_task_data()` é definida mas nunca chamada pelas routes.  
**Impact:** Dependências desnecessárias; confusão sobre quais utilitários são realmente usados.  
**Fix:** Remover imports não utilizados; decidir se `process_task_data()` deve ser usada nas routes.  
**Recommendation:** Limpar imports e conectar `process_task_data()` ou remover a função.

---

### [LOW] log_action() usa print() em vez de Logger
**ID:** AP-13  
**File:** `utils/helpers.py`  
**Lines:** `log_action()` function  
**Description:** A função `log_action()` em `helpers.py` usa `print()` internamente. Mesma prática de anti-pattern que o projeto 1.  
**Impact:** Sem controle de nível de log; sem integração com sistemas de observabilidade.  
**Fix:** PT-10  
**Recommendation:** Usar `logging.getLogger(__name__)` dentro de `log_action()`.

---

### [LOW] Validações de Status/Priority Hardcoded nas Routes
**ID:** AP-14  
**File:** `routes/task_routes.py`, `routes/user_routes.py`  
**Lines:** Vários  
**Description:** As listas de valores válidos (`['pending', 'in_progress', 'done', 'cancelled']`, `['admin', 'manager', 'user']`) estão hardcoded inline nas routes, embora `VALID_STATUSES` e `VALID_ROLES` já estejam definidos em `utils/helpers.py`.  
**Impact:** Duplicação entre routes e helpers; inconsistência se um for atualizado sem o outro.  
**Fix:** PT-12  
**Recommendation:** Importar e usar `VALID_STATUSES`, `VALID_ROLES` de `utils/helpers.py` nas routes.

---

### [LOW] app.py com debug=True Hardcoded
**ID:** AP-02  
**File:** `app.py`  
**Lines:** `app.run(debug=True)` (última linha)  
**Description:** O modo debug do Flask está ativado diretamente no código. Em produção, isso expõa o debugger interativo e informações de stack trace para usuários.  
**Impact:** Exposição de stack traces e possível execução de código arbitrário via Werkzeug debugger em produção.  
**Fix:** PT-02  
**Recommendation:** Mover para `DEBUG = os.environ.get("DEBUG", "false").lower() == "true"`.

---

```
================================
Phase 2 complete.
Total findings: 12 (2C / 3H / 4M / 3L)

Proceed with Phase 3 — Refactoring? [y/n]
> y
================================
```
