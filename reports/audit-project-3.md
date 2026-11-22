================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite via Flask-SQLAlchemy 3.1.1)
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] AP-02 Hardcoded Credentials
File: app.py:13, services/notification_service.py:9-10
Description: `SECRET_KEY` definida como 'supe****' direto no código; usuário e senha SMTP ('senh****') embutidos no construtor do NotificationService.
Impact: Quem acessa o repositório consegue forjar sessões e usar a conta de e-mail.
Recommendation: Ler segredos de variáveis de ambiente (com .env.example sem valores reais) e falhar na inicialização se ausentes (playbook: PB-02).

### [CRITICAL] AP-04 Autenticação e segurança de dados quebradas (hash fraco e exposição de senha)
File: models/user.py:29, models/user.py:32, models/user.py:21, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209
Description: Senha armazenada e comparada com MD5 sem sal. `User.to_dict()` inclui o campo `password` (hash), e esse dict é devolvido em criação, atualização, GET /users/<id> e login.
Impact: Hashes MD5 são quebráveis em massa e são vazados em respostas da API.
Recommendation: Usar hash adequado da stack (werkzeug.security), com migração dos hashes MD5 existentes no login, e remover `password` das respostas (playbook: PB-04).

### [CRITICAL] AP-04 Autenticação e segurança de dados quebradas (sem autenticação/autorização e token falso)
File: routes/user_routes.py:207-211, routes/user_routes.py:42-90, routes/user_routes.py:134-151, routes/task_routes.py:225-238, routes/report_routes.py:211-223
Description: O login devolve o token fixo `'fake-jwt-token-' + id`, que não é validado em nenhuma rota. Nenhum endpoint exige autenticação. Qualquer cliente pode apagar usuários, tasks e categorias, e criar usuário com `role='admin'` (linhas 52, 71-78).
Impact: Qualquer pessoa pode se passar por qualquer usuário, escalar privilégios e destruir dados.
Recommendation: Emitir token assinado e proteger rotas mutáveis e administrativas com decorator de autenticação/autorização; impedir autoatribuição de role (playbook: PB-04).

### [HIGH] AP-05 Lógica de negócio em Controllers/Rotas
File: routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/user_routes.py:153-183, routes/report_routes.py:12-101, routes/report_routes.py:103-155
Description: Handlers calculam atraso (overdue), estatísticas, taxa de conclusão, validam regras de domínio e montam respostas. `summary_report` tem ~90 linhas com laços e condicionais aninhados.
Impact: Regras não são testáveis sem HTTP e ficam duplicadas entre rotas.
Recommendation: Mover regras para uma camada de controllers/services e deixar as rotas só com entrada → controller → resposta (playbook: PB-05).

### [HIGH] AP-07 Violação de camadas
File: routes/task_routes.py:14, routes/user_routes.py:12, routes/report_routes.py:15-68, routes/report_routes.py:157-223
Description: Rotas consultam e persistem direto via `Model.query` e `db.session`. O CRUD de categorias está dentro de `report_routes.py`. `services/notification_service.py` e `utils/helpers.py` existem mas não são usados pelas rotas.
Impact: Acesso a dados espalhado, camada de serviços ociosa e domínio de categorias no módulo errado.
Recommendation: Criar controllers por domínio, mover o acesso a dados para os models e as rotas de categoria para um blueprint próprio (playbook: PB-01, PB-05).

### [HIGH] AP-08 Configuração insegura de produção / exposição de internals
File: app.py:34, app.py:11, app.py:15
Description: `app.run(debug=True, host='0.0.0.0')` expõe o debugger do Werkzeug em todas as interfaces. A URI do banco é fixa no código e o CORS está totalmente aberto.
Impact: O debugger permite execução remota de código e vaza stack traces (inclusive para os `int()` sem tratamento nas linhas 261 e 264 de task_routes.py).
Recommendation: Controlar debug/host/porta/CORS por configuração externa, com defaults seguros (playbook: PB-02, PB-07).

### [MEDIUM] AP-09 Consultas N+1
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:55-56, routes/report_routes.py:163
Description: Para cada task, `User.query.get` e `Category.query.get`. Para cada usuário, `len(u.tasks)` (lazy load) e `Task.query.filter_by(user_id=...)`. Para cada categoria, um `count()`.
Impact: 1+N (até 1+2N) consultas por requisição.
Recommendation: Usar joinedload ou consultas agregadas com GROUP BY (playbook: PB-08).

### [MEDIUM] AP-10 Validação de entrada ausente ou inconsistente
File: routes/task_routes.py:113, routes/task_routes.py:167-169, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/report_routes.py:196-197, routes/user_routes.py:103, routes/user_routes.py:125
Description: Comparação de `priority` sem checar o tipo, `len()` sobre `title` sem checar o tipo, `int()` de query string sem tratamento, `request.get_json()` sem checagem de `None` em `update_category`, `name`/`active` de usuário sem validação e cor de categoria sem validação.
Impact: Entradas malformadas geram 500 em vez de 400 e dados inválidos entram no banco.
Recommendation: Centralizar a validação e devolver 400 consistente (playbook: PB-09).

### [MEDIUM] AP-11 Tratamento de erros ausente, ruidoso ou espalhado
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:204, routes/task_routes.py:236, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221 (+1 ocorrência)
Description: `except:` genérico engole erros sem log. Respostas de erro montadas à mão em cada rota. Não há tratador global. Erros são registrados com `print`.
Impact: Falhas ficam invisíveis, o formato de erro é inconsistente e qualquer exceção não prevista vira 500 bruto.
Recommendation: Criar exceção de domínio e `errorhandler` global, com logging (playbook: PB-07).

### [MEDIUM] AP-12 Código duplicado
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-43, routes/report_routes.py:132-135
Description: A regra de atraso (overdue) é reescrita 6 vezes, apesar de `Task.is_overdue()` existir. A serialização de task, a regex de e-mail e a lista de status válidos são repetidas em vários arquivos.
Impact: Uma mudança de regra exige editar vários pontos, com risco de divergência.
Recommendation: Reaproveitar `Task.is_overdue()`/`to_dict()` e centralizar validações e constantes (playbook: PB-10).

### [MEDIUM] AP-13 APIs deprecated: `Model.query.get()` (SQLAlchemy legacy)
File: routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122 (+13 ocorrências)
Description: `Query.get()` é API legada no SQLAlchemy 2.x; substituto: `db.session.get(Model, id)`. Fonte: documentação do SQLAlchemy 2.0.
Impact: Emite LegacyAPIWarning e pode quebrar em atualizações futuras.
Recommendation: Trocar por `db.session.get()` (playbook: PB-11).

### [MEDIUM] AP-13 APIs deprecated: `datetime.utcnow()`
File: models/task.py:15-16, models/task.py:52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, routes/task_routes.py:215 (+15 ocorrências)
Description: `datetime.utcnow()` é deprecated a partir do Python 3.12; substituto: `datetime.now(timezone.utc)` (com `.replace(tzinfo=None)` para manter valores naive). Fonte: documentação do Python 3.12. Versão de produção a verificar.
Impact: DeprecationWarning em Python ≥3.12; troca direta pode quebrar comparações naive/aware.
Recommendation: Centralizar um helper `utc_now()` (playbook: PB-11).

### [LOW] AP-14 Magic numbers e strings soltas
File: routes/task_routes.py:96, routes/task_routes.py:99, routes/task_routes.py:110, routes/task_routes.py:113, routes/user_routes.py:64, routes/user_routes.py:71 (+8 ocorrências)
Description: Limites de título, prioridade, tamanho mínimo de senha, listas de status/roles e a janela de 7 dias estão soltos no código; as constantes de utils/helpers.py:110-116 não são usadas.
Impact: Valores duplicados e difíceis de alterar.
Recommendation: Centralizar em um módulo de constantes (playbook: PB-12).

### [LOW] AP-15 Nomenclatura ruim
File: routes/report_routes.py:24-28, models/task.py:45, utils/helpers.py:57, utils/helpers.py:84, routes/task_routes.py:17
Description: Nomes opacos (`p1..p5`, `p`, `t`, `u`, `cat`, `pwd`) e `process_task_data` genérico.
Impact: Leitura e manutenção mais difíceis.
Recommendation: Renomear para nomes descritivos (playbook: PB-12).

### [LOW] AP-16 Código morto, imports não usados e logging inadequado
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, utils/helpers.py:2-7, utils/helpers.py:9-108, services/notification_service.py:4-48 (+12 ocorrências)
Description: Imports não usados, helpers e `NotificationService` nunca chamados, `Task.validate_status`/`validate_priority` não usados, dependências `marshmallow`, `requests` e `python-dotenv` declaradas sem uso e `print` no lugar de logger.
Impact: Ruído, superfície de manutenção desnecessária e logs sem nível.
Recommendation: Remover o código morto e usar o módulo `logging` (playbook: PB-12).

================================
Total: 15 findings
================================
