# Skill de Auditoria e Refatoração Arquitetural

Skill do Claude Code que audita e refatora uma codebase para o padrão MVC de forma agnóstica
de tecnologia, em três fases: **análise da stack → relatório de auditoria (com aprovação
humana obrigatória) → refatoração validada**.

Entregue e executada nos três projetos legados do desafio: dois em Python/Flask (um monolítico,
um parcialmente organizado) e um em Node.js/Express (God Class).

## O que foi entregue

| Item | Onde |
|---|---|
| Skill (`SKILL.md` + 6 arquivos de referência, 1.869 linhas) | [code-smells-project/.claude/skills/refactor-arch/](code-smells-project/.claude/skills/refactor-arch/) — copiada idêntica nos 3 projetos |
| Relatórios de auditoria (61 findings) | [reports/audit-project-1.md](reports/audit-project-1.md) · [audit-project-2.md](reports/audit-project-2.md) · [audit-project-3.md](reports/audit-project-3.md) |
| Relatórios de validação (antes/depois) | [reports/validation-project-1.md](reports/validation-project-1.md) · [validation-project-2.md](reports/validation-project-2.md) · [validation-project-3.md](reports/validation-project-3.md) |
| Código refatorado dos 3 projetos | [code-smells-project/src/](code-smells-project/src/) · [ecommerce-api-legacy/src/](ecommerce-api-legacy/src/) · [task-manager-api/src/](task-manager-api/src/) |
| Scripts de validação de endpoints | [scripts/](scripts/) |

Resultado consolidado:

| Projeto | Stack | Findings | Endpoints | Status idêntico ao baseline | Diferenças intencionais |
|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 21 | 19 | 30/30 | 3 (SQLi corrigida, 2 backdoors removidos) |
| ecommerce-api-legacy | Node.js + Express 4 | 18 | 3 | 5/5 | 3 (rotas admin exigem credencial) |
| task-manager-api | Python + Flask 3.0 + SQLAlchemy | 22 | 22 | 33/33 | 9 (auth nas rotas sensíveis + política de senha) |

Todos os critérios de aceite foram atingidos nos 3 projetos — detalhamento na
[seção C](#c-resultados).

## Estrutura do repositório

```
.
├── README.md
├── reports/                      # relatórios de auditoria (Fase 2) e de validação (Fase 3)
├── scripts/                      # baterias de smoke test usadas no baseline e na validação
│
├── code-smells-project/          # Projeto 1 — Python/Flask (monolito)
│   ├── .claude/skills/refactor-arch/
│   │   ├── SKILL.md
│   │   └── references/{project-analysis,antipatterns,report-template,
│   │                   mvc-guidelines,refactor-playbook,validation}.md
│   ├── src/{config,database,models,validators,services,controllers,views,middlewares}/
│   ├── src/app.py                # composition root (create_app)
│   ├── run.py                    # entry point
│   └── .env.example
│
├── ecommerce-api-legacy/         # Projeto 2 — Node.js/Express (God Class)
│   ├── .claude/skills/refactor-arch/
│   ├── src/{config,database,models,services,controllers,routes,middlewares,utils,validators}/
│   ├── src/app.js                # composition root (createApp, sem listen)
│   ├── server.js                 # entry point
│   └── .env.example
│
└── task-manager-api/             # Projeto 3 — Python/Flask + SQLAlchemy (semi-organizado)
    ├── .claude/skills/refactor-arch/
    ├── src/{config,domain,models,validators,services,controllers,views,middlewares,utils}/
    ├── src/app.py                # application factory
    ├── run.py · seed.py
    └── .env.example
```

---

# A) Análise Manual

Leitura integral dos três projetos (2.118 linhas) antes de escrever a skill, para que o
catálogo de anti-patterns nascesse de problemas reais e não de uma lista genérica.

**Método:** classificação de cada arquivo por camada, matriz de responsabilidades misturadas,
e verificação de uso real de cada símbolo (o que revelou a "camada fantasma" do projeto 3).
Onde possível, cada achado foi **confirmado em execução**, não só por leitura.

Cota exigida pelo desafio (≥5 problemas por projeto, com ≥1 CRITICAL/HIGH, ≥2 MEDIUM,
≥2 LOW) — atendida com folga nos três:

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project | 5 | 5 | 6 | 5 | 21 |
| ecommerce-api-legacy | 4 | 5 | 4 | 5 | 18 |
| task-manager-api | 3 | 4 | 7 | 8 | 22 |

## Projeto 1 — code-smells-project (Python/Flask 3.1.1, 4 arquivos, 780 linhas)

Domínio: API de e-commerce (produtos, usuários, pedidos, relatório de vendas).
Os nomes dos arquivos sugerem MVC (`app.py`, `controllers.py`, `models.py`, `database.py`),
mas as responsabilidades não respeitam camada alguma.

| # | Sev. | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection por concatenação em todas as 19 queries | `models.py:28, 48-50, 110-111, 289-299` … | Bypass de autenticação **confirmado**: `POST /login` com `x' OR '1'='1` responde 200 como `Admin`. O mesmo vetor lê e destrói qualquer tabela — e `database.py:70` já usava placeholders, provando que foi negligência |
| 2 | CRITICAL | `POST /admin/query` executa SQL arbitrário; `/admin/reset-db` apaga tudo — sem auth | `app.py:47-57, 59-78` | Backdoor de administração remota anônima, com o servidor em `0.0.0.0`. Confirmado: query arbitrária retornou 200 e o reset zerou as 4 tabelas |
| 3 | CRITICAL | `SECRET_KEY` e `DEBUG=True` hardcoded | `app.py:7-8` | Segredo versionado vale como comprometido; o debugger do Werkzeug permite execução remota de código |
| 4 | CRITICAL | `/health` devolve a `SECRET_KEY`; `/usuarios` devolve senhas em texto plano | `controllers.py:285-289`, `models.py:83, 99` | Confirmado: endpoint público de health check publica o segredo, e a listagem de usuários entrega `"senha": "admin123"` |
| 5 | CRITICAL | God Module: 315 linhas, 4 domínios, 3 camadas (SQL + regra + formatação) | `models.py:1-315` | Impossível testar a regra de desconto sem banco; mudança em um domínio afeta os outros três |
| 6 | HIGH | Senhas sem hash: armazenadas, comparadas no SQL e devolvidas | `database.py:76-79`, `models.py:110, 127-129` | O vazamento do item 4 entrega senhas utilizáveis, não hashes |
| 7 | HIGH | Criação de pedido escreve em 3 tabelas sem transação nem rollback | `models.py:133-169` | Exceção no meio do laço deixa pedido com itens parciais e estoque debitado errado — corrupção silenciosa |
| 8 | HIGH | Conexão global mutável com `check_same_thread=False`; DDL e seed dentro do getter | `database.py:4-11` | Uma conexão para todas as requisições com a proteção do driver desligada; impossível injetar conexão de teste |
| 9 | HIGH | Debug ligado, `0.0.0.0`, CORS liberado, `"ambiente": "producao"` | `app.py:7-9, 88` | O baseline registrou `Debugger PIN` acessível na rede |
| 10 | HIGH | E-mail/SMS/push simulados com `print` dentro do controller | `controllers.py:208-210, 248-250` | Integração acoplada ao fluxo HTTP: trocar de canal exige editar o controller |
| 11 | HIGH | 19 rotas no entry point, em duas convenções (`add_url_rule` + `@app.route`) | `app.py:11-31, 33, 47, 59` | Não existe camada de View; adicionar rota exige editar o arquivo que também guarda o segredo |
| 12 | MEDIUM | N+1: uma query por pedido e outra por item | `models.py:187-199, 219-231` | 50 pedidos com 4 itens = 251 queries |
| 13 | MEDIUM | Duplicação: listagem de pedidos e validação de produto | `models.py:171-233`, `controllers.py:28-54 / 72-90` | Já divergiu: o `PUT` aceita nome e categoria que o `POST` rejeita |
| 14 | MEDIUM | 16 blocos `except Exception` devolvendo `str(e)`, sem handler central | `controllers.py:10-12, 21-22, …` | Vaza fragmento de SQL ao cliente e descarta o stacktrace |
| 15 | MEDIUM | Validação sem checagem de tipo | `controllers.py:43, 118-121, 146-162` | `preco` como string gera 500 em vez de 400; e-mail nunca é validado |
| 16 | MEDIUM | 17 `print` como log, incluindo auditoria de login | `controllers.py:8, 179, 182, 208-210` … | Sem nível nem destino: o registro de login se perde no stdout |
| 17 | MEDIUM | Mapeamento `row → dict` repetido 6× | `models.py:12-21, 31-40, 79-86` … | Foi esse padrão que propagou o campo `senha` para a resposta |
| 18 | LOW | Faixas de desconto como literais (`10000`/`0.1`…) | `models.py:256-262` | Política comercial escondida em comparações |
| 19 | LOW | Parâmetros chamados `id` (shadowing) e idiomas misturados | `models.py:24, 54, 65, 89` | Legibilidade e risco de erro sutil |
| 20 | LOW | Imports não utilizados | `models.py:2`, `database.py:2` | Sugere dependências entre camadas que não existem |
| 21 | LOW | Versão e ambiente hardcoded em dois lugares, já divergentes | `app.py:35-45`, `controllers.py:285-288` | Informa o cliente incorretamente (`"producao"` com `debug=True`) |

## Projeto 2 — ecommerce-api-legacy (Node.js/Express 4.18, 3 arquivos, 180 linhas)

Domínio: plataforma de cursos (LMS) com checkout, matrícula, pagamento e relatório financeiro.

| # | Sev. | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | God Class com 7 responsabilidades: conexão, DDL, seed, rotas, pagamento, matrícula, cache | `src/AppManager.js:4-141` | Caso-limite de violação de MVC: model, view, controller e infra no mesmo arquivo |
| 2 | CRITICAL | Credenciais de produção hardcoded, incluindo `pk_live` de gateway | `src/utils.js:1-7` | Chave de pagamento real versionada no Git — comprometida por definição |
| 3 | CRITICAL | Número completo do cartão e chave do gateway impressos em log | `src/AppManager.js:45` | Confirmado no baseline: `Processando cartão 4111222233334444 na chave pk_live_…`. Violação de PCI-DSS com impacto legal |
| 4 | CRITICAL | Hash caseiro (base64 em laço, sem salt, truncado em 10 chars) e senha default `123456` | `src/utils.js:17-23`, `AppManager.js:68` | Cria contas com credencial previsível e hashes sem valor criptográfico |
| 5 | HIGH | Checkout em 5 níveis de callback, sem transação nem rollback | `src/AppManager.js:28-78` | Falha ao inserir o pagamento deixa a matrícula persistida — matrícula fantasma em fluxo financeiro |
| 6 | HIGH | Estado global mutável: `globalCache` sem TTL e `totalRevenue` nunca atualizado | `src/utils.js:9-10, 25` | Vazamento de memória, impede múltiplas instâncias, e o "faturamento" é um bug latente |
| 7 | HIGH | 11 queries SQL cruas dentro dos handlers HTTP | `src/AppManager.js:37, 40, 50, …` | Schema espalhado por callbacks; nada reutilizável ou testável |
| 8 | HIGH | `DELETE /api/users/:id` ignora o erro e deixa órfãos — declarado na própria resposta | `src/AppManager.js:131-137` | Confirmado: após deletar, o relatório ainda lista a matrícula como `student: "Unknown"` |
| 9 | HIGH | Relatório financeiro e deleção de usuário sem autenticação | `src/AppManager.js:80, 131` | Confirmado: receita, nomes e e-mails retornados sem credencial. O projeto não tem auth em nenhuma rota |
| 10 | MEDIUM | N+1 com contadores manuais de conclusão | `src/AppManager.js:83-128` | 20 cursos × 30 matrículas ≈ 1.221 queries; erro ignorado pode travar a resposta |
| 11 | MEDIUM | Erro tratado de 3 formas diferentes; 4 pontos ignoram o erro; respostas em texto puro | `src/AppManager.js:38, 92, 104, 133` | Contrato de erro imprevisível numa API JSON |
| 12 | MEDIUM | Contrato cifrado (`usr`, `eml`, `pwd`, `c_id`) e sem validação de formato | `src/AppManager.js:29-35` | `cc.startsWith` quebra com 500 se `card` vier como número |
| 13 | MEDIUM | Banco `:memory:` fixo, DDL e seed embutidos na aplicação | `src/AppManager.js:7, 10-23` | Dados perdidos a cada restart, sem caminho de migração |
| 14 | LOW | Aprovação de pagamento por `cc.startsWith("4")` | `src/AppManager.js:46` | Regra financeira escondida em um literal |
| 15 | LOW | `let self = this` convivendo com arrow functions | `src/AppManager.js:26, 50, 54` | Duas estratégias de binding no mesmo método |
| 16 | LOW | Código morto: `totalRevenue` exportado e nunca usado | `src/utils.js:10, 25` | Sugere funcionalidade de receita inexistente |
| 17 | LOW | Laço de 10.000 iterações cujo resultado é descartado | `src/utils.js:19-21` | CPU gasta por cadastro sem ganho de segurança |
| 18 | LOW | `port` no mesmo objeto das credenciais; log de boot informal | `src/utils.js:6`, `src/app.js:13` | Config pública e segredo com o mesmo ciclo de vida |

## Projeto 3 — task-manager-api (Python/Flask 3.0 + SQLAlchemy, 15 arquivos, 1.158 linhas)

Domínio: Task Manager (tarefas, usuários, categorias) com relatórios de produtividade.
É o caso "parcialmente organizado": tem `models/`, `routes/`, `services/` e `utils/` — mas
**não tem camada de controller**, e boa parte do que está nas pastas é código morto.

| # | Sev. | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Senhas com MD5 sem salt | `models/user.py:29, 32` | MD5 é quebrado para senha; as senhas do seed são recuperáveis instantaneamente |
| 2 | CRITICAL | `to_dict()` inclui o hash — propagado a `/login`, `GET /users/<id>` e `POST /users` | `models/user.py:21` | Confirmado: `/login` devolveu `81dc9bdb52d04dc20036dbd8313ed055` (= MD5 de `1234`). Com o item 1, equivale a publicar as senhas |
| 3 | CRITICAL | `SECRET_KEY` e credenciais SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | Dois segredos versionados; `python-dotenv` estava no requirements, indicando intenção nunca implementada |
| 4 | HIGH | Fat routes: 70, 68 e 90 linhas com validação + regra + serialização | `routes/task_routes.py:85-154, 156-223`, `report_routes.py:12-101` | A camada de controller simplesmente não existe — é a violação central de MVC aqui |
| 5 | HIGH | **Camada fantasma**: 19 símbolos definidos e nunca chamados | `services/notification_service.py:4-48`, `utils/helpers.py:19-116`, `models/task.py:38-60` | Duas versões divergentes de cada regra: a "oficial" em `utils/`/`models/` e a inline nas rotas. A estrutura de pastas simula organização que o código não tem |
| 6 | HIGH | Config, CORS, rotas inline e `db.create_all()` em tempo de import | `app.py:9-31` | `import app` cria o banco como efeito colateral; sem factory não há ambiente de teste |
| 7 | HIGH | Token `'fake-jwt-token-' + id` e nenhuma rota protegida | `routes/user_routes.py:207-211` | Token previsível, forjável e nunca verificado; relatórios e deleção de conta abertos |
| 8 | MEDIUM | N+1 em quatro endpoints | `task_routes.py:41-57`, `user_routes.py:22`, `report_routes.py:53-68, 157-165` | `GET /tasks` com 100 tarefas ≈ 201 queries |
| 9 | MEDIUM | Regra de "atrasada" duplicada em 6 lugares, apesar de existir no model | `models/task.py:50-60` vs 6 blocos nas rotas | Mudar a definição exige 6 edições — e uma delas já difere |
| 10 | MEDIUM | 12 `except:` nus, sem handler central | `task_routes.py:62, 236`, `user_routes.py:130, 149` … | Captura até `KeyboardInterrupt` e apaga o stacktrace |
| 11 | MEDIUM | Validação duplicada em 4 lugares e divergente | `task_routes.py:110, 177`, `helpers.py:75, 110` … | `PUT /tasks/<id>` compara `priority` sem converter tipo: `"abc"` gera 500 |
| 12 | MEDIUM | CRUD de categorias dentro do blueprint de relatórios | `report_routes.py:157-223` | Organização por arquivo não corresponde ao domínio |
| 13 | MEDIUM | Regex de e-mail aceita `a@b` (sem TLD) | `user_routes.py:61, 106`, `helpers.py:21` | Cadastro inválido ocupa a coluna `unique` |
| 14 | MEDIUM | Deleção manual em laço em vez de cascade | `user_routes.py:140-142` | Cada novo ponto de deleção precisa repetir o laço, ou deixa tarefas órfãs |
| 15 | LOW | **API deprecated:** 18 usos de `datetime.utcnow()` | `models/task.py:15-16, 52`, `report_routes.py:35-71` … | Deprecada no Python 3.12 e devolve datetime *naive* |
| 16 | LOW | **API deprecated:** 16 usos de `Query.get()` (Legacy Query API) | `task_routes.py:42, 51, 67` … | `LegacyAPIWarning … (deprecated since: 2.0)` confirmado em runtime |
| 17 | LOW | Imports não usados e 3 dependências declaradas sem uso | `app.py:7`, `task_routes.py:7`, `requirements.txt` | `marshmallow`, `requests` e `python-dotenv` nunca importados |
| 18 | LOW | `type(x) == list` em vez de `isinstance` | `task_routes.py:141, 210` | Falha para subclasses |
| 19 | LOW | Magic numbers com constantes equivalentes ignoradas | `task_routes.py:96, 113`, `helpers.py:110-116` | O mínimo de senha (4) está espalhado e é fraco |
| 20 | LOW | `if/else` devolvendo booleano literal | `models/task.py:38-48`, `models/user.py:34-38` | Ruído que esconde a intenção |
| 21 | LOW | 21 `print` como log, incluindo mensagens de erro | `task_routes.py:149, 153`, `user_routes.py:83` … | O erro real fica no stdout, o cliente recebe 500 genérico |
| 22 | LOW | Nomes pobres (`t`, `u`, `c`) e contadores `p1..p5` | `report_routes.py:24-28`, `task_routes.py:16` | A relação entre `p1` e `critical` só existe na cabeça do autor |

---

# B) Construção da Skill

## Decisões de design

**1. `SKILL.md` é o roteiro; as referências são o conhecimento.**
O `SKILL.md` (145 linhas) descreve *o que fazer* — as três fases, o formato de saída, o gate de
confirmação e as regras invioláveis. Os seis arquivos de referência (1.724 linhas) carregam o
*conhecimento de domínio* e são lidos sob demanda, na fase em que importam. Isso mantém o
prompt de entrada pequeno e permite crescer o catálogo sem inflar o contexto.

| Arquivo | Fase | Conteúdo |
|---|---|---|
| `project-analysis.md` | 1 | Heurísticas de detecção (manifesto → linguagem/framework, rotas, banco), mapeamento de camadas, matriz de responsabilidades misturadas |
| `antipatterns.md` | 2 | 23 anti-patterns com sinais de detecção executáveis, falsos positivos, e seção obrigatória de APIs deprecated |
| `report-template.md` | 2 | Formato exato do relatório, regras de contagem e de `arquivo:linha` |
| `mvc-guidelines.md` | 3 | Responsabilidade de cada camada, regra de dependência, estrutura por stack, checklist de conformidade |
| `refactor-playbook.md` | 3 | 16 padrões de transformação com exemplos antes/depois em Python e JavaScript |
| `validation.md` | 3 | Protocolo de baseline, boot, smoke test e rollback |

**2. Baseline antes de tocar em código.** Foi a decisão mais importante e não estava no
enunciado: a Fase 3 começa capturando status e payload de **todos** os endpoints do projeto
original. Sem isso, "os endpoints continuam respondendo" é uma afirmação sem prova. Foi o
baseline que transformou achados de leitura em evidência — por exemplo, provar que
`POST /login` com `x' OR '1'='1` retornava 200 como `Admin`.

**3. O gate da Fase 2 é uma regra inviolável, não uma sugestão.** O `SKILL.md` abre com seis
regras invioláveis, e a primeira é que as Fases 1 e 2 são somente leitura. O gate imprime o
relatório e para; qualquer resposta que não seja afirmativa encerra a skill sem modificar
arquivo algum.

**4. Preservar o contrato externo, e declarar cada exceção.** Refatoração não é redesign de
API. A skill exige que mesmas rotas, métodos e códigos de status sejam mantidos — com uma
exceção explícita: falha de segurança que *obriga* mudança de payload (hash de senha exposto,
backdoor de SQL). Toda exceção tem que aparecer no relatório final, ligada ao finding que a
motivou. Foi o que permitiu remover dois endpoints do projeto 1 sem que isso fosse "quebrar a
aplicação".

**5. Severidade com regra de ajuste, não com tabela fixa.** O catálogo define a escala do
desafio e as condições de escalada: sobe um nível quando o trecho está em caminho de
autenticação/pagamento ou quando o dado é credencial/PII; desce quando é comprovadamente
inalcançável. Isso resolveu casos como `console.log` — LOW isolado, CRITICAL quando imprime o
número do cartão (projeto 2, finding 3).

**6. Sinais de detecção executáveis.** Cada anti-pattern traz o `grep`/comando que o encontra,
mais uma seção de falsos positivos. "Código ruim" não é acionável; `execute\(.*(\+|%|\.format\()`
é. E o catálogo instrui a **confirmar abrindo o trecho** antes de registrar — o grep é ponto de
partida, não prova.

## Quais anti-patterns entraram, e por quê

Partiram da análise manual, não de uma lista teórica. O critério foi recorrência mais impacto
arquitetural. Dos 23, **16 aparecem em mais de um projeto** — é o que dá à skill a chance de
ser útil no quarto projeto, que ela nunca viu:

| Anti-pattern | Sev. | P1 | P2 | P3 |
|---|---|---|---|---|
| Hardcoded secrets | CRITICAL | ✓ | ✓ | ✓ |
| Dado sensível na resposta da API | CRITICAL | ✓ | — | ✓ |
| Autenticação/criptografia inadequada | CRITICAL | ✓ | ✓ | ✓ |
| God Class / God Module | CRITICAL | ✓ | ✓ | — |
| Endpoint perigoso sem proteção | CRITICAL | ✓ | ✓ | ✓ |
| SQL Injection por concatenação | CRITICAL | ✓ | — | — |
| Fat Controller / regra na apresentação | HIGH | ✓ | ✓ | ✓ |
| Ausência de camada de dados | HIGH | ✓ | ✓ | — |
| Estado global mutável | HIGH | ✓ | ✓ | — |
| Escrita multi-tabela sem transação | HIGH | ✓ | ✓ | ✓ |
| Config de desenvolvimento em código | HIGH | ✓ | ✓ | ✓ |
| Aninhamento profundo / callback hell | HIGH | — | ✓ | — |
| **Camada fantasma** | HIGH | — | — | ✓ |
| N+1 queries | MEDIUM | ✓ | ✓ | ✓ |
| Exceção engolida / erro não centralizado | MEDIUM | ✓ | ✓ | ✓ |
| Lógica duplicada | MEDIUM | ✓ | ✓ | ✓ |
| **APIs deprecated** | MEDIUM | — | — | ✓ |
| Validação ausente ou inconsistente | MEDIUM | ✓ | ✓ | ✓ |
| `print`/`console.log` como log | MEDIUM | ✓ | ✓ | ✓ |
| Magic numbers | LOW | ✓ | ✓ | ✓ |
| Nomenclatura pobre / shadowing | LOW | ✓ | ✓ | ✓ |
| Código morto / import não usado | LOW | ✓ | ✓ | ✓ |
| Boilerplate de serialização | LOW | ✓ | — | ✓ |

Dois merecem nota:

- **Camada fantasma (AP-13)** nasceu do projeto 3 e não existiria se eu tivesse analisado só o
  monolito. É o anti-pattern mais fácil de passar batido em auditoria automatizada: a estrutura
  de diretórios *parece* correta. A detecção é contraintuitiva — para cada símbolo definido em
  `services/` ou `utils/`, buscar uso externo; **uma única ocorrência significa que só a
  definição existe**.
- **APIs deprecated (AP-17)** é exigência do desafio, e a tabela por ecossistema envelhece. Por
  isso o catálogo manda triangular: símbolos conhecidos, **avisos de runtime**
  (`python -W all`, `node --pending-deprecation`) e `npm outdated`/`pip list --outdated`. Foi o
  runtime que provou o `LegacyAPIWarning` do SQLAlchemy no projeto 3 — e foi ele também que
  sustentou o "nenhuma encontrada" honesto nos projetos 1 e 2.

## Como garanti que a skill é agnóstica de tecnologia

1. **Detecção por manifesto, nunca por nome de arquivo.** A Fase 1 parte de
   `requirements.txt`/`package.json`/`pom.xml`/`go.mod`/`composer.json`/`Cargo.toml` e confirma
   pelos imports. Nenhuma referência a `models.py` ou `AppManager.js` na skill.
2. **Sinais de detecção por linguagem.** Cada anti-pattern traz variantes de busca para Python
   e JS/TS, mais o padrão conceitual para as demais stacks.
3. **Playbook bilíngue.** Dos 16 padrões, os principais têm exemplo antes/depois nas duas
   linguagens — inclusive um caso que só existe em Node (promisificar driver de callback).
4. **Estrutura-alvo definida por responsabilidade, não por pasta.** As guidelines fixam
   *responsabilidades e regra de dependência*; os nomes de diretório seguem a convenção do
   ecossistema detectado (`views/` no Flask, `routes/` no Express, `@RestController` no Spring).
5. **Granularidade derivada do domínio.** Um model e um controller por *agregado de domínio*
   descoberto na Fase 1 — não um por arquivo legado. Foi isso que produziu 3 models no projeto 1
   (produto, usuário, pedido) a partir de um único `models.py`.
6. **Regra explícita contra camada vazia.** "Não crie `services/` se não houver regra
   multi-agregado" — camada vazia por simetria é o próprio AP-13.
7. **Teste real:** a mesma pasta `.claude/skills/refactor-arch/`, byte a byte idêntica, rodou
   nos 3 projetos (`diff -r` confirma). Nenhum ajuste por projeto.

## Desafios encontrados

**1. "Aplicação continua funcionando" é vago — e o gap virou o baseline.** O enunciado pede
validar que a app funciona. Sem capturar o comportamento *antes*, qualquer resultado passa.
Escrevi `validation.md` exigindo baseline com caminhos felizes **e** os de erro (404/400),
porque foi justamente nos códigos de erro que a refatoração quase regrediu.

**2. Correção de segurança conflita com "preservar o contrato".** Manter o `/health` que vaza
a `SECRET_KEY` é preservar o contrato; consertar é quebrá-lo. Resolvi com a categoria
"diferença intencional": permitida, obrigatoriamente ligada a um finding e declarada no
relatório. Sem essa válvula, a skill teria que escolher entre não corrigir ou mentir na validação.

**3. Ordem de validação escondendo um caminho de negócio.** No projeto 2, coloquei a exigência
de senha forte no validador de entrada do checkout. Resultado: dois casos do baseline caíram de
200/404 para 400 — a senha só é necessária quando o checkout **cria** a conta. A regra pertencia
ao cadastro de usuário, não à entrada da requisição. A validação pegou; a leitura do código não
tinha pegado.

**4. Trocar API deprecated pode mudar semântica silenciosamente.** `datetime.utcnow()` →
`datetime.now(timezone.utc)` parece mecânico, mas o primeiro devolve datetime *naive* e o
segundo *aware*: comparar os dois levanta `TypeError`, e as colunas `DateTime` do SQLite
descartam o offset. Mantive UTC *naive* (`now_utc()`), removendo a API deprecada sem alterar
armazenamento nem payload, e registrei a migração para *aware* como mudança separada. O
playbook ganhou um aviso explícito sobre isso.

**5. Default seguro versus paridade com o baseline.** Ao aplicar a application factory no
projeto 1, o debug ficou ligado por default em desenvolvimento — reintroduzindo o finding 9 que
eu tinha acabado de corrigir. A validação estrutural pegou. Debug virou opt-in explícito, em
qualquer ambiente.

**6. Dado de demonstração é a exceção incômoda.** Os seeds precisam de senha para o usuário de
exemplo ser utilizável. Em vez de fingir que não é segredo, os três projetos passaram a semear
apenas fora de produção, com a senha do seed sobrescrevível por variável de ambiente — e o
resíduo está declarado nos relatórios de validação.

**7. Ambiente antes do código.** O `flask==3.1.1` do projeto 1 exige Python ≥3.9 e a máquina
tinha 3.8 sem `pip`. Preferi instalar o runtime correto a relaxar a versão pinada do projeto:
mudar o manifesto para o ambiente caber é esconder um problema de compatibilidade.

---

# C) Resultados

## Resumo dos relatórios de auditoria

| | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Stack detectada | Python + Flask 3.1.1 | Node.js + Express 4.18.2 | Python + Flask 3.0.0 + SQLAlchemy 2.0.51 |
| Domínio detectado | E-commerce (produtos, usuários, pedidos) | LMS com checkout | Task Manager com relatórios |
| Arquivos / linhas | 4 / 780 | 3 / 180 | 15 / 1.158 |
| Endpoints | 19 | 3 | 22 |
| Findings | 21 | 18 | 22 |
| CRITICAL / HIGH | 5 / 5 | 4 / 5 | 3 / 4 |
| MEDIUM / LOW | 6 / 5 | 4 / 5 | 7 / 8 |
| APIs deprecated | nenhuma (verificado) | nenhuma (verificado) | 2 tipos, 34 ocorrências |

## Antes e depois

| | Antes | Depois |
|---|---|---|
| **Projeto 1** | 4 arquivos, 780 linhas; camadas: nenhuma | 33 arquivos, 1.289 linhas; `config, database, models, validators, services, controllers, views, middlewares` |
| **Projeto 2** | 3 arquivos, 180 linhas; God Class de 141 linhas | 25 arquivos, 1.076 linhas; `config, database, models, services, controllers, routes, middlewares, utils, validators` |
| **Projeto 3** | 15 arquivos, 1.158 linhas; sem controllers, `services/` morto | 37 arquivos, 1.880 linhas; `config, domain, models, validators, services, controllers, views, middlewares, utils` |

Estrutura resultante do projeto 1 (as outras seguem a convenção do respectivo ecossistema):

```
src/
├── config/{settings,logging_config}.py     # env → configuração, sem segredo literal
├── database/{connection,schema}.py         # conexão por request + DDL/seed explícitos
├── models/{produto,usuario,pedido}_model.py
├── validators/{produto,usuario,pedido}_validator.py
├── services/notification_service.py
├── controllers/{produto,usuario,pedido,relatorio,health}_controller.py
├── views/{produto,usuario,pedido,relatorio,health}_routes.py
├── middlewares/error_handler.py
└── app.py                                  # composition root (create_app)
run.py · .env.example
```

## Evidências de correção (medidas, não afirmadas)

**Bypass de autenticação por SQL Injection — projeto 1**

```console
# ANTES
$ curl -X POST localhost:5000/login -d '{"email":"x'"'"' OR '"'"'1'"'"'='"'"'1","senha":"x'"'"' OR '"'"'1'"'"'='"'"'1"}'
{"dados":{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},"sucesso":true}   # 200

# DEPOIS
{"erro":"Email ou senha inválidos","sucesso":false}                                        # 401
```

**Segredo e senhas vazando pela API — projeto 1**

```console
# ANTES  GET /health   → "secret_key":"minha-chave-super-secreta-123", "debug":true, "db_path":"loja.db"
# DEPOIS GET /health   → {"counts":{...},"database":"connected","status":"ok","versao":"1.0.0"}

# ANTES  GET /usuarios → {"email":"admin@loja.com","senha":"admin123",...}
# DEPOIS GET /usuarios → {"email":"admin@loja.com","nome":"Admin","tipo":"admin",...}
```

**Dados de cartão em log — projeto 2**

```console
# ANTES
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef

# DEPOIS
{"ts":"...","level":"info","message":"Cobrança processada",
 "context":{"cardLast4":"4444","amount":497,"status":"PAID","gateway":"simulado"}}

$ grep -cE "4111222233334444|pk_live" server.log
0
```

**Integridade referencial — projeto 2**

```console
# ANTES  (após DELETE /api/users/1)  revenue 1994, students [{"student":"Unknown"},{"student":"Unknown"}]
# DEPOIS (ON DELETE CASCADE)         revenue 0,    students []
```

**Hash de senha na resposta — projeto 3**

```console
# ANTES  POST /login → "password":"81dc9bdb52d04dc20036dbd8313ed055"   (MD5 de "1234")
#                      "token":"fake-jwt-token-1"
# DEPOIS POST /login → sem campo password
#                      "token":"eyJzdWIiOjEsInJvbGUiOiJhZG1pbiJ9.amPcFA..."   (assinado, com TTL)
```

**APIs deprecated — projeto 3**

```console
# ANTES  LegacyAPIWarning: The Query.get() method is considered legacy ... (deprecated since: 2.0)
# DEPOIS $ grep -rn "utcnow()\|\.query\.get(" src/ run.py seed.py   → nenhuma ocorrência em código
#        $ python -c "import warnings; warnings.simplefilter('always'); import src.app"
#          (nenhum DeprecationWarning ou LegacyAPIWarning)
```

**Camada fantasma — projeto 3** (ocorrências do símbolo em todo o projeto; 1 = só a definição)

| Símbolo | Antes | Depois |
|---|---|---|
| `NotificationService` | 1 | 4 (usado na atribuição de tarefa) |
| `Task.is_overdue()` | 1 | 4 (única definição de "atrasada") |
| `VALID_STATUSES` | 1 | 4 (validadores + model) |
| `marshmallow`, `requests`, `python-dotenv` | declaradas, 0 imports | removidas do requirements |

## Checklist de validação do desafio

**Fase 1 — Análise** (3/3 projetos)

- [x] Linguagem detectada corretamente — Python 3.9+, JavaScript/Node 20, Python 3.9+
- [x] Framework detectado corretamente — Flask 3.1.1, Express 4.18.2, Flask 3.0.0 + SQLAlchemy 2.0.51
- [x] Domínio descrito corretamente — e-commerce, LMS com checkout, task manager
- [x] Número de arquivos condiz com a realidade — 4, 3 e 15 (conferido com `find | wc -l`)

**Fase 2 — Auditoria** (3/3 projetos)

- [x] Relatório segue o template de `report-template.md`
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW), numeração contínua
- [x] Mínimo de 5 findings — 21, 18 e 22
- [x] Detecção de APIs deprecated incluída — 34 ocorrências no projeto 3; nos projetos 1 e 2 a
      verificação foi executada (símbolos + avisos de runtime + `npm outdated`) e o resultado
      negativo está registrado no relatório
- [x] Skill pausou e pediu confirmação antes da Fase 3 — três vezes, uma por projeto

**Fase 3 — Refatoração** (3/3 projetos)

- [x] Estrutura de diretórios segue o padrão MVC
- [x] Configuração extraída para módulo de config, sem hardcoded — `grep` por segredo literal
      volta vazio nos três
- [x] Models criados para abstrair dados — nenhuma query fora de `models/`/`database/`
- [x] Views/Routes separadas, apenas mapeamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado — middleware nos três; nenhum `except:` nu ou erro ignorado
- [x] Entry point claro — `run.py`, `server.js`, `run.py`
- [x] Aplicação inicia sem erros — log de boot limpo, debug off
- [x] Endpoints originais respondem corretamente — 30/30, 5/5 e 33/33 com status idêntico ao
      baseline; as 15 diferenças restantes são intencionais, cada uma ligada a um finding

**Critérios de aceite** (obrigatórios nos 3 projetos)

| Critério | P1 | P2 | P3 |
|---|---|---|---|
| Fase 1 detecta a stack corretamente | ✓ | ✓ | ✓ |
| Fase 2 encontra ≥ 5 findings | ✓ 21 | ✓ 18 | ✓ 22 |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ 10 | ✓ 9 | ✓ 7 |
| Fase 3 aplicação funciona após refatoração | ✓ | ✓ | ✓ |

## Logs das aplicações após a refatoração

```console
# Projeto 1
$ python run.py
WARNING  [src.app] SECRET_KEY não definida no ambiente — usando chave efêmera de desenvolvimento.
INFO     [src.database.connection] Banco populado com dados de demonstração
INFO     [src.app] Servidor iniciado em http://127.0.0.1:5000 (ambiente: development)
 * Debug mode: off
$ curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/health
200
```

```console
# Projeto 2
$ ADMIN_API_KEY=... npm start
{"ts":"...","level":"info","message":"Banco populado com dados de demonstração"}
{"ts":"...","level":"info","message":"Servidor iniciado",
 "context":{"service":"lms-api","port":3000,"env":"development","database":":memory:"}}
```

```console
# Projeto 3
$ python seed.py && python run.py
Seed concluído com sucesso!  3 usuários · 4 categorias · 10 tasks
WARNING  [src.app] SECRET_KEY não definida no ambiente — usando chave efêmera de desenvolvimento.
INFO     [src.services.notification_service] SMTP não configurado — notificações serão registradas no log
INFO     [src.app] Servidor iniciado em http://127.0.0.1:5000 (ambiente: development)
 * Debug mode: off
```

## Riscos residuais declarados

Refatoração não é redesign; o que ficou fora está registrado em vez de escondido:

- **Projeto 2:** o checkout não autentica o titular do e-mail (comportamento do legado);
  autorização administrativa é por chave estática (`x-api-key`), suficiente para fechar a rota
  mas não substitui auth de usuário.
- **Projeto 3:** o CRUD de tarefas/categorias e o `GET /users` seguem sem autenticação —
  protegi o que expõe ou altera dados de terceiros; estender ao resto muda o contrato de 11
  endpoints e é decisão de produto. Datas seguem UTC *naive* por compatibilidade de payload.
- **Todos:** credenciais de demonstração nos seeds, que só rodam fora de produção.

Detalhamento em cada `reports/validation-project-*.md`.

---

# D) Como Executar

## Pré-requisitos

| Requisito | Versão usada | Observação |
|---|---|---|
| Claude Code | — | A skill vive em `.claude/skills/refactor-arch/` de cada projeto |
| Python | 3.9.5 | O projeto 1 exige ≥3.9 (`flask==3.1.1`); em Ubuntu 20.04: `sudo apt install python3.9 python3.9-venv python3-pip` |
| Node.js | 20.20.2 | Projeto 2 |
| `curl` | qualquer | Usado pelos scripts de validação |

Nenhuma dependência nova foi introduzida na refatoração: o hash de senha usa
`werkzeug.security` (Python) e `crypto.scrypt` nativo (Node); a assinatura de token usa
`itsdangerous`, que já vem com o Flask.

## Executando a skill

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

A skill imprime o resumo da Fase 1, gera o relatório da Fase 2 e **para**, pedindo confirmação:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Responder `n` (ou qualquer coisa que não seja afirmativa) encerra sem modificar nenhum arquivo.
Com `y`, a Fase 3 captura o baseline, refatora e valida.

> Como esta execução foi feita a partir da raiz do repositório, as três fases foram executadas
> seguindo o `SKILL.md` de cada projeto, com o gate de confirmação respondido manualmente em
> cada um. Os relatórios em `reports/` são a saída dessas execuções.

## Rodando as aplicações refatoradas

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
python3.9 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # opcional: em dev, a SECRET_KEY é gerada de forma efêmera
.venv/bin/python run.py       # http://127.0.0.1:5000
```

```bash
# Projeto 2 — Node.js/Express
cd ecommerce-api-legacy
npm install
ADMIN_API_KEY=uma-chave-local npm start   # http://127.0.0.1:3000
# sem ADMIN_API_KEY, as rotas administrativas respondem 401 (fail closed)
```

```bash
# Projeto 3 — Python/Flask + SQLAlchemy
cd task-manager-api
python3.9 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py      # popula 3 usuários, 4 categorias, 10 tasks
.venv/bin/python run.py       # http://127.0.0.1:5000
```

## Validando que a refatoração funcionou

Cada script exercita todos os endpoints do projeto (caminhos felizes, 400, 401, 404, 409) e
grava status e corpo de cada resposta em um diretório, para comparação:

```bash
# Projeto 1 — 33 chamadas nos 19 endpoints (inclui sonda de SQL Injection no login)
./scripts/smoke-project-1.sh /tmp/depois-p1

# Projeto 2 — 8 chamadas nos 3 endpoints
./scripts/smoke-project-2.sh /tmp/depois-p2

# Projeto 3 — 42 chamadas nos 22 endpoints
./scripts/smoke-project-3.sh /tmp/depois-p3
```

Comparando duas execuções (por exemplo, antes e depois de uma mudança):

```bash
for f in /tmp/antes-p1/*.status; do
  n=$(basename "$f" .status)
  b=$(cat "$f"); a=$(cat "/tmp/depois-p1/$n.status")
  [ "$b" = "$a" ] && echo "✓ $n ($b)" || echo "✗ $n: antes=$b depois=$a"
done
```

Checagens estruturais (todas devem voltar vazias):

```bash
cd code-smells-project
grep -rniE "(secret|password|api_?key|token)[[:space:]]*[:=][[:space:]]*['\"][^'\"]{3,}" src/ run.py \
  | grep -vE "os\.environ|getenv|senha_hash"      # segredo literal
grep -rlE "SELECT |INSERT |UPDATE |DELETE FROM" src/ | grep -vE "src/(models|database)/"   # SQL fora da camada de dados
grep -rn "from flask import\|jsonify\|request\." src/models/                               # HTTP dentro de models
grep -rnE "^[[:space:]]*print\(" src/ run.py                                               # print de diagnóstico
grep -rnE "execute\(.*(\+|%|\.format\(|f['\"])" src/                                       # concatenação em query
```

Verificações específicas de segurança (projeto 1):

```bash
# SQL Injection no login deve responder 401
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"x'"'"' OR '"'"'1'"'"'='"'"'1","senha":"x'"'"' OR '"'"'1'"'"'='"'"'1"}'

# /health não deve conter secret_key; /usuarios não deve conter senha
curl -s localhost:5000/health   | grep -c secret_key   # 0
curl -s localhost:5000/usuarios | grep -c '"senha"'    # 0

# backdoors devem responder 404
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:5000/admin/query \
  -H 'Content-Type: application/json' -d '{"sql":"SELECT 1"}'
```

Verificação de autenticação (projeto 3):

```bash
TOKEN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")

curl -s -o /dev/null -w 'sem token:  %{http_code}\n' localhost:5000/reports/summary
curl -s -o /dev/null -w 'com token:  %{http_code}\n' localhost:5000/reports/summary -H "Authorization: Bearer $TOKEN"
```

## Histórico de commits

```
0bc32be refactor(project-3): introduz camada de controller e elimina camada fantasma
3a3a996 refactor(project-2): reestrutura ecommerce-api-legacy para MVC em camadas
0cf8bfb refactor(project-1): reestrutura code-smells-project para MVC em camadas
7c242e8 feat(skill): cria skill refactor-arch de auditoria e refatoração MVC
6d1ce62 chore: initial commit with refactor challenge boilerplate
```

---

## Sobre o desafio

Escala de severidade adotada (definida pelo enunciado e implementada em
`references/antipatterns.md`):

- **CRITICAL** — falha grave de arquitetura ou segurança: credenciais hardcoded, SQL Injection,
  God Class com banco, lógica e roteamento no mesmo arquivo.
- **HIGH** — violação forte de MVC/SOLID: regra de negócio pesada no controller, acoplamento
  sem injeção de dependência, estado global mutável.
- **MEDIUM** — padronização, duplicação e performance moderada: N+1, middleware mal usado,
  validação ausente.
- **LOW** — legibilidade: nomes ruins, magic numbers, código morto.

Ferramenta: **Claude Code**, recurso *Custom Skills* (`.claude/skills/`), arquivos de
referência em Markdown. O enunciado completo do desafio está em `to-do.md`.
