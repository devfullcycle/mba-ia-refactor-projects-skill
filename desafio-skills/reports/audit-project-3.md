# Relatório de auditoria — Projeto 3 (`task-manager-api`)

**Stack detectada:** Python + Flask 3.x + Flask-SQLAlchemy + SQLite (`tasks.db`)  
**Domínio:** Task Manager (usuários, tasks, categorias, relatórios)  
**Arquitetura (pré-refatoração):** parcialmente organizada (`models/`, `routes/`, `services/`), porém com lógica pesada em rotas e falhas de segurança em modelo de usuário.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   ~15 arquivos fonte analisados

## Summary
CRITICAL: 1 | HIGH: 2 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Credenciais SMTP hardcoded
File: services/notification_service.py:9-10 (pré-refatoração)
Description: Usuário e senha Gmail fictícios no código.
Impact: Vazamento de segredo; bloqueia boas práticas de deploy.
Recommendation: `SMTP_USER` / `SMTP_PASSWORD` via ambiente; no-op seguro se ausente.

### [HIGH] Exposição de hash/senha em `to_dict`
File: models/user.py:16-25 (pré-refatoração)
Description: Serialização incluía campo `password` (hash MD5 legado).
Impact: Vazamento de material para ataque offline via listagens de usuários.
Recommendation: Remover campo de payloads públicos; DTO dedicado.

### [HIGH] MD5 como armazenamento de senha
File: models/user.py:27-32 (pré-refatoração)
Description: `hashlib.md5` para derivar “hash” de senha.
Impact: Resistência criptográfica inadequada para credenciais.
Recommendation: `werkzeug.security.generate_password_hash` / `check_password_hash`.

### [MEDIUM] N+1 queries na listagem de tasks
File: routes/task_routes.py:11-57 (pré-refatoração)
Description: Para cada task, queries adicionais a `User` e `Category`.
Impact: Latência com crescimento de dados.
Recommendation: `joinedload` ou eager loading na consulta principal.

### [MEDIUM] Lógica de domínio e serialização nas rotas
File: routes/task_routes.py (pré-refatoração)
Description: Montagem de dicts, validação e regras de overdue diretamente em blueprint.
Impact: Dificulta testes e viola separação MVC.
Recommendation: `controllers/task_controller.py` com casos de uso; rotas apenas delegam.

### [MEDIUM] APIs deprecated — `datetime.utcnow()` (timezone naive)
File: models/task.py, routes diversos (pré-refatoração)
Description: Uso extensivo de `datetime.utcnow()` (comportamento naive).
Impact: Bugs de comparação quando migrar para timestamps conscientes de fuso.
Recommendation: `datetime.now(timezone.utc)` em evoluções futuras.

### [LOW] `except:` sem tipo
File: routes/task_routes.py:62-63, 236-237 (pré-refatoração)
Description: Captura qualquer exceção sem log estruturado.
Impact: Depuração difícil; pode mascarar `KeyboardInterrupt` em contextos interativos.
Recommendation: `except Exception as e:` + log + handler global.

### [LOW] Token JWT fictício em login
File: routes/user_routes.py:207-211 (pré-refatoração)
Description: Retorno `fake-jwt-token-` sem assinatura.
Impact: Falsa sensação de segurança para clientes.
Recommendation: JWT real ou remover campo até implementação.

================================
Total: 8 findings
================================
```

**Nota pós-refatoração:** `controllers/task_controller.py` centraliza tasks com `joinedload`; `models/user.py` usa Werkzeug; `notification_service` lê SMTP do ambiente; `config.py` + `python-dotenv` para `SECRET_KEY` e `DATABASE_URL`.
