# Desafio 03 — Skill `/refactor-arch`

Skill para Claude Code que automatiza análise, auditoria e refatoração arquitetural de projetos legados para o padrão MVC. Agnóstica de tecnologia — funciona com Python/Flask e Node.js/Express.

---

## A) Análise Manual

### Projeto 1 — code-smells-project (Python/Flask E-commerce)

| Severidade | Arquivo | Linha(s) | Problema |
|---|---|---|---|
| CRITICAL | `models.py` | 17, 30, 37, 45, 70, 84, 106, 116, 145, 172, 206, 232, 275–285 | SQL Injection — todas as queries usam concatenação de string |
| CRITICAL | `app.py` | 8 | Hardcoded Secret Key — `"minha-chave-super-secreta-123"` no código |
| CRITICAL | `app.py` | 48–57, 60–79 | Endpoints `/admin/reset-db` e `/admin/query` sem nenhuma autenticação |
| CRITICAL | `database.py` | 46–53 | Senhas em texto plano nos seeds e na query de login |
| HIGH | `controllers.py` | 114–120 | Secret key e `debug: True` expostos no response do `/health` |
| HIGH | `database.py` | 4–5 | Conexão de banco global mutável — não é thread-safe |
| HIGH | `controllers.py` | 83–90 | Side effects de notificação (`print ENVIANDO EMAIL/SMS`) dentro do controller |
| MEDIUM | `models.py` | 175–245 | N+1 queries em `get_pedidos_usuario` e `get_todos_pedidos` (cursor aninhado em loop) |
| MEDIUM | `models.py` | 175–245 | Duplicação de código — as duas funções de listagem de pedidos são ~95% idênticas |
| LOW | Todos | Vários | `print()` usado como logging operacional em vez de `logging` |
| LOW | `controllers.py` | 53–65, 77–95 | Validação inconsistente — `criar_produto` valida categoria, `atualizar_produto` não |
| LOW | `models.py` | 257–263 | Magic numbers na lógica de desconto (`10000`, `5000`, `0.1` sem constantes) |

**Justificativas dos problemas mais críticos:**
- **SQL Injection** é o problema de maior impacto: permite comprometimento total do banco e bypass de autenticação com `email = "' OR '1'='1"`. Afeta 13+ locais no código.
- **Endpoints admin sem auth** permitem que qualquer cliente HTTP execute SQL arbitrário ou apague todo o banco — sem nenhuma credencial.
- **Senhas em texto plano** garantem que uma única violação do banco exponha imediatamente 100% das credenciais dos usuários.

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express LMS)

| Severidade | Arquivo | Linha(s) | Problema |
|---|---|---|---|
| CRITICAL | `src/utils.js` | 2–7 | Credenciais hardcoded — `dbPass`, `paymentGatewayKey`, `smtpUser` em texto plano |
| CRITICAL | `src/AppManager.js` | 1–120 | God Class — DB, rotas, pagamento, auditoria e cache misturados em uma classe |
| CRITICAL | `src/utils.js`, `AppManager.js` | `utils.js:15–21`, `AppManager.js:55` | `badCrypto()` — hash customizado trivialmente reversível usado para senhas |
| CRITICAL | `src/AppManager.js` | 68–100 | Endpoint `/api/admin/financial-report` público sem autenticação |
| HIGH | `src/AppManager.js` | 68–100 | N+1 queries com callback hell de 4 níveis no relatório financeiro |
| HIGH | `src/AppManager.js` | 20–65 | Lógica de pagamento embutida na rota — 50 linhas com callbacks aninhados |
| HIGH | `src/utils.js` | 9–10 | Cache global mutável sem TTL ou limite de tamanho |
| HIGH | `src/AppManager.js` | 101–105 | DELETE de usuário sem cascade — orphaned records documentados no próprio código |
| MEDIUM | `src/AppManager.js` | 42 | Magic string para aprovação de pagamento — `cc.startsWith("4")` hardcoded |
| MEDIUM | `src/AppManager.js` | Vários | Sem error handling centralizado — strings genéricas em vez de JSON |
| LOW | `src/AppManager.js`, `utils.js` | 42, 13 | `console.log` com número de cartão — dados sensíveis nos logs |
| LOW | `src/AppManager.js` | 13–17 | Parâmetros crípticos na API — `usr`, `eml`, `c_id` sem documentação |

**Justificativas dos problemas mais críticos:**
- **God Class** é o problema arquitetural central: torna impossível testar qualquer componente de forma isolada e cria acoplamento total entre DB, rotas e regras de negócio.
- **`badCrypto()`** é especialmente grave porque parece ser "criptografia" mas é trivialmente reversível — dá falsa sensação de segurança.
- **N+1 com callbacks aninhados** em 4 níveis é impossível de manter e escala O(n×m) com o crescimento de dados.

---

### Projeto 3 — task-manager-api (Python/Flask + SQLAlchemy)

| Severidade | Arquivo | Linha(s) | Problema |
|---|---|---|---|
| CRITICAL | `models/user.py` | 27–32 | MD5 para senhas — sem salt, reversível por rainbow table |
| CRITICAL | `services/notification_service.py` | 8–11 | Credenciais SMTP hardcoded — `email_user` e `email_password` no código |
| HIGH | `models/user.py` | 16–25 | `to_dict()` inclui o campo `password` no response de todos os endpoints |
| HIGH | `routes/task_routes.py`, `report_routes.py` | Múltiplos | Lógica de overdue duplicada 4+ vezes nas routes (modelo já tem `is_overdue()` ignorado) |
| HIGH | `routes/report_routes.py` | 53–68 | N+1 — `Task.query.filter_by(user_id=...)` dentro de loop Python por usuário |
| MEDIUM | `services/notification_service.py` | Completo | Serviço de notificação definido mas nunca chamado pelas routes — dead code |
| MEDIUM | `routes/user_routes.py`, `utils/helpers.py` | Vários | Validação de email duplicada — regex inline ignora o `validate_email()` em helpers |
| MEDIUM | `routes/user_routes.py` | Login handler | Token JWT falso — string não assinada retornada sem validação em nenhuma rota |
| MEDIUM | `utils/helpers.py` | 1–8 | Imports não utilizados — `sys`, `json`, `hashlib`, `os`, `math` |
| LOW | `utils/helpers.py` | `log_action()` | `print()` em `log_action()` em vez de logger estruturado |
| LOW | `routes/task_routes.py`, `user_routes.py` | Vários | Listas hardcoded em vez de `VALID_STATUSES` e `VALID_ROLES` já definidos em `helpers.py` |
| LOW | `app.py` | Última linha | `debug=True` hardcoded em vez de variável de ambiente |

**Justificativas dos problemas mais críticos:**
- **MD5 para senhas** é especialmente grave por parecer seguro mas não ser: sem salt e com rainbow tables públicas disponíveis, qualquer hash MD5 de senha comum é quebrado em segundos.
- **Password exposto no `to_dict()`** significa que literalmente todo endpoint que retorna usuários vaza o hash — incluindo o hash quebrado de MD5.
- **N+1 no relatório** carrega todos os objetos Task em memória Python para contar por usuário — com 10.000 tasks seria catastrófico.

---

## B) Construção da Skill

### Estrutura do SKILL.md

O `SKILL.md` foi estruturado como um **prompt de agente especialista** com 3 fases sequenciais, cada uma com responsabilidades estritamente separadas:

- **Fase 1 — somente leitura:** detecta stack, mapeia arquitetura, imprime resumo padronizado. Não toca em nenhum arquivo.
- **Fase 2 — somente leitura + relatório:** cruza o código contra o `antipatterns-catalog.md`, produz relatório formatado pelo `audit-report-template.md`, e **pausa obrigatoriamente** antes de qualquer modificação.
- **Fase 3 — escrita:** aplica transformações do `refactoring-playbook.md` seguindo a estrutura do `mvc-guidelines.md`, valida com boot da aplicação.

A regra central do SKILL.md é: **fases 1 e 2 são read-only**. O agente só pode modificar arquivos após confirmação explícita do usuário na transição para a Fase 3.

### Arquivos de referência e decisões de design

| Arquivo | Decisão de design | Por quê |
|---|---|---|
| `analysis-guide.md` | Heurísticas baseadas em extensões de arquivo e dependências declaradas | Nomes de arquivo variam entre projetos; extensões e `package.json`/`requirements.txt` são confiáveis |
| `antipatterns-catalog.md` | 15 anti-patterns com sinais de detecção concretos (ex: `cursor.execute("..." + str(id))`) | "Código ruim" não é acionável; a regex/padrão exato é o que o agente precisa procurar |
| `audit-report-template.md` | Template com exemplo preenchido completo do Projeto 1 | O agente precisa ver o nível de detalhe esperado, não apenas o esqueleto do template |
| `mvc-guidelines.md` | Duas árvores de diretório separadas: Flask e Express, com regras de responsabilidade por camada | A estrutura MVC difere entre as stacks; definir as duas evita ambiguidade |
| `refactoring-playbook.md` | 12 padrões com código antes/depois em ambas as stacks quando aplicável | Exemplos concretos evitam que o agente invente soluções; playbook é a "memória de transformações" |

### Como a skill é agnóstica de tecnologia

A skill funciona em qualquer stack porque:
1. `analysis-guide.md` tem seções separadas por linguagem para detecção de framework e banco.
2. `antipatterns-catalog.md` tem sinais de detecção tanto em Python quanto em JavaScript onde o padrão difere.
3. `mvc-guidelines.md` define a estrutura MVC alvo para **Flask** e **Express** separadamente.
4. `refactoring-playbook.md` inclui exemplos de código nas duas linguagens.
5. O SKILL.md instrui o agente a detectar a tecnologia primeiro (Fase 1) e usar os guias correspondentes nas fases seguintes.

### Desafios encontrados

**Conflito de namespace Python (Projeto 1):** criar o pacote `database/` conflitou com o arquivo `database.py` legado — Python não pode ter um módulo e um pacote com o mesmo nome. Solução: renomear os arquivos legados para `*_legacy.py` antes de criar os novos pacotes.

**N+1 com callbacks em Node.js (Projeto 2):** o driver `sqlite3` assíncrono torna a correção de N+1 verbosa com callbacks aninhados. Solução: migrar para `better-sqlite3` (síncrono), que permite JOINs diretos com código limpo e legível.

**Mudança de algoritmo de senha (Projeto 3):** trocar MD5 por werkzeug invalida todos os hashes existentes no banco. Solução: o `seed.py` já usa `u.set_password()` — ao re-rodar o seed após a mudança, todos os hashes são recriados automaticamente com o novo algoritmo.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 5 | 3 | 2 | 3 | **13** |
| ecommerce-api-legacy | Node.js + Express 4.18 | 4 | 4 | 2 | 2 | **12** |
| task-manager-api | Python + Flask 3.0 + SQLAlchemy | 2 | 3 | 4 | 3 | **12** |

### Comparação de estrutura antes/depois

#### Projeto 1 — code-smells-project

```
ANTES (4 arquivos planos)          DEPOIS (MVC completo)
──────────────────────────         ──────────────────────────────────
app.py                             config/
controllers.py                       settings.py
models.py                            logging_config.py
database.py                        database/
                                     connection.py
                                   models/
                                     produto_model.py
                                     usuario_model.py
                                     pedido_model.py
                                     relatorio_model.py
                                   controllers/
                                     produto_controller.py
                                     usuario_controller.py
                                     pedido_controller.py
                                   routes/
                                     api_routes.py
                                   middlewares/
                                     auth.py
                                     error_handler.py
                                   services/
                                     notification_service.py
                                   app.py  ← composition root
```

#### Projeto 2 — ecommerce-api-legacy

```
ANTES (God Class)                  DEPOIS (MVC Express)
──────────────────────             ──────────────────────────────────
src/app.js                         src/config/settings.js
src/AppManager.js  ← 120 linhas    src/database/connection.js
src/utils.js                       src/models/
                                     userModel.js
                                     courseModel.js
                                     enrollmentModel.js
                                   src/controllers/
                                     checkoutController.js
                                     reportController.js
                                     userController.js
                                   src/routes/
                                     checkoutRoutes.js
                                     reportRoutes.js
                                     userRoutes.js
                                   src/middlewares/
                                     auth.js
                                     errorHandler.js
                                   src/services/
                                     paymentService.js
                                   src/app.js  ← composition root
```

#### Projeto 3 — task-manager-api

Estrutura de diretórios preservada (já tinha `models/`, `routes/`, `services/`, `utils/`). Correções aplicadas nos arquivos existentes:

| Arquivo | O que mudou |
|---|---|
| `models/user.py` | MD5 → `werkzeug.security`, campo `password` removido de `to_dict()` |
| `services/notification_service.py` | Credenciais SMTP → `os.environ`, `print()` → `logging` |
| `utils/helpers.py` | Imports desnecessários removidos, `log_action()` usa `logging` |
| `routes/report_routes.py` | N+1 → `func.count()` + `group_by()` do SQLAlchemy |
| `app.py` | `SECRET_KEY` e `DEBUG` → `os.environ`, versão atualizada para `2.0.0` |

### Output de validação

**Projeto 1:**
```
GET  /                      200  versao: 2.0.0
GET  /health                200  status: ok  | secret_key exposta: False
GET  /produtos              200  10 produtos
GET  /produtos/busca?q=...  200  1 resultado (query parametrizada)
POST /login                 200  Admin (hash werkzeug)
POST /login (senha errada)  401
POST /pedidos               201  pedido_id: 1
GET  /relatorios/vendas     200  faturamento calculado
```

**Projeto 2:**
```
POST /api/checkout (cartão Visa)   200  { "msg": "Sucesso" }
POST /api/checkout (cartão Master) 400  { "error": "Pagamento recusado" }
GET  /api/admin/financial-report   401  (sem token)
```

**Projeto 3:**
```
GET  /                 200  version: 2.0.0
GET  /health           200  status: ok
GET  /tasks            200  10 tasks
GET  /users            200  campo password exposto: False
POST /login            200  João Silva (hash werkzeug)
GET  /reports/summary  200  total_tasks: 10
```

### Checklist de validação

#### Projeto 1 — code-smells-project

| Item | Status |
|---|---|
| Linguagem detectada corretamente (Python) | ✅ |
| Framework detectado corretamente (Flask 3.1.1) | ✅ |
| Domínio descrito corretamente (E-commerce API) | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ |
| ≥5 findings com arquivo e linha exatos | ✅ 13 findings |
| Skill pausa para confirmação antes da Fase 3 | ✅ |
| Estrutura de diretórios MVC criada | ✅ |
| Configuração extraída para `config/` (sem hardcoded) | ✅ |
| Senhas com hash (werkzeug) | ✅ |
| SQL Injection corrigido (queries parametrizadas) | ✅ |
| Endpoints admin protegidos | ✅ |
| Error handling centralizado | ✅ |
| Aplicação inicia sem erros | ✅ |
| Todos os endpoints respondem corretamente | ✅ |

#### Projeto 2 — ecommerce-api-legacy

| Item | Status |
|---|---|
| Linguagem detectada corretamente (JavaScript/Node.js) | ✅ |
| Framework detectado corretamente (Express 4.18) | ✅ |
| Domínio descrito corretamente (LMS com checkout) | ✅ |
| ≥5 findings com arquivo e linha exatos | ✅ 12 findings |
| Skill pausa para confirmação | ✅ |
| God Class desmembrada em MVC | ✅ |
| `badCrypto` substituído por bcrypt | ✅ |
| Credenciais movidas para `.env` | ✅ |
| N+1 corrigido com JOIN único | ✅ |
| Endpoint admin protegido por `requireAdmin` | ✅ |
| Aplicação inicia sem erros | ✅ |
| Checkout e relatório financeiro funcionando | ✅ |

#### Projeto 3 — task-manager-api

| Item | Status |
|---|---|
| Linguagem detectada corretamente (Python) | ✅ |
| Framework detectado corretamente (Flask 3.0 + SQLAlchemy) | ✅ |
| Domínio descrito corretamente (Task Manager) | ✅ |
| ≥5 findings mesmo em projeto parcialmente organizado | ✅ 12 findings |
| Skill pausa para confirmação | ✅ |
| MD5 → werkzeug | ✅ |
| Password removido do `to_dict()` | ✅ |
| Credenciais SMTP → env vars | ✅ |
| N+1 → `func.count()` + `group_by()` | ✅ |
| Aplicação inicia sem erros | ✅ |
| Todos os endpoints respondem corretamente | ✅ |

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado com API key da Anthropic configurada
- Python 3.10+ com `pip`
- Node.js 18+ com `npm`

### Executar a skill nos projetos

```bash
# Projeto 1 — Python/Flask E-commerce
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"

# Projeto 2 — Node.js/Express LMS
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# Projeto 3 — Python/Flask Task Manager
cd ../task-manager-api
pip install -r requirements.txt
python seed.py
claude "/refactor-arch"
```

### Validar que a refatoração funcionou

Cada projeto tem um script de testes que valida todos os endpoints automaticamente:

```bash
# Projeto 1
cd code-smells-project
python test_app.py

# Projeto 2
cd ../ecommerce-api-legacy
node test_app.js

# Projeto 3
cd ../task-manager-api
python test_app.py
```

### Iniciar os servidores manualmente

```bash
# Projeto 1 (Python/Flask) — http://localhost:5000
cd code-smells-project
python app.py

# Projeto 2 (Node.js/Express) — http://localhost:3000
cd ecommerce-api-legacy
npm start

# Projeto 3 (Python/Flask) — http://localhost:5000
cd task-manager-api
python seed.py  # rodar antes do primeiro boot
python app.py
```

### Relatórios de auditoria

Os relatórios completos da Fase 2 estão em:

```
reports/
├── audit-project-1.md   ← code-smells-project  (13 findings: 5C / 3H / 2M / 3L)
├── audit-project-2.md   ← ecommerce-api-legacy (12 findings: 4C / 4H / 2M / 2L)
└── audit-project-3.md   ← task-manager-api     (12 findings: 2C / 3H / 4M / 3L)
```
