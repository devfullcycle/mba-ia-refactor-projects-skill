```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite)
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] AP-03 Injeção em consultas (SQL Injection)
File: models.py:28, models.py:48-49, models.py:58-60, models.py:68, models.py:92 (+16 ocorrências: 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 289-299); app.py:69
Description: Todas as consultas são montadas por concatenação de strings com dados vindos da requisição (id, nome, email, senha, termo de busca `q`, categoria, status). Ex.: `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"` (login, models.py:109-111). Além disso, `/admin/query` executa SQL arbitrário recebido no corpo (app.py:62-69).
Impact: Bypass de login (`' OR '1'='1`), leitura/alteração/destruição de qualquer dado do banco por qualquer cliente.
Recommendation: Usar placeholders `?` do sqlite3 com tupla de parâmetros em todas as queries; remover execução de SQL arbitrário (playbook: PB-03).

### [CRITICAL] AP-04 Autenticação e segurança de dados quebradas (senhas)
File: models.py:109-111, models.py:126-128, models.py:83, models.py:99; database.py:75-79
Description: Senhas guardadas e comparadas em texto puro (seed `admin123`, `123456`...). `get_todos_usuarios` e `get_usuario_por_id` devolvem o campo `senha` ao cliente (GET /usuarios e /usuarios/<id>). Login não emite token/sessão.
Impact: Vazamento de todas as senhas a qualquer chamador; comprometimento total das contas em caso de acesso ao banco.
Recommendation: Hash com sal (werkzeug `generate_password_hash`/`check_password_hash`), nunca devolver senha/hash nas respostas, migrar seeds (playbook: PB-04).

### [CRITICAL] AP-04 Operações administrativas/destrutivas sem autenticação
File: app.py:47-57, app.py:59-78
Description: `POST /admin/reset-db` apaga todas as tabelas e `POST /admin/query` executa qualquer SQL, ambos sem nenhuma autenticação/autorização. CORS está totalmente aberto (app.py:9).
Impact: Qualquer pessoa com acesso à rede apaga ou exfiltra o banco inteiro.
Recommendation: Remover os endpoints ou protegê-los com autenticação de admin e habilitação explícita por configuração; restringir CORS (playbook: PB-04). Como a remoção altera o contrato, será registrado em Deviations.

### [CRITICAL] AP-02 Credenciais e segredos hardcoded
File: app.py:7, controllers.py:289
Description: `SECRET_KEY` definida como `'minh****'` diretamente no código e repetida em `health_check`.
Impact: Quem tem acesso ao repositório consegue forjar sessões/assinaturas; o segredo não pode ser rotacionado sem alterar código.
Recommendation: Ler de variável de ambiente/arquivo de configuração externo, falhar no boot se ausente, fornecer `.env.example` (playbook: PB-02).

### [CRITICAL] AP-08 Exposição de segredos e configuração insegura de produção
File: controllers.py:285-289, app.py:8, app.py:88
Description: `GET /health` devolve `secret_key` (`'minh****'`), `debug: True`, `db_path` e ambiente. A aplicação roda com `debug=True` e `host="0.0.0.0"` (console interativo Werkzeug exposto). Todos os handlers devolvem `str(e)` ao cliente (ex.: controllers.py:12, 22, 62).
Impact: Vazamento de segredo real por endpoint público; debug exposto permite execução remota de código; mensagens internas revelam estrutura do banco. Elevado a CRITICAL por expor segredo real.
Recommendation: Remover campos sensíveis do health, debug/host por configuração (default seguro), mensagens genéricas ao cliente com log interno (playbook: PB-02, PB-07).

### [CRITICAL] AP-01 God File
File: models.py:1-314
Description: Um único módulo de 314 linhas atende quatro domínios (produtos, usuários, pedidos, relatórios) e mistura acesso a dados, regra de negócio (desconto por faixa de faturamento, models.py:256-262; cálculo de total, 137-169), serialização e transação.
Impact: Impossível testar ou evoluir um domínio isoladamente; qualquer mudança afeta todo o módulo.
Recommendation: Separar por domínio em models/repositórios por entidade e mover regras para controllers/serviços (playbook: PB-01).

### [HIGH] AP-05 Lógica de negócio em Controllers/Rotas
File: controllers.py:24-62, controllers.py:188-220, controllers.py:237-255, controllers.py:264-292
Description: Controllers contêm validação de domínio e lista de categorias (52-54), orquestração de notificações simuladas por `print` (e-mail/SMS/push, 208-210), regras de status (242-250, com "Devolver estoque" apenas impresso, sem efetivar) e `health_check` que consulta o banco diretamente.
Impact: Regra de negócio acoplada à camada HTTP, não reutilizável nem testável; regra de cancelamento incompleta.
Recommendation: Mover regras para camada de serviço/controller de domínio e deixar rotas só com mapeamento e serialização (playbook: PB-05).

### [HIGH] AP-06 Estado global mutável e acoplamento sem injeção
File: database.py:4-11, models.py:1, controllers.py:3
Description: Conexão SQLite em variável global mutável `db_connection`, criada preguiçosamente, com `check_same_thread=False` e compartilhada entre requisições/threads; `get_db()` também cria schema e seed. Models e controllers importam e chamam `get_db()` diretamente.
Impact: Condições de corrida entre threads, impossível substituir o banco em testes, efeitos colaterais no primeiro acesso.
Recommendation: Conexão por requisição (ex.: `g`/teardown) ou fábrica injetada; separar init de schema/seed; composição no entry point (playbook: PB-06).

### [HIGH] AP-07 Violação de camadas
File: app.py:49-55, app.py:66-76, controllers.py:3, controllers.py:266-274, models.py:256-262
Description: Rotas em `app.py` e `health_check` em `controllers.py` usam o cursor do banco diretamente; models implementam regra de negócio (desconto) em vez de apenas acesso a dados.
Impact: Fronteiras entre rota, controller e model inexistentes; mudanças de persistência vazam para toda a aplicação.
Recommendation: Encapsular queries em models/repositórios e regras em controllers/serviços (playbook: PB-01, PB-05).

### [MEDIUM] AP-09 Consultas N+1
File: models.py:139-146, models.py:154-166, models.py:187-193, models.py:219-225
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam uma query de itens por pedido e outra de produto por item; `criar_pedido` consulta produto dentro de dois laços.
Impact: 1+N+M queries por requisição; latência cresce com o volume de pedidos.
Recommendation: Buscar itens e nomes de produto com JOIN/IN e agrupar em memória (playbook: PB-08).

### [MEDIUM] AP-10 Validação de entrada ausente ou inconsistente
File: controllers.py:43-50, controllers.py:87-90, controllers.py:118-121, controllers.py:169-171, controllers.py:195-203, controllers.py:239-240, models.py:140-144, app.py:61-62
Description: Tipos não são verificados (`preco < 0` com string gera TypeError → 500); `float(preco_min)` sem tratamento; atualização de produto não valida tamanho do nome nem categoria (divergente da criação); `login`, `atualizar_status_pedido` e `/admin/query` quebram se o corpo for nulo; itens do pedido sem validar `produto_id`/`quantidade` (KeyError, quantidade negativa); e-mail sem validação de formato nem unicidade.
Impact: Erros 500 em vez de 400, dados inconsistentes, regras divergentes entre rotas.
Recommendation: Centralizar validação de entrada por recurso, com respostas 400 consistentes (playbook: PB-09).

### [MEDIUM] AP-11 Tratamento de erros espalhado e que vaza detalhes
File: controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109 (+11 ocorrências em controllers.py); app.py:77-78
Description: Cada handler repete `try/except Exception` retornando `str(e)` com 500, sem tratador global; formatos de erro divergem (alguns com `sucesso: False`, outros apenas `erro`).
Impact: Vazamento de detalhes internos, contrato de erro inconsistente, repetição.
Recommendation: Tratador de erros global e exceções de domínio mapeadas para status, com log interno (playbook: PB-07).

### [MEDIUM] AP-12 Código duplicado
File: models.py:12-21, models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:178-199, models.py:211-231; controllers.py:28-50, controllers.py:72-90
Description: A serialização de produto (3x), usuário (2x) e pedido com itens (2x) é copiada; a validação de produto é duplicada entre criar e atualizar com divergências.
Impact: Correções precisam ser replicadas e já divergiram.
Recommendation: Extrair funções de serialização e validação únicas (playbook: PB-10).

### [LOW] AP-14 Magic numbers e strings soltas
File: models.py:257-262, models.py:150, models.py:247-253, controllers.py:52, controllers.py:242, controllers.py:47-49, app.py:88
Description: Faixas de faturamento e percentuais de desconto (10000/0.1, 5000/0.05, 1000/0.02), status de pedido (`'pendente'`, `'aprovado'`...), categorias válidas, limites de nome (2/200) e porta 5000 como literais soltos.
Impact: Regras difíceis de localizar e alterar; risco de inconsistência dos literais repetidos.
Recommendation: Extrair para constantes/configuração nomeadas (playbook: PB-12).

### [LOW] AP-15 Nomenclatura ruim
File: models.py:24, models.py:54, models.py:65, models.py:89, models.py:187-191, models.py:219-223, controllers.py:14, controllers.py:56
Description: Parâmetro `id` sombreia o builtin; `cursor2`/`cursor3` sem significado; mistura de convenções (`get_todos_produtos` vs `listar_produtos`) e `dados` genérico.
Impact: Leitura mais difícil e risco de bugs por sombreamento.
Recommendation: Renomear para nomes descritivos e padronizar convenção (playbook: PB-12).

### [LOW] AP-16 Código morto, comentado e logging inadequado
File: controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:161, controllers.py:208-210 (+7 ocorrências); app.py:56, app.py:83-86; models.py:2; database.py:2
Description: `print` usado como log (inclui e-mail do usuário em login e notificações simuladas); imports não usados (`sqlite3` em models.py, `os` em database.py).
Impact: Sem níveis/formatação de log, dados pessoais em stdout, ruído.
Recommendation: Usar o módulo `logging` e remover imports mortos (playbook: PB-12).

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
