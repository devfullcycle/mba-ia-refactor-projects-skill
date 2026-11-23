# Relatório de Auditoria Arquitetural — code-smells-project

================================
ARCHITECTURE AUDIT REPORT (INITIAL)
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] SQL Injection & Arbitrary Query Execution
File: app.py:59-78
Description: A rota `/admin/query` recebe uma string SQL arbitrária no corpo da requisição JSON e a executa diretamente no banco de dados via `cursor.execute(query)` sem validação ou sanitização. Além disso, múltiplas funções em `models.py` (linhas 28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299) constroem queries SQL através de interpolação e concatenação direta de strings.
Impact: Risco catastrófico de segurança; qualquer usuário ou invasor pode executar queries arbitrárias (DROP TABLE, exfiltração total de dados, alteração de saldos/estoque) ou contornar a autenticação de login injetando payload SQL.
Recommendation: Remover ou proteger restritamente a rota de execução de queries arbitrárias. Substituir todas as concatenações SQL por consultas parametrizadas usando placeholders (`?`) com passagem de tuplas de argumentos, ou adotar um ORM.

### [CRITICAL] Exposed Hardcoded Sensitive Credentials & Open Admin Endpoints
File: app.py:7-8
Description: A chave de sessão `SECRET_KEY` está hardcoded no arquivo de inicialização da aplicação (`"minha-chave-super-secreta-123"`), e também é exposta publicamente no retorno JSON do endpoint de health check (`controllers.py:289`). Adicionalmente, o endpoint `/admin/reset-db` (`app.py:47-57`) permite que qualquer requisição POST não autenticada apague todas as tabelas e dados da loja.
Impact: Comprometimento da assinatura de sessões/tokens e exposição de segredos em logs e rotas públicas; risco de negação de serviço e perda total de dados de produção devido a endpoint administrativo desprotegido.
Recommendation: Extrair todas as credenciais e configurações sensíveis para variáveis de ambiente via módulo desacoplado (`config/settings.py`). Remover dados sensíveis do retorno da rota `/health` e proteger ou eliminar endpoints administrativos destrutivos.

### [CRITICAL] Monolithic God File / Single Responsibility Violation
File: models.py:1-314
Description: O arquivo `models.py` funciona como um "God Module" com mais de 300 linhas, concentrando simultaneamente conexões com banco de dados, DDL, queries raw SQL, regras de negócio para 4 entidades distintas (Produtos, Usuários, Pedidos, Relatórios) e regras financeiras de cálculo de descontos. De forma análoga, `controllers.py:1-292` agrega todas as rotas e regras de fluxo de todos os recursos da aplicação em um único arquivo plano.
Impact: Violação frontal do Single Responsibility Principle (SRP); acoplamento extremo entre domínios que impede manutenibilidade, testes de unidade isolados e colaboração concorrente no código.
Recommendation: Decompor o monólito em camadas MVC limpas, separando entidades em módulos de modelos dedicados (`models/produto.py`, `models/usuario.py`, `models/pedido.py`), orquestradores em controllers por recurso (`controllers/produto_controller.py`, etc.) e rotas centralizadas em blueprints/views.

### [HIGH] Direct Database Operations in Controllers
File: controllers.py:266-275
Description: A função `health_check()` dentro do controlador obtém diretamente a conexão do banco via `get_db()`, instancia cursores e executa queries SQL (`SELECT 1`, `SELECT COUNT(*) FROM produtos`, etc.), em vez de delegar para a camada de persistência. A rota `reset_database` em `app.py:49-55` também executa operações diretas de banco de dados.
Impact: Acoplamento indevido entre a camada de transporte/controle HTTP e a camada de persistência, violando o isolamento de camadas do MVC e impedindo o reaproveitamento de regras de acesso a dados.
Recommendation: Mover todas as operações de banco e consultas de contagem para métodos utilitários na camada de Models ou serviços de infraestrutura, mantendo o controller restrito à orquestração de resposta HTTP.

### [HIGH] Broken Cryptography & Plaintext Password Exposure
File: models.py:72-103
Description: As senhas de usuários são salvas e verificadas em texto plano (`models.py:109-111, 126-129`), e as funções `get_todos_usuarios()` e `get_usuario_por_id()` retornam o campo sensível `"senha"` diretamente na estrutura serializada enviada aos clientes da API.
Impact: Exposição direta de credenciais de usuários e administradores em endpoints de consulta pública da API; ausência de qualquer proteção criptográfica em caso de vazamento do banco SQLite.
Recommendation: Implementar algoritmo seguro de hashing com salt (ex: `werkzeug.security.generate_password_hash` / `check_password_hash` ou `bcrypt`). Excluir obrigatoriamente o campo de senha do payload de serialização/retorno da API.

### [HIGH] Uncontrolled Mutable Global State
File: database.py:4-10
Description: A conexão com o banco SQLite é mantida em uma variável global mutável compartilhada (`db_connection = None` e declaração `global db_connection`), inicializada com `check_same_thread=False`.
Impact: Condições de corrida (race conditions) em servidores WSGI multi-thread/multi-processo (como Gunicorn ou uWSGI), inconsistência transacional e potenciais vazamentos de memória ou conexões corrompidas entre requisições concorrentes.
Recommendation: Encapsular a gestão da conexão por contexto de requisição (utilizando o objeto `g` do Flask ou um gerenciador de contexto `with get_db():`) garantindo abertura e encerramento seguros a cada ciclo de vida de requisição HTTP.

### [HIGH] Unsafe Deletion & Broken Referential Integrity
File: models.py:65-70
Description: A exclusão de produtos (`deletar_produto`) executa um `DELETE FROM produtos WHERE id = ...` sem verificar previamente se existem registros vinculados na tabela `itens_pedido` e sem suporte a transações ou tratamento de integridade referencial. Além disso, as chaves estrangeiras não estão ativadas no SQLite.
Impact: Registros órfãos em tabelas associadas (`itens_pedido`), corrupção da integridade relacional do banco de dados e erros inesperados (`KeyError` ou dados inconsistentes) em relatórios de vendas e histórico de pedidos.
Recommendation: Habilitar integridade referencial com `PRAGMA foreign_keys = ON`, implementar validação prévia de vínculos antes da exclusão (ou soft-delete com flag `ativo = 0`) e encapsular operações em transações atômicas.

### [MEDIUM] N+1 Query Problem & Nested Queries in Loops
File: models.py:171-233
Description: Tanto em `get_pedidos_usuario` quanto em `get_todos_pedidos`, o código busca a lista de pedidos e, para cada pedido iterado em um loop, executa uma nova consulta para obter itens (`SELECT * FROM itens_pedido WHERE pedido_id = ...`), e dentro de outro loop aninhado executa mais uma consulta para obter o nome do produto (`SELECT nome FROM produtos WHERE id = ...`).
Impact: Explosão na quantidade de requisições de I/O ao banco de dados (1 + N + M queries), causando degradação exponencial de latência e consumo desnecessário de recursos à medida que o volume de pedidos cresce.
Recommendation: Reescrever a consulta utilizando `JOIN` (`pedidos LEFT JOIN itens_pedido ON ... LEFT JOIN produtos ON ...`) para recuperar todos os pedidos e seus respectivos itens em uma única viagem ao banco de dados.

### [MEDIUM] Heavy Health Check & Unnecessary Table Counts
File: controllers.py:266-275
Description: A rota `/health` executava contagens completas em lote (`SELECT COUNT(*) FROM produtos`, `usuarios`, `pedidos`) a cada requisição HTTP de verificação de integridade da aplicação.
Impact: Endpoints de health check são frequentemente consultados por orquestradores (Kubernetes, balanceadores de carga, probes de monitoramento) em intervalos de poucos segundos. Realizar leituras contínuas de contagem consome I/O, conexões e gera risco de degradação e cascading failures sob carga alta.
Recommendation: O health check deve realizar exclusivamente a validação atômica de conectividade com o banco (`SELECT 1;`), retornando HTTP 200 quando saudável ou 503 quando indisponível. Métricas analíticas ou contagens totais devem ser movidas para endpoints específicos de telemetria/dashboards (`/metrics`).

### [MEDIUM] High Cyclomatic Complexity & Deeply Nested Business Logic
File: controllers.py:24-63
Description: O método `criar_produto` (e análogo em `models.py:133-169` para `criar_pedido`) acumula múltiplas verificações manuais de campos nulos, ranges numéricos, comprimentos de string e checagem de listas literais em cascata, combinando validação de entrada, persistência e regra de negócio.
Impact: Dificuldade de compreensão e manutenção do código, elevada probabilidade de regressão e ausência de padronização nas validações dos contratos de entrada da API.
Recommendation: Adotar Guard Clauses com retorno antecipado, criar validadores de entrada dedicados ou schemas estruturados, e mover regras de cálculo e reserva de estoque para a camada de serviço/modelo.

### [MEDIUM] Inconsistent Error Handling & Console-only Logging
File: controllers.py:10-12
Description: Todas as funções do controller utilizam blocos genéricos `except Exception as e:` que capturam indiscriminadamente qualquer exceção, imprimem no console via `print("ERRO: " + str(e))` e retornam a mensagem crua da exceção para o cliente HTTP (`return jsonify({"erro": str(e)}), 500`).
Impact: Ausência de logging estruturado com rastreabilidade (traceback), exposição de detalhes internos de implementação e mensagens de infraestrutura para usuários externos, além de mascarar a raiz dos erros.
Recommendation: Implementar logging padronizado através do módulo `logging`, criar classes de erro específicas para regras de negócio e centralizar o tratamento de erros em um middleware/error handler global (`@app.errorhandler`).

### [LOW] Missing Explicit HTTP Methods & Inconsistent Routing
File: app.py:32-33
Description: A rota `@app.route("/")` é declarada sem especificar o parâmetro `methods=["GET"]`. Adicionalmente, o projeto mescla duas convenções diferentes de registro de rotas no mesmo arquivo: `app.add_url_rule` (linhas 11-30) e `@app.route` (linhas 32, 47, 59).
Impact: Ambiguidade no contrato da API e inconsistência de design no ponto de entrada, prejudicando a legibilidade e a padronização do código.
Recommendation: Padronizar o registro de rotas utilizando Blueprints com anotações explícitas de métodos HTTP (`methods=["GET"]`, etc.).

### [LOW] Magic Numbers & Ad-Hoc Domain Literals
File: controllers.py:52-54
Description: Valores fixos e categorias são declarados como listas literais dispersas no código (ex.: `categorias_validas = [...]` em `controllers.py:52`, status válidos em `controllers.py:242` e regras de desconto com números mágicos `10000`, `5000`, `0.1` em `models.py:256-263`).
Impact: Fragilidade na manutenção das regras de negócio; adicionar uma nova categoria ou alterar percentuais de desconto exige buscar literais soltos em múltiplos pontos do código.
Recommendation: Centralizar listas de domínio, enums e constantes de negócio em arquivos de configuração ou constantes de modelo.

### [LOW] Dead Code & Unused Imports
File: database.py:2
Description: O módulo `import os` é importado no topo de `database.py` mas nunca é utilizado no restante do arquivo. De modo similar, `import sqlite3` em `models.py:2` é redundante, pois o arquivo utiliza apenas o wrapper `get_db()`.
Impact: Poluição do namespace, distração cognitiva para desenvolvedores e acoplamento desnecessário.
Recommendation: Remover todos os imports não referenciados e higienizar os módulos.

================================
Total: 14 findings
================================

---

# Re-Auditoria Pós-Refatoração (Validação Fase 2)

================================
ARCHITECTURE AUDIT REPORT (POST-REFACTOR)
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1 (MVC Architecture)
Files:   26 analyzed | ~900 lines of code

## Summary
CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 0

## Findings Status & Verification

1. [CRITICAL] SQL Injection & Arbitrary Query Execution (SEC-001)
   Status: RESOLVIDO
   Evidência: Consultas 100% parametrizadas com placeholders `?` em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`. Endpoint `/admin/query` desativado com HTTP 403 Forbidden em `views/system_routes.py`.

2. [CRITICAL] Exposed Hardcoded Sensitive Credentials & Open Admin Endpoints (SEC-002)
   Status: RESOLVIDO
   Evidência: Credenciais extraídas para `config/settings.py` via `os.getenv()`. Rota `/health` sanitizada sem expor `secret_key` ou caminhos internos.

3. [CRITICAL] Monolithic God File / Single Responsibility Violation (ARCH-001)
   Status: RESOLVIDO
   Evidência: Monólito decomposto na estrutura MVC completa (`config/`, `models/`, `controllers/`, `views/`, `middlewares/`).

4. [HIGH] Direct Database Operations in Controllers (ARCH-002)
   Status: RESOLVIDO
   Evidência: Controllers apenas orquestram chamadas e invocam a camada Model. Nenhuma query SQL direta existe em controllers.

5. [HIGH] Broken Cryptography & Plaintext Password Exposure (SEC-003)
   Status: RESOLVIDO
   Evidência: Hashing seguro com salt via `werkzeug.security` em `models/usuario_model.py`. O campo `senha` foi removido de todos os retornos de serialização de usuários.

6. [HIGH] Uncontrolled Mutable Global State (ARCH-003)
   Status: RESOLVIDO
   Evidência: Removida a conexão global `db_connection`. Gerenciamento de conexão agora atrelado ao ciclo de vida da requisição via `g.db` com limpeza automática em `teardown_appcontext`.

7. [HIGH] Unsafe Deletion & Broken Referential Integrity (DATA-001)
   Status: RESOLVIDO
   Evidência: `PRAGMA foreign_keys = ON` ativado. `ON DELETE CASCADE` implementado nas tabelas relacionais. Soft-delete seguro para produtos com itens em pedidos históricos.

8. [MEDIUM] N+1 Query Problem & Nested Queries in Loops (PERF-001)
   Status: RESOLVIDO
   Evidência: `PedidoModel.listar_todos()` e `PedidoModel.listar_por_usuario()` utilizam `LEFT JOIN` único consolidando pedidos, itens e produtos em uma única query.

9. [MEDIUM] High Cyclomatic Complexity & Deeply Nested Business Logic (CODE-001)
   Status: RESOLVIDO
   Evidência: Controllers refatorados com Guard Clauses lineares e validações antecipadas.

10. [MEDIUM] Inconsistent Error Handling & Console-only Logging (CODE-002)
    Status: RESOLVIDO
    Evidência: Tratamento global centralizado em `middlewares/error_handler.py` com `logging.exception` estruturado.

11. [LOW] Missing Explicit HTTP Methods & Inconsistent Routing (ARCH-004)
    Status: RESOLVIDO
    Evidência: Todas as rotas declaradas via Blueprints em `views/` com especificação explícita do verbo HTTP (`methods=["GET"]`, etc.).

12. [LOW] Magic Numbers & Ad-Hoc Domain Literals (CODE-004)
    Status: RESOLVIDO
    Evidência: Categorias válidas, status de pedidos e faixas de desconto centralizadas em `config/settings.py`.

13. [LOW] Dead Code & Unused Imports (CODE-003)
    Status: RESOLVIDO
    Evidência: Imports não utilizados removidos de todos os módulos.

14. [MEDIUM] Heavy Health Check & Unnecessary Table Counts (PERF-002)
    Status: RESOLVIDO
    Evidência: `HealthController.health_check()` em `controllers/health_controller.py` refatorado para utilizar `check_connection()` de `models/database.py`, executando exclusivamente a validação atômica `SELECT 1` e retornando HTTP 200 (conectado) ou 503 (degradado), sem consultas de contagem ou sobrecarga nas tabelas.

================================
Total: 0 remaining findings
================================
