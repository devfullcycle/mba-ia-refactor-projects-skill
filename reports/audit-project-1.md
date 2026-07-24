```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.9+ (requerido por flask==3.1.1)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        API de e-commerce — catálogo de produtos, usuários, pedidos e relatório de vendas
Architecture:  Monolítica em 4 arquivos. Os nomes sugerem MVC (app/controllers/models/database),
               mas as responsabilidades não respeitam as camadas: models.py acumula SQL, regra
               de negócio e formatação de resposta; app.py mistura entry point, configuração,
               segredo e roteamento. Sem config, sem middlewares, sem services.
Source files:  4 files analyzed | ~780 lines of code
Entry point:   app.py:80 (`if __name__ == "__main__"`, app.run em 0.0.0.0:5000 com debug=True)
Routes:        19 endpoints (16 via add_url_rule em app.py:11-31 + 3 via @app.route em app.py:33, 47, 59)
DB tables:     produtos, usuarios, pedidos, itens_pedido (DDL em database.py:14-53)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
```

Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-07-24

## Summary

CRITICAL: 5 | HIGH: 5 | MEDIUM: 6 | LOW: 5

| Camada MVC | Situação |
|---|---|
| Config | **Ausente** — configuração literal em `app.py:7-8`; caminho do banco em `database.py:5` |
| Models | **Corrompida** — `models.py` faz SQL + regra de negócio + serialização para 4 domínios |
| Views/Routes | **Ausente** — roteamento dentro do entry point (`app.py:11-31`), em duas convenções |
| Controllers | **Parcial** — `controllers.py` existe, mas repassa regra ao "model" e executa efeitos colaterais |
| Middlewares | **Ausente** — nenhum tratamento de erro, auth ou log centralizado |
| Entry point | **Sobrecarregado** — cria app, define segredo, registra 19 rotas e ainda declara 3 handlers inline |

## Findings

### 1. [CRITICAL] SQL Injection por Concatenação (AP-04)
File: models.py:28, 48-50, 58-61, 68, 92, 110-111, 127-129, 140, 148-151, 155-161, 163-166, 174, 188, 192, 220, 224, 280-281, 291-297
Description: Todas as 19 queries de `models.py` são montadas por concatenação de string com
             entrada do usuário. Em `login_usuario` (models.py:109-111) e-mail e senha entram
             direto no `WHERE`; em `buscar_produtos` (models.py:289-299) os filtros `q`,
             `categoria`, `preco_min` e `preco_max` vêm da querystring sem tratamento.
Impact: Bypass de autenticação **confirmado em execução**: `POST /login` com
        `{"email":"x' OR '1'='1","senha":"x' OR '1'='1"}` responde `200` autenticado como
        `Admin` (`tipo: admin`). O mesmo vetor permite ler e destruir qualquer tabela. O
        projeto já usa placeholders em `database.py:70-72, 80-83`, então a correção é local.
Recommendation: Substituir toda concatenação por queries parametrizadas (`?`) e isolar acesso
                a dados em model por agregado. Autenticação deve buscar por e-mail e comparar
                hash na aplicação, nunca no `WHERE` — padrão RP-03, RP-04.

### 2. [CRITICAL] Backdoor de Administração sem Autenticação (AP-06)
File: app.py:47-57, 59-78
Description: `POST /admin/query` recebe `{"sql": "..."}` e executa direto no banco, com commit
             (app.py:69-76). `POST /admin/reset-db` apaga as 4 tabelas (app.py:51-54). Nenhuma
             das duas exige autenticação, e o servidor sobe em `0.0.0.0` (app.py:88).
Impact: Qualquer cliente na rede lê, altera ou destrói o banco inteiro. Confirmado no baseline:
        `POST /admin/query` → 200 com o resultado da query; `POST /admin/reset-db` → 200 e
        `GET /produtos` passa a devolver lista vazia.
Recommendation: Remover ambos os endpoints — SQL arbitrário via HTTP é backdoor por design, não
                se protege. Reset de banco vira script/CLI de desenvolvimento — padrão RP-14.

### 3. [CRITICAL] Credenciais e Segredos Hardcoded (AP-02)
File: app.py:7-8, database.py:5, controllers.py:285-289
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` (app.py:7) e `DEBUG = True`
             (app.py:8) literais; `db_path = "loja.db"` fixo (database.py:5); metadados de
             ambiente hardcoded no health check (controllers.py:285-288).
Impact: Segredo versionado no Git — vale como comprometido e exige rotação. Sem separação por
        ambiente, não há como subir dev e produção com configurações distintas.
Recommendation: Módulo `config/settings.py` lendo `os.environ`, com `.env.example` versionado e
                falha explícita no boot se `SECRET_KEY` estiver ausente — padrão RP-02.

### 4. [CRITICAL] Dado Sensível Exposto na Resposta da API (AP-03)
File: controllers.py:276-290, models.py:83, 99
Description: `GET /health` devolve `"secret_key": "minha-chave-super-secreta-123"`,
             `"db_path"`, `"debug": true` e `"ambiente": "producao"` (controllers.py:285-289).
             O mapeamento de usuário inclui o campo `senha` (models.py:83, 99), propagado por
             `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Confirmado no baseline — `GET /health` publica a SECRET_KEY e `GET /usuarios` devolve
        as senhas em texto plano de todos os usuários (`"senha": "admin123"`). Endpoint público
        de health check funciona como vazamento de credenciais.
Recommendation: Health check devolve apenas `status` e conectividade. Serialização de usuário
                sem campo de senha, com uma única função de saída por model — padrão RP-04, RP-16.

### 5. [CRITICAL] God Module — models.py concentra 4 domínios e 3 camadas (AP-01, AP-08)
File: models.py:1-315
Description: Um arquivo de 315 linhas com 19 funções cobrindo produtos (models.py:4-70,
             285-314), usuários (72-131), pedidos (133-233) e relatórios (235-273). Cada função
             mistura acesso a dados, regra de negócio (cálculo de total, baixa de estoque,
             faixas de desconto em models.py:256-262) e formatação da resposta (dicionários de
             saída em models.py:12-21, 31-40, 79-86, 95-102, 194-199, 304-313).
Impact: Impossível testar em isolamento — não há como exercitar a regra de desconto sem banco.
        Qualquer mudança em um domínio toca o arquivo usado pelos outros três.
Recommendation: Separar em `models/{produto,usuario,pedido}_model.py` (dados + invariantes) e
                `controllers/*_controller.py` (fluxo), com serialização única por model —
                padrão RP-01, RP-05.

### 6. [HIGH] Senhas em Texto Plano — Armazenamento e Comparação (AP-05)
File: database.py:76-79, models.py:110-111, 127-129
Description: Usuários do seed são inseridos com senha literal (`("Admin", "admin@loja.com",
             "admin123", "admin")`, database.py:76); `criar_usuario` persiste a senha recebida
             sem hash (models.py:126-129); o login compara a senha dentro do SQL (models.py:110).
Impact: Não existe hash em nenhum ponto do fluxo — o vazamento do finding 4 entrega senhas
        utilizáveis, não hashes. Reuso de senha expõe as contas dos usuários em outros serviços.
Recommendation: `werkzeug.security.generate_password_hash` / `check_password_hash` (ou bcrypt),
                com coluna `senha_hash`, e verificação na aplicação — padrão RP-04.

### 7. [HIGH] Escrita Multi-tabela sem Transação (AP-10)
File: models.py:133-169
Description: `criar_pedido` valida estoque (models.py:139-146), insere o pedido (148-152),
             insere cada item e debita estoque em laço (154-166) e só então faz `commit`
             (168) — sem `BEGIN` explícito e sem nenhum `rollback` no arquivo.
Impact: Exceção no meio do laço deixa pedido criado com itens parciais e estoque debitado
        incorretamente, sem forma de detectar. Corrupção silenciosa de dado de estoque.
Recommendation: Envolver a operação em transação com `rollback` no erro, validar tudo antes de
                escrever e usar `UPDATE ... WHERE estoque >= ?` para evitar estoque negativo —
                padrão RP-07.

### 8. [HIGH] Estado Global Mutável — Conexão Singleton Thread-Unsafe (AP-09)
File: database.py:4-11, 86
Description: `db_connection` é global inicializada por efeito colateral do primeiro `get_db()`
             (database.py:7-10) com `check_same_thread=False` (linha 10); o mesmo getter também
             executa DDL (14-53) e seed (56-84).
Impact: Uma conexão compartilhada por todas as requisições, com a proteção de thread do driver
        desligada — corrida em escrita concorrente. Impossível injetar conexão de teste; o
        schema é criado como efeito colateral de um acesso de leitura.
Recommendation: Conexão por request (`flask.g`) ou pool, injetada nos models; DDL/seed em função
                de inicialização explícita chamada pelo factory ou por CLI — padrão RP-06.

### 9. [HIGH] Configuração de Desenvolvimento em Código de Aplicação (AP-11)
File: app.py:7-9, 88
Description: `DEBUG = True` (app.py:8), `CORS(app)` sem restrição de origem (linha 9) e
             `app.run(host="0.0.0.0", port=5000, debug=True)` (linha 88), com o health check
             declarando `"ambiente": "producao"` (controllers.py:286).
Impact: O debugger do Werkzeug fica ativo e acessível na rede (o baseline registrou
        `Debugger PIN: 251-794-342`), permitindo execução de código arbitrário no host. CORS
        liberado permite requisição cross-origin de qualquer domínio.
Recommendation: Debug e host vindos de variável de ambiente, com default seguro; CORS com lista
                de origens; entry point separado da criação da app (factory) — padrão RP-02.

### 10. [HIGH] Efeitos Colaterais de Integração dentro do Controller (AP-07)
File: controllers.py:208-210, 248-250
Description: Envio de e-mail, SMS e push simulado com `print` dentro do fluxo HTTP de
             `criar_pedido` (controllers.py:208-210) e notificação de mudança de status
             (248-250), com a regra "se aprovado / se cancelado" no controller.
Impact: Regra de notificação intestável sem cliente HTTP e impossível de reaproveitar; troca de
        canal (e-mail → fila) exige editar o controller. O controller assume responsabilidade
        de integração externa.
Recommendation: Extrair para `services/notification_service.py` injetado no controller, com o
                controller apenas orquestrando — padrão RP-05.

### 11. [HIGH] Roteamento no Entry Point, em Duas Convenções (AP-01)
File: app.py:11-31, 33-45, 47-57, 59-78
Description: 16 rotas registradas via `add_url_rule` (app.py:11-31) e outras 3 declaradas com
             `@app.route` e corpo inline no mesmo arquivo (33, 47, 59) — sendo que dois desses
             handlers inline contêm acesso direto ao banco (app.py:49-55, 66-76).
Impact: Não existe camada de View/Routes. Adicionar endpoint exige editar o arquivo que também
         define segredo, configuração e inicialização do servidor; a divergência de convenção
         dificulta enxergar o conjunto real de rotas.
Recommendation: Blueprints por agregado em `views/`, registrados pelo factory; nenhum handler
                inline no entry point — padrão RP-01.

### 12. [MEDIUM] N+1 Queries na Listagem de Pedidos (AP-14)
File: models.py:187-199, 219-231
Description: Para cada pedido, uma query de itens (models.py:188, 220); para cada item, uma
             query do nome do produto (192, 224). `GET /pedidos` com 50 pedidos de 4 itens
             executa 251 queries.
Impact: Latência cresce linearmente com o volume; o endpoint degrada em produção sem aviso.
Recommendation: Uma query com `LEFT JOIN` entre `pedidos`, `itens_pedido` e `produtos`,
                agrupando em memória — padrão RP-10.

### 13. [MEDIUM] Lógica Duplicada (AP-16)
File: models.py:171-201 vs models.py:203-233; controllers.py:28-54 vs 72-90
Description: `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE`
             (models.py:174 vs 206). A validação de produto está duplicada entre `criar_produto`
             (controllers.py:28-54) e `atualizar_produto` (72-90) — e já divergiu: o update
             perdeu a checagem de tamanho de nome (linhas 47-50) e de categoria válida (52-54).
Impact: Correção precisa ser aplicada em dois lugares; a divergência atual significa que o
        `PUT /produtos/<id>` aceita dados que o `POST /produtos` rejeita.
Recommendation: Uma função de listagem com filtro opcional e um único validador por recurso —
                padrão RP-11, RP-16.

### 14. [MEDIUM] Exceção Genérica sem Tratamento Centralizado (AP-15)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Description: 16 blocos `except Exception as e` devolvendo `jsonify({"erro": str(e)})` com status
             500, sem `@app.errorhandler` em nenhum ponto do projeto.
Impact: Mensagem interna vaza para o cliente (inclusive fragmento de SQL malformado, que
        ajudaria um atacante a explorar o finding 1); o stacktrace é descartado, então o erro
        real fica invisível; 16 cópias do mesmo tratamento.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`) + middleware
                `register_error_handlers`, com detalhe no log e mensagem genérica na resposta —
                padrão RP-08.

### 15. [MEDIUM] Validação de Entrada Inconsistente e Incompleta (AP-18)
File: controllers.py:28-54, 72-90, 111-121, 146-165, 188-201, 237-243
Description: Presença é checada, mas não tipo: `preco < 0` (controllers.py:43) quebra com string
             e devolve 500; `criar_usuario` (146-162) não valida formato de e-mail nem tamanho
             de senha; categorias válidas ficam em lista literal dentro do controller (linha 52);
             filtros de busca convertem para `float` sem tratar entrada inválida (118-121).
Impact: Entrada malformada resulta em 500 em vez de 400, e dado inválido chega ao banco.
Recommendation: Validador único por recurso, validando presença, tipo, formato e faixa, com
                constantes nomeadas para os valores válidos — padrão RP-11, RP-13.

### 16. [MEDIUM] `print()` como Estratégia de Log (AP-19)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86; database.py (nenhum)
Description: 17 `print` de diagnóstico, incluindo tentativa de login com o e-mail do usuário
             (controllers.py:179, 182) e "envio" de notificações (208-210). Nenhum `import
             logging` no projeto.
Impact: Sem nível, timestamp ou destino configurável; a saída de auditoria de login se perde no
        stdout e não pode ser filtrada nem retida.
Recommendation: `logging` configurado por `LOG_LEVEL`, com logger por módulo — padrão RP-12.

### 17. [MEDIUM] Boilerplate de Serialização Repetido (AP-23)
File: models.py:12-21, 31-40, 79-86, 95-102, 194-199, 304-313
Description: O mapeamento manual `row → dict` aparece 6 vezes, duas delas idênticas para
             produto (models.py:12-21 e 304-313) e duas para usuário (79-86 e 95-102).
Impact: Adicionar coluna exige editar seis blocos; foi exatamente esse padrão que propagou o
        campo `senha` para a resposta da API (finding 4).
Recommendation: Uma função de serialização por model, com lista explícita de campos públicos —
                padrão RP-16.

### 18. [LOW] Magic Numbers em Regra de Negócio (AP-20)
File: models.py:256-262, 272
Description: Faixas de desconto expressas em literais (`10000`/`0.1`, `5000`/`0.05`,
             `1000`/`0.02`) e status de pedido como string solta (`'pendente'` em models.py:150,
             lista de status válidos em controllers.py:242).
Impact: A política comercial fica escondida em comparações; mudança de faixa exige caçar
        literais.
Recommendation: Constantes nomeadas (`FAIXAS_DESCONTO`, enum de status) na camada de model —
                padrão RP-13.

### 19. [LOW] Shadowing de Builtin e Nomenclatura Inconsistente (AP-21)
File: models.py:24, 54, 65, 89; controllers.py:14, 64, 98, 136
Description: Parâmetros nomeados `id`, sombreando o builtin, em 8 funções. Mistura de idiomas
             entre camadas (`get_todos_produtos`, `health_check`) e chaves de resposta não
             padronizadas (`dados`/`sucesso`/`erro` vs `status`/`counts` em controllers.py:276).
Impact: Legibilidade e risco de erro sutil ao usar `id()` no mesmo escopo.
Recommendation: `produto_id`, `usuario_id`, `pedido_id`; padronizar idioma e envelope de
                resposta — padrão RP-13.

### 20. [LOW] Imports Não Utilizados (AP-22)
File: models.py:2, database.py:2, controllers.py:3
Description: `import sqlite3` em models.py:2 (o módulo não usa nada de sqlite3 diretamente),
             `import os` em database.py:2, e `from database import get_db` em controllers.py:3
             usado apenas pelo health check (linha 266).
Impact: Ruído que sugere dependências inexistentes entre camadas.
Recommendation: Remover imports não usados — padrão RP-16.

### 21. [LOW] Metadados de Aplicação Hardcoded na Resposta (AP-20)
File: app.py:35-45, controllers.py:285-288
Description: Versão (`"1.0.0"`), lista de endpoints e ambiente escritos à mão em dois lugares
             (app.py:36-44 e controllers.py:285-288), com valores já divergentes do estado real
             (`"ambiente": "producao"` com `debug=True`).
Impact: Documentação embutida que envelhece em silêncio e informa o cliente incorretamente.
Recommendation: Metadados vindos da configuração/manifesto — padrão RP-02, RP-13.

## Deprecated APIs

Verificação executada: (a) busca pelos símbolos deprecated de Python e Flask do catálogo
(`utcnow`, `before_first_request`, `JSONEncoder`, adaptadores implícitos de `datetime` no
`sqlite3`); (b) boot da aplicação com `python -W all` e leitura dos avisos de runtime.

| API | Arquivo:linha | Substituto | Removida em |
|---|---|---|---|
| — | — | — | — |

Nenhuma API deprecated em uso. O projeto não manipula `datetime` em Python (usa
`CURRENT_TIMESTAMP` do SQLite, database.py:23, 33, 42) e não usa hooks depreciados do Flask.
O boot com avisos habilitados não emitiu `DeprecationWarning`.

## Endpoints inventariados (baseline da Fase 3)

| Método | Rota | Handler | Observação |
|---|---|---|---|
| GET | / | app.py:33 | metadados hardcoded (finding 21) |
| GET | /health | controllers.py:264 | vaza SECRET_KEY (finding 4) |
| GET | /produtos | controllers.py:5 | — |
| GET | /produtos/busca | controllers.py:111 | SQL Injection (finding 1) |
| GET | /produtos/`<id>` | controllers.py:14 | SQL Injection (finding 1) |
| POST | /produtos | controllers.py:24 | SQL Injection, validação inconsistente |
| PUT | /produtos/`<id>` | controllers.py:64 | validação mais fraca que o POST (finding 13) |
| DELETE | /produtos/`<id>` | controllers.py:98 | sem auth |
| GET | /usuarios | controllers.py:128 | vaza senhas em texto plano (finding 4) |
| GET | /usuarios/`<id>` | controllers.py:136 | vaza senha (finding 4) |
| POST | /usuarios | controllers.py:146 | senha sem hash (finding 6) |
| POST | /login | controllers.py:167 | bypass por SQL Injection (finding 1) |
| POST | /pedidos | controllers.py:188 | sem transação (finding 7), notificação inline (finding 10) |
| GET | /pedidos | controllers.py:229 | N+1 (finding 12) |
| GET | /pedidos/usuario/`<usuario_id>` | controllers.py:222 | N+1 (finding 12) |
| PUT | /pedidos/`<pedido_id>`/status | controllers.py:237 | notificação inline (finding 10) |
| GET | /relatorios/vendas | controllers.py:257 | sem auth, magic numbers (finding 18) |
| POST | /admin/reset-db | app.py:47 | destrutivo, sem auth (finding 2) |
| POST | /admin/query | app.py:59 | SQL arbitrário, sem auth (finding 2) |

Baseline capturado: 33 chamadas cobrindo os 19 endpoints (caminhos felizes + 404 + 400 + sonda
de SQL Injection). Resultado registrado em `reports/validation-project-1.md`.

```
================================
Total: 21 findings
================================
```
