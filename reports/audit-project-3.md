================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python (CPython 3.13) + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 6 | LOW: 2

MVC Adherence: 4/10 (Parcial)
  Models:       parcial — entidades e regra simples isoladas (models/*.py), mas quase toda a regra de negócio e acesso a dados vive nas rotas
  Views/Routes: parcial — blueprints existem, porém os handlers concentram validação, queries, regra e serialização
  Controllers:  ausente — não há camada de controller/service em uso; pastas controllers/ e services/ não têm código ativo (só __pycache__ órfão e um NotificationService morto)
  Separation:   violada — rota = view + controller + model; utils/helpers e schemas subutilizados; segredos no entrypoint

Findings

[CRITICAL] Hash de senha fraco (MD5 sem salt)
File: models/user.py:27-32
Description: set_password/check_password usam hashlib.md5 sem salt para armazenar e comparar senhas.
Impact: MD5 é quebrável por rainbow tables e brute force; um vazamento do banco expõe as senhas dos usuários quase imediatamente.
Recommendation: usar werkzeug.security (generate_password_hash/check_password_hash) ou bcrypt/argon2 com salt. (AP-04)

[CRITICAL] SECRET_KEY hardcoded no código
File: app.py:13
Description: app.config['SECRET_KEY'] = 'super-secret-key-123' fixo no fonte, versionado em git.
Impact: qualquer pessoa com acesso ao repositório conhece a chave usada para assinar sessões/tokens; comprometimento total de integridade de sessão.
Recommendation: carregar de os.environ via módulo config/settings.py, com .env fora do versionamento. (AP-02)

[CRITICAL] Credenciais de SMTP hardcoded
File: services/notification_service.py:7-10
Description: host, usuário e senha de e-mail ('taskmanager@gmail.com' / 'senha123') fixos na classe.
Impact: exposição direta de credenciais de e-mail em qualquer clone/commit.
Recommendation: mover para variáveis de ambiente / config; nunca versionar segredos. (AP-02)

[HIGH] Regra de negócio e acesso a dados dentro das rotas (sem controller/service)
File: routes/task_routes.py:11-299, routes/user_routes.py:10-211, routes/report_routes.py:12-223
Description: os handlers fazem tudo — validação de input, queries SQLAlchemy, regra de domínio (overdue, completion_rate, agregações de relatório) e montagem da resposta — inline. Handlers de 40-100+ linhas.
Impact: viola MVC e SRP; a regra não é reutilizável nem testável em isolamento; qualquer mudança de contrato mexe em rota, dados e regra ao mesmo tempo.
Recommendation: extrair regra/queries para models/services; introduzir controllers magros que orquestram; rotas apenas mapeiam e delegam. (AP-06)

[HIGH] Hash de senha exposto nas respostas da API
File: models/user.py:16-25
Description: User.to_dict() inclui o campo 'password' (o hash), e é retornado em create_user (user_routes.py:85-86) e em login (user_routes.py:209).
Impact: vaza material de credencial para qualquer cliente; facilita ataques offline caso o hash seja capturado.
Recommendation: remover 'password' da serialização; usar um schema de saída (marshmallow, já em requirements) que nunca exponha o hash. (relacionado a AP-04)

[HIGH] Autenticação de fachada e ausência de autorização
File: routes/user_routes.py:185-211, routes/task_routes.py:225-238, routes/report_routes.py:211-223
Description: /login retorna um token fixo 'fake-jwt-token-<id>' sem assinatura; nenhum endpoint valida token ou papel. DELETE de tasks, users e categories está aberto a qualquer requisição.
Impact: controle de acesso quebrado — qualquer um cria, altera ou apaga dados; o "token" não protege nada.
Recommendation: emitir JWT real assinado (SECRET_KEY via env) e aplicar middleware de auth/autorização por papel nas rotas sensíveis/destrutivas. (AP-13)

[MEDIUM] APIs deprecated: datetime.utcnow() e Model.query.get()
File: models/user.py:14; models/task.py:15-16,52; routes/task_routes.py:31,285; routes/report_routes.py:35,42,45; routes/user_routes.py:29 (e demais ocorrências)
Description: datetime.utcnow() está deprecated (Python 3.12+; usar datetime.now(timezone.utc)); Model.query.get() é API legada no SQLAlchemy 2.x (usar db.session.get(Model, id)).
Impact: quebra/avisos em upgrades futuros; datas naïve sem timezone geram bugs de comparação de overdue.
Recommendation: migrar para datetime.now(timezone.utc) e db.session.get(); centralizar a lógica de data em utils. (AP-11)

[MEDIUM] Debug ligado, side-effects no import e logging por print
File: app.py:30-34; routes/task_routes.py:149,153,219,234; routes/user_routes.py:83,89,147
Description: app.run(debug=True) expõe o debugger interativo; db.create_all() roda no import do módulo; logs feitos com print espalhado pelos handlers.
Impact: debug=True em produção é RCE via console Werkzeug; efeitos colaterais no import dificultam teste; prints não são logging estruturado.
Recommendation: controlar debug por ambiente (config), mover create_all/bootstrap para um ponto explícito, usar logging. (AP-16)

[MEDIUM] Lógica de "overdue" e serialização duplicadas
File: routes/task_routes.py:30-39,71-80,283-287; routes/user_routes.py:171-180; routes/report_routes.py:34-37,132-135; models/task.py:50-60
Description: o mesmo bloco aninhado que decide se a task está atrasada é reescrito em 6 lugares (havendo Task.is_overdue() no model); a montagem manual do dict de task repete Task.to_dict().
Impact: manutenção multiplicada e risco de divergência silenciosa entre cópias.
Recommendation: usar/estender Task.is_overdue() e Task.to_dict() (ou um serializer/schema) como fonte única. (AP-10)

[MEDIUM] Tratamento de erro engolido e casts sem validação
File: routes/task_routes.py:62-63,261,264; routes/task_routes.py:236-238; routes/user_routes.py:130-132; routes/report_routes.py:186-188,207-209,221-223
Description: vários `except:` nus retornam 500 genérico e escondem a causa real; em /tasks/search, int(priority) e int(user_id) não são protegidos e estouram 500 com input inválido.
Impact: erros mascarados dificultam diagnóstico; entradas malformadas derrubam o handler em vez de retornar 400.
Recommendation: validar entrada por schema (marshmallow já está disponível), capturar exceções específicas e centralizar o tratamento num middleware de erro. (AP-09)

[MEDIUM] Delete de categoria deixa tasks órfãs
File: routes/report_routes.py:211-223
Description: delete_category remove a categoria sem tratar as tasks que a referenciam; category_id fica apontando para um id inexistente.
Impact: integridade referencial quebrada — tasks com categoria fantasma; get_task passa a expor category_name inconsistente.
Recommendation: definir o comportamento (setar category_id=NULL ou bloquear delete com tasks vinculadas) via cascade/ON DELETE explícito ou regra no service. (AP-12)

[MEDIUM] Abstrações mortas e dependências não usadas
File: services/notification_service.py:1-48; utils/helpers.py:57-108; requirements.txt:4 (marshmallow)
Description: NotificationService nunca é instanciado/chamado; helpers.process_task_data reimplementa a validação das rotas mas não é usado; marshmallow está declarado e não é utilizado (validação é manual); a pasta schemas/ não tem código ativo.
Impact: código morto engana o leitor sobre o que está em uso e mascara a ausência real de camada de serviço/validação.
Recommendation: ou integrar essas abstrações no fluxo (schemas para validação, service para orquestração) ou removê-las. (AP-10 / dívida técnica)

[LOW] Strings/números mágicos espalhados com constantes ignoradas
File: routes/task_routes.py:110,113,177,182; routes/user_routes.py:71,120; utils/helpers.py:110-116
Description: listas de status válidos, faixas de prioridade (1..5) e papéis são repetidos literalmente nos handlers, enquanto VALID_STATUSES/VALID_ROLES/limites já existem em utils/helpers.py e não são importados.
Impact: intenção obscura e risco de divergência ao alterar um valor em só um lugar.
Recommendation: centralizar em config/constants e importar; remover as duplicações literais. (AP-14)

[LOW] Nomenclatura pobre e booleanos verbosos
File: models/user.py:34-38; models/task.py:38-48; routes/task_routes.py:16-59; routes/report_routes.py:55-68
Description: variáveis de uma letra (u, t, c, p, td, cat) e padrões `if cond: return True else: return False` em is_admin/validate_status/validate_priority.
Impact: legibilidade menor e mais chance de erro de leitura/manutenção.
Recommendation: nomes intencionais e retorno booleano direto (return self.role == 'admin'). (AP-15)

================================
Total: 14 findings
================================
