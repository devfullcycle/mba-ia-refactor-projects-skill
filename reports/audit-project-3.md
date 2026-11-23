# Relatório de Auditoria Arquitetural — task-manager-api

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.x + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   15 analyzed | ~970 lines of code

## Summary
CRITICAL: 1 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Exposed Hardcoded Sensitive Credentials & Application Secret
File: app.py:11-13
Description: A chave de criptografia de sessão `SECRET_KEY` está fixada no código (`'super-secret-key-123'`), e no arquivo `services/notification_service.py:7-10` as credenciais de autenticação SMTP (`email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'`) encontram-se expostas em texto puro. Além disso, a URI de banco de dados SQLite (`'sqlite:///tasks.db'`) está hardcoded no arquivo principal. O pacote `python-dotenv` consta no `requirements.txt`, mas não é inicializado nem utilizado na aplicação.
Impact: Comprometimento crítico de segurança e infraestrutura. Qualquer acesso ao repositório expõe credenciais de envio de e-mail e permite forjar tokens de sessão e cookies criptografados. Violação direta de conformidade (LGPD/GDPR e OWASP).
Recommendation: Extrair todas as credenciais, segredos e URIs para variáveis de ambiente via arquivo `.env`, criando um módulo centralizador `config/settings.py` responsável pelo carregamento seguro e validação das variáveis.

### [HIGH] Direct Database Operations in Routes / Missing Controller Layer
File: routes/task_routes.py:11-298
Description: As funções das rotas em `task_routes.py`, `user_routes.py` (linhas 10-210) e `report_routes.py` (linhas 12-223) realizam consultas diretas ao banco de dados via ORM (`Task.query`, `User.query`, `Category.query`), manipulam transações (`db.session.add()`, `db.session.commit()`, `db.session.rollback()`) e executam lógicas de negócio e formatação de dados diretamente no manipulador HTTP. Não existe a camada de Controllers no projeto.
Impact: Forte acoplamento entre o protocolo de transporte HTTP e a persistência de dados. Inviabiliza testes unitários isolados das regras de negócio sem mockar o ciclo de vida HTTP do Flask e impede o reaproveitamento de regras em outros fluxos (CLI, tarefas assíncronas, jobs agendados).
Recommendation: Implementar a camada `controllers/` (`task_controller.py`, `user_controller.py`, `category_controller.py`, `report_controller.py`), mantendo as rotas restritas à recepção de requisições HTTP, validação de schema e repasse para os controladores/modelos.

### [HIGH] Broken Cryptography & Password Exposure in DTO
File: models/user.py:17-32
Description: O método `set_password` utiliza o algoritmo obsoleto e vulnerável `hashlib.md5()` sem salt para armazenar as senhas dos usuários. Adicionalmente, o método `to_dict()` da classe `User` (linhas 17-25) inclui o campo `'password'` (o hash MD5) diretamente no dicionário retornado, o qual é exposto para os clientes nos endpoints de detalhe e criação de usuário (`user_routes.py:33-40, 85-86`) e no login (`user_routes.py:209`).
Impact: Vulnerabilidade severa à quebra de senhas por tabelas rainbow e ataques de dicionário. Exposição desnecessária de dados confidenciais do usuário em respostas da API REST, facilitando ataques de personificação e vazamento de identidade.
Recommendation: Migrar o hashing de senhas para `werkzeug.security.generate_password_hash` e `check_password_hash` (utilizando PBKDF2/scrypt com salt). Remover o campo `'password'` do método de serialização `to_dict()` e nunca retornar credenciais em payloads de saída.

### [HIGH] Unsafe Deletion & Manual Cascade without Database Constraint
File: routes/user_routes.py:140-146
Description: A exclusão de usuários na rota `delete_user` realiza a limpeza de tarefas associadas através de uma iteração manual (`tasks = Task.query.filter_by(user_id=user_id).all(); for t in tasks: db.session.delete(t)`), sem que a foreign key ou o relacionamento ORM em `models/task.py:13-20` declarem comportamento de deleção em cascata (`cascade="all, delete-orphan"` ou `ON DELETE CASCADE` no banco de dados).
Impact: Risco iminente de corrupção relacional e geração de registros órfãos na tabela `tasks` caso exclusões ocorram via outros pontos do sistema ou caso a execução falhe no meio da iteração.
Recommendation: Configurar cascade formal no relacionamento SQLAlchemy (`relationship('Task', cascade='all, delete-orphan')`) e aplicar integridade referencial nativa no banco de dados, delegando a regra de integridade para a camada de persistência.

### [MEDIUM] N+1 Query Problem in Entity Listings & Aggregations
File: routes/task_routes.py:41-58
Description: No endpoint `GET /tasks` (`task_routes.py:14-59`), a API busca todas as tarefas (`Task.query.all()`) e, dentro de um loop de iteração sobre os resultados, executa duas queries síncronas adicionais para cada tarefa: `User.query.get(t.user_id)` e `Category.query.get(t.category_id)`. O mesmo anti-pattern ocorre em `report_routes.py:53-68` (onde são disparadas queries de busca de tarefas para cada usuário) e em `report_routes.py:159-165` (onde `Task.query.filter_by(category_id=c.id).count()` é executado dentro do loop de categorias).
Impact: Explosão geométrica na quantidade de requisições enviadas ao banco de dados ($1 + 2N$ queries no caso de tarefas). Degradação severa de latência de rede e consumo excessivo de I/O de banco de dados conforme o volume de registros aumenta.
Recommendation: Utilizar `joinedload` ou queries com `JOIN` e agregações agrupadas (`GROUP BY`) via SQLAlchemy para recuperar os dados relacionados em uma única consulta otimizada.

### [MEDIUM] Swallowed Exceptions & Silent Bare Except Blocks
File: routes/task_routes.py:62-63
Description: Múltiplos trechos do sistema utilizam blocos genéricos `except:` sem tipagem e sem registrar logs com traceback, retornando apenas mensagens de erro genéricas como `{'error': 'Erro interno'}` ou `{'error': 'Erro ao deletar'}`. O padrão repete-se em `task_routes.py:236-238`, `user_routes.py:130-132, 149-151`, `report_routes.py:186-188, 207-209, 221-223` e `utils/helpers.py:46-50`.
Impact: Supressão silenciosa de falhas de sistema, impedindo observabilidade, diagnóstico de falhas e auditoria pós-incidente em ambientes de produção.
Recommendation: Capturar classes de exceção específicas, registrar o traceback completo via módulo `logging` e unificar o tratamento de erros em um middleware/error handler global (`@app.errorhandler`).

### [MEDIUM] High Cyclomatic Complexity & Deeply Nested Conditionals
File: models/task.py:50-60
Description: O método `is_overdue` na classe `Task` implementa múltiplos níveis de condicionais aninhadas (`if self.due_date: if self.due_date < datetime.utcnow(): if self.status != 'done'...`). Lógica semelhante de verificação de atraso é duplicada de forma dispersa em `task_routes.py:30-39`, `task_routes.py:71-80` e `report_routes.py:33-43, 119-136`.
Impact: Código difícil de ler e manter, com caminhos de execução redundantes, duplicação de regras de negócio entre modelos e controladores e maior propensão a erros sutis.
Recommendation: Refatorar o método utilizando Guard Clauses e expressões booleanas diretas (`return bool(self.due_date and self.due_date < now and self.status not in ('done', 'cancelled'))`), centralizando essa lógica no Model e eliminando duplicações nas rotas.

### [MEDIUM] Destructive Cascade Deletion on Optional Categories & Missing Prior Disassociation
File: routes/report_routes.py:212-225 / models/category.py:13
Description: No endpoint de remoção de categorias (`DELETE /categories/<id>`), a exclusão do registro de categoria apagava em cascata todas as tarefas associadas (via `cascade='all, delete-orphan'`), em vez de validar dependências e desvincular as tarefas dependentes. Como a associação entre tarefa e categoria é puramente opcional (`category_id` anulável), a exclusão de uma categoria secundária não deve destruir o histórico e o ciclo de vida das tarefas pertencentes aos usuários.
Impact: Perda acidental de dados de tarefas dos usuários por efeito colateral imprevisto na remoção de uma categoria organizatória.
Recommendation: Remover `cascade='all, delete-orphan'` do modelo `Category`, implementar a desvinculação prévia explícita no controller (`task.category_id = None`) e declarar `ondelete='SET NULL'` na foreign key de `Task`.

### [LOW] Deprecated APIs (datetime.utcnow)
File: models/user.py:14
Description: O método `datetime.utcnow()` é utilizado como default nos modelos (`user.py:14`, `category.py:11`, `task.py:15-16`) e em cálculos de tempo em `task_routes.py:31, 72, 215, 285`, `report_routes.py:35, 43, 45, 71, 133`, `services/notification_service.py:35` e `utils/helpers.py:38`. Desde o Python 3.12, `datetime.utcnow()` foi formalmente marcado como obsoleto (deprecated).
Impact: Emissão contínua de `DeprecationWarning` nos logs da aplicação e inconsistências no manuseio de fuso horário por gerar objetos de data ingênuos (sem timezone explícito).
Recommendation: Substituir todas as chamadas a `datetime.utcnow()` por `lambda: datetime.now(timezone.utc)` nos modelos e `datetime.now(timezone.utc)` nas rotas e utilitários.

### [LOW] Missing Explicit HTTP Methods on Root Endpoints
File: app.py:22-28
Description: Os endpoints `@app.route('/health')` e `@app.route('/')` em `app.py` não especificam o parâmetro de métodos aceitos (`methods=['GET']`), dependendo do comportamento padrão implícito do Flask.
Impact: Falta de clareza nos contratos da API, permitindo que verbos não intencionais sejam processados ou rejeitados sem semântica explícita.
Recommendation: Declarar explicitamente `methods=['GET']` em todas as rotas da aplicação.

### [LOW] Dead Code & Unused Imports
File: app.py:7
Description: Imports não utilizados estão presentes em diversos arquivos: `import os, sys, json` em `app.py:7`, `import json` em `models/task.py:3`, `import json, os, sys, time` em `routes/task_routes.py:7`, `import json` em `routes/user_routes.py:6` e `routes/report_routes.py:8`, além de `import os, json, sys, math, hashlib` em `utils/helpers.py:3-8`.
Impact: Poluição do escopo global, aumento desnecessário do tempo de carga de módulos e distração durante a leitura e revisão do código.
Recommendation: Remover todos os imports não referenciados e higienizar os módulos.

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
