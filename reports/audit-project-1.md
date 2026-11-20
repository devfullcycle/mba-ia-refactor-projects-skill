================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.14 + Flask 3.1.1 (SQLite via sqlite3 raw driver)
Files:   4 analyzed | ~780 lines of code
Architecture: Pseudo-layered

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 6 | LOW: 5

## Findings

### [CRITICAL] AP-04 Unprotected administrative endpoints (arbitrary SQL + DB wipe)
File: app.py:47-57, 59-78
Description: `POST /admin/query` executa `cursor.execute(query)` com o campo `sql` vindo direto do corpo da requisição (app.py:62-69), e `POST /admin/reset-db` executa `DELETE FROM` sem `WHERE` em `itens_pedido`, `pedidos`, `produtos` e `usuarios` (app.py:51-55). Nenhuma das rotas verifica identidade ou papel (`tipo = 'admin'`).
Impact: Qualquer cliente anônimo pode ler a tabela `usuarios` (com senhas), alterar/destruir dados ou apagar o banco inteiro com uma única requisição.
Recommendation: Remover a capacidade de SQL arbitrário (ou restringir a SELECT somente-leitura) e proteger `/admin/*` com verificação de autenticação e papel admin; mover o reset para um controller/repositório transacional. (T-17)

### [CRITICAL] AP-02 SQL Injection
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Todas as queries são montadas por concatenação de strings. Dados controlados pelo cliente chegam diretamente ao SQL: login `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:109-111); `nome`/`descricao` em INSERT/UPDATE de produtos (models.py:47-50, 57-61); `nome`/`email`/`senha` em `criar_usuario` (models.py:126-129); `termo` e `categoria` da query string em `buscar_produtos` (models.py:291, 293); `usuario_id`, `produto_id` e `quantidade` do JSON (sem tipo validado) em `criar_pedido` (models.py:140-166).
Impact: `email = "' OR 1=1 --"` autentica como o primeiro usuário (Admin); `GET /produtos/busca?q=' UNION SELECT ...` exfiltra dados; nomes legítimos com apóstrofo (`D'Agua`) quebram o INSERT com HTTP 500.
Recommendation: Usar queries parametrizadas (placeholders `?`) em repositórios na camada de modelo. (T-02)

### [CRITICAL] AP-06 Sensitive data exposure (passwords and secrets in responses)
File: models.py:83, 99, controllers.py:286-289
Description: Os mapeadores de usuário incluem `"senha": row["senha"]` (models.py:83, 99), então `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha de todos os usuários. `GET /health` retorna `"secret_key": "minha-chave-****"`, `"db_path": "loja.db"` e `"debug": True` (controllers.py:286-289).
Impact: Qualquer cliente obtém as credenciais de todos os usuários (inclusive o admin) e a chave de assinatura da aplicação — violação direta de LGPD.
Recommendation: Remover `senha` dos serializers públicos e retirar dados de configuração do health check (manter apenas status/contagens). (T-10)

### [CRITICAL] AP-05 Insecure password storage (plaintext)
File: models.py:109-111, 126-129, database.py:75-83
Description: `criar_usuario` grava `senha` exatamente como recebida (models.py:126-129); o login compara texto puro no SQL `... AND senha = '" + senha + "'` (models.py:109-111); o seed insere `"admin123"`, `"123456"`, `"senha123"` em texto puro (database.py:75-83).
Impact: Um único vazamento do `loja.db` (ou do endpoint `/admin/query`) expõe todas as senhas, reutilizadas em outros serviços.
Recommendation: Armazenar hash com sal (`werkzeug.security.generate_password_hash`, já instalado com Flask) e verificar com `check_password_hash` no controller de autenticação; aplicar hash também no seed. (T-09)

### [CRITICAL] AP-01 Hardcoded secrets
File: app.py:7, controllers.py:289
Description: `app.config["SECRET_KEY"] = "minha-chave-****"` definido como literal (app.py:7) e duplicado literalmente na resposta do health check (controllers.py:289).
Impact: Qualquer pessoa com acesso ao repositório obtém o segredo; impossível rotacionar por ambiente.
Recommendation: Ler `SECRET_KEY` de variável de ambiente em um módulo `config`, com valor aleatório gerado apenas em desenvolvimento; documentar em `.env.example`. (T-01)

### [CRITICAL] AP-03 God Module (models.py)
File: models.py:1-314
Description: Um único módulo de 314 linhas atende 4 contextos não relacionados — produtos (4-70, 285-314), usuários/autenticação (72-131), pedidos (133-233, 275-283) e relatórios (235-273) — misturando acesso a dados com regras de negócio: verificação de estoque (144-145), cálculo do total (146), baixa de estoque (163-166) e faixas de desconto do faturamento (256-262). Cada função também obtém a conexão global por conta própria.
Impact: Impossível testar regras de negócio sem banco; qualquer mudança em um domínio arrisca todos os outros (viola SRP).
Recommendation: Dividir em modelos/repositórios por entidade (`produto`, `usuario`, `pedido`) e mover as regras (estoque, total, descontos) para controllers. (T-03)

### [HIGH] AP-12 Insecure configuration hardcoded for production
File: app.py:8, 9, 88, controllers.py:286-288
Description: `app.config["DEBUG"] = True` (app.py:8) e `app.run(host="0.0.0.0", port=5000, debug=True)` (app.py:88) ligam o debugger do Werkzeug em todas as interfaces; `CORS(app)` sem restrição de origem (app.py:9); o health check se declara `"ambiente": "producao"` com `"debug": True`. O login (controllers.py:167-186) não emite nenhum token — não há mecanismo real de controle de acesso.
Impact: O debugger interativo exposto em 0.0.0.0 permite execução remota de código; CORS aberto permite que qualquer site chame a API.
Recommendation: Ler DEBUG/HOST/PORT/CORS_ORIGINS de variáveis de ambiente com default seguro (debug desligado). (T-01)

### [HIGH] AP-10 Non-atomic multi-step writes / broken referential integrity
File: models.py:133-169, 65-70, app.py:51-55
Description: `criar_pedido` faz INSERT em `pedidos`, N INSERTs em `itens_pedido` e N UPDATEs de estoque sem `BEGIN/ROLLBACK` (models.py:148-168); como a conexão é global e compartilhada, uma exceção no meio deixa escritas pendentes que serão confirmadas pelo próximo `commit()` de outra requisição. A verificação de estoque é lida antes e escrita depois sem condição (`estoque = estoque - n` sem `AND estoque >= n`), permitindo venda acima do estoque sob concorrência. `deletar_produto` (models.py:65-70) apaga produtos referenciados por `itens_pedido` (sem FOREIGN KEY no schema).
Impact: Pedidos parciais/órfãos, estoque negativo e relatórios incorretos.
Recommendation: Envolver a criação do pedido em transação única com rollback em erro e baixa de estoque condicional; tratar referências antes do delete. (T-11)

### [HIGH] AP-09 Global mutable state (shared SQLite connection)
File: database.py:4-11
Description: `db_connection = None` em nível de módulo, reatribuído via `global db_connection` (database.py:8) e aberto com `sqlite3.connect(db_path, check_same_thread=False)` (database.py:10) — uma única conexão/transação compartilhada por todas as threads do servidor Flask.
Impact: Condições de corrida e mistura de transações entre requisições (o commit de uma requisição confirma escritas parciais de outra); testes não conseguem isolar o banco.
Recommendation: Conexão por requisição (`flask.g` + `teardown_appcontext`) criada a partir da configuração injetada. (T-06)

### [HIGH] AP-07 Business logic and DB access in the HTTP layer
File: controllers.py:24-62, 64-96, 188-220, 237-255, 264-292, app.py:47-78
Description: Os "controllers" são handlers HTTP (usam `request`/`jsonify`) e concentram regras: validação de produto e lista de categorias válidas (controllers.py:28-54), orquestração de pedido + notificações (188-220), transição de status + notificações (237-255), consultas SQL diretas no health check (266-274). Rotas em `app.py` executam SQL diretamente (app.py:49-55, 66-76).
Impact: As regras não podem ser reutilizadas nem testadas sem HTTP; viola SRP e o MVC.
Recommendation: Rotas finas (parse → controller → resposta) e controllers sem dependência de Flask, que orquestram modelos e serviços. (T-04)

### [HIGH] AP-08 Tight coupling / no composition root
File: app.py:3-4, 6-30, controllers.py:2-3, models.py:1
Description: `from database import get_db` importado em todas as camadas (app.py:4, controllers.py:3, models.py:1); `app = Flask(__name__)` e o registro de rotas acontecem em tempo de import (app.py:6-30), sem app factory; controllers dependem do módulo concreto `models`.
Impact: Impossível trocar o banco ou serviços em testes; toda camada depende de concretos (viola DIP).
Recommendation: App factory `create_app(config)` que monta config → DB → modelos → controllers → rotas. (T-05)

### [MEDIUM] AP-14 Missing and duplicated input validation
File: controllers.py:28-54, 72-90, 118-121, 169-170, 195-201, 239-242, models.py:139-146
Description: As validações de criação e atualização de produto são duplicadas e divergentes — a atualização não valida tamanho do nome nem categoria (controllers.py:72-90 vs 28-54). `preco`/`estoque` não têm tipo verificado (`"abc" < 0` → TypeError 500). `float(preco_min)` sem tratamento (118-121) → 500. `request.get_json().get(...)` sem checar `None` no login e no status (169-170, 239-240) → 500. Itens do pedido não são validados: `quantidade` ausente → KeyError 500 e `quantidade` negativa passa na checagem de estoque (models.py:144), gera total negativo e **aumenta** o estoque.
Impact: Erros 500 para entrada inválida e manipulação de estoque/valores por qualquer cliente.
Recommendation: Validadores únicos por entidade (tipos, faixas, quantidade inteira > 0) reutilizados em create/update, retornando 400. (T-14)

### [MEDIUM] AP-06 Raw exception text returned to clients
File: app.py:78, controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292
Description: Todos os handlers retornam `jsonify({"erro": str(e)})` com HTTP 500 (rebaixado para MEDIUM: expõe apenas o texto da exceção, ex.: mensagens do SQLite com trechos da query).
Impact: Vaza detalhes internos (estrutura de tabelas, SQL) que facilitam a exploração das injeções.
Recommendation: Handler global que registra a exceção e responde mensagem genérica. (T-10)

### [MEDIUM] AP-13 N+1 queries
File: models.py:177-200, 209-232, 139-140, 154-155, 239-254
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam uma query de itens por pedido (188, 220) e uma query de produto por item (192, 224). `criar_pedido` busca cada produto duas vezes (140 e 155). `relatorio_vendas` faz 5 queries (`COUNT`, `SUM` e 3× `COUNT ... WHERE status`) que um único `GROUP BY status` responde.
Impact: `GET /pedidos` com 100 pedidos de 3 itens executa ~401 queries; tempo cresce linearmente com os dados.
Recommendation: JOIN `itens_pedido` × `produtos` com `IN (...)` agrupando em memória; agregação única com `GROUP BY`. (T-08)

### [MEDIUM] AP-16 Inconsistent / absent error handling
File: controllers.py:10, 21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291, app.py:77, models.py:143, 145
Description: `try/except Exception` repetido em 17 handlers e nenhum `@app.errorhandler`. Formatos de erro misturados: `{"erro": ...}`, `{"erro": ..., "sucesso": False}` e `{"status": "erro", "detalhes": ...}` (controllers.py:292). O modelo sinaliza erro de negócio retornando dict `{"erro": ...}` (models.py:143, 145) que o controller testa por chave (controllers.py:205).
Impact: Clientes não podem confiar no formato de erro; falhas reais ficam escondidas.
Recommendation: Exceções de domínio (`NotFound`, `ValidationError`) e um error handler central com envelope `{"erro", "sucesso": false}`. (T-07)

### [MEDIUM] AP-15 Code duplication
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 177-200, 209-232, controllers.py:28-50, 72-90
Description: Mapeamento linha→dict de produto repetido 3 vezes e de usuário 2 vezes; a montagem de pedidos com itens é praticamente idêntica em `get_pedidos_usuario` e `get_todos_pedidos`; validações de produto copiadas entre criar/atualizar.
Impact: Regras divergem com o tempo (já divergiram na validação de update); correções precisam ser aplicadas N vezes.
Recommendation: Funções únicas de serialização e consulta de pedidos parametrizada; constantes compartilhadas. (T-15)

### [MEDIUM] AP-18 Side effects and infrastructure in the wrong place
File: controllers.py:208-210, 247-250, database.py:14-84
Description: Notificações (e-mail, SMS, push) simuladas com `print` dentro dos handlers (controllers.py:208-210, 247-250); a mensagem "cancelado. Devolver estoque." é impressa mas o estoque não é devolvido. `get_db()` mistura conexão, criação de schema e seed (database.py:14-84).
Impact: Efeitos colaterais ocultos, acoplamento do domínio à infraestrutura, difícil de testar.
Recommendation: Serviço de notificação injetado pela composition root; separar schema/seed da obtenção de conexão. (T-05)

### [LOW] AP-22 print used as logging
File: app.py:56, 83-86, controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208, 209, 210, 219, 248, 250
Description: 19 chamadas `print(...)` para mensagens operacionais e erros; algumas registram e-mails de usuários (controllers.py:161, 179, 182).
Impact: Sem níveis nem estrutura; impossível silenciar; vaza PII nos logs.
Recommendation: Usar `logging` com logger por módulo. (T-16)

### [LOW] AP-19 Magic numbers and strings
File: models.py:150, 247-262, controllers.py:52, 242, 247, 249, 285, app.py:36, 85, 88
Description: Faixas de desconto `> 10000`, `* 0.1`, `> 5000`, `* 0.05`, `> 1000`, `* 0.02` (models.py:257-262); status `'pendente'`, `'aprovado'`, `'cancelado'` repetidos em models e controllers; lista de categorias inline (controllers.py:52); versão `"1.0.0"` duplicada; porta `5000` literal.
Impact: Significado oculto; mudar uma regra exige caçar literais.
Recommendation: Constantes nomeadas em um módulo de domínio/config. (T-15)

### [LOW] AP-21 Unused imports and dead code
File: database.py:2, models.py:2, controllers.py:268
Description: `import os` (database.py:2) e `import sqlite3` (models.py:2) nunca usados; `cursor.execute("SELECT 1")` cujo resultado é descartado (controllers.py:268).
Impact: Ruído e dependências enganosas.
Recommendation: Remover. (T-16)

### [LOW] AP-20 Poor naming
File: controllers.py:14, 56, 64, 98, 136, 160, models.py:24, 187-193, 219-225
Description: Parâmetro/variável `id` sombreia o builtin; `cursor2`, `cursor3`, `prod`, `e` sem significado; `controllers.py` na verdade contém a camada HTTP (views).
Impact: Legibilidade; nomes enganosos escondem a responsabilidade real dos módulos.
Recommendation: Renomear internamente mantendo os nomes públicos dos campos. (T-16)

### [LOW] AP-23 Verbose / non-idiomatic code
File: controllers.py:200, models.py:63, 70, 283, 146
Description: `if not itens or len(itens) == 0` (redundante); funções que sempre `return True` sem uso do retorno (models.py:63, 70, 283); `total = total + ...` em vez de `sum(...)`.
Impact: Legibilidade.
Recommendation: Simplificar expressões e remover retornos sem significado. (T-16)

## Deprecated APIs
No deprecated API usage detected for Python 3.14 + Flask 3.1.1 + sqlite3 (confirmed with `python -W default -c "import app"`: no warnings).

## Endpoint contract (to preserve in Phase 3)
| Method | Path | Handler |
|---|---|---|
| GET | / | app.py:33 |
| GET | /produtos | controllers.py:5 |
| GET | /produtos/busca | controllers.py:111 |
| GET | /produtos/<int:id> | controllers.py:14 |
| POST | /produtos | controllers.py:24 |
| PUT | /produtos/<int:id> | controllers.py:64 |
| DELETE | /produtos/<int:id> | controllers.py:98 |
| GET | /usuarios | controllers.py:128 |
| GET | /usuarios/<int:id> | controllers.py:136 |
| POST | /usuarios | controllers.py:146 |
| POST | /login | controllers.py:167 |
| POST | /pedidos | controllers.py:188 |
| GET | /pedidos | controllers.py:229 |
| GET | /pedidos/usuario/<int:usuario_id> | controllers.py:222 |
| PUT | /pedidos/<int:pedido_id>/status | controllers.py:237 |
| GET | /relatorios/vendas | controllers.py:257 |
| GET | /health | controllers.py:264 |
| POST | /admin/reset-db | app.py:48 |
| POST | /admin/query | app.py:60 |

================================
Total: 22 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
