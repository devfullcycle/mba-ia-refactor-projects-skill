# ARCHITECTURE AUDIT REPORT

**Project:** code-smells-project
**Stack:** Python + Flask 3.1.1
**Files:** 4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Secrets
File: `app.py:7-8`
Description: `SECRET_KEY` hardcoded como `minha-chave-super-secreta-123` e `DEBUG=True` fixo no código.
Impact: Vazamento de chave secreta em qualquer controle de versão; debug ativo em produção.
Recommendation: Mover segredos para `config/settings.py` lendo `os.environ`, e `DEBUG` via `FLASK_DEBUG`.

### [CRITICAL] SQL Injection / Query Concatenation
File: `models.py:28,48,92,110,127,140,149,174,188,224,280,291`
Description: Queries construídas por concatenação de strings com inputs diretamente interpolados (ex: `"WHERE id = " + str(id)`).
Impact: Execução de SQL arbitrário (injeção).
Recommendation: Usar queries parametrizadas (`?` + tupla de args) em todas as operações.

### [CRITICAL] Backdoor / Unsafe Admin Query
File: `app.py:59-78`
Description: Endpoint `POST /admin/query` executa qualquer SQL arbitrário sem qualquer autenticação.
Impact: Leitura/escrita/truncagem total do banco por qualquer requester.
Recommendation: Remover o endpoint; ele não faz parte do domínio da API. Qualquer admin real deve passar por autenticação.

### [CRITICAL] Backdoor / Unsafe Admin Reset
File: `app.py:47-57`
Description: Endpoint `POST /admin/reset-db` apaga (`DELETE`) todas as tabelas sem autenticação.
Impact: Destruição total de dados da aplicação.
Recommendation: Remover; destruição de dados deve requerer autorização e não expor via HTTP público.

### [CRITICAL] God Module
File: `models.py:1-314`
Description: Arquivo único contém todas as queries, regras de negócio, cálculos de pedido e formatação de resposta para 4 domínios (produto, usuário, pedido, relatório).
Impact: Impossível testar isoladamente; qualquer mudança afeta tudo.
Recommendation: Split em `models/` por domínio (`produto_model`, `usuario_model`, `pedido_model`) + `services/` para regras.

### [HIGH] Business Logic in Controller/Route
File: `controllers.py:167-186,188-220`
Description: Regras de negócio e notificações "EMail/SMS/PUSH" via `print` presas dentro dos handlers de rota.
Impact: Dificulta testes e manutenção; efeitos colaterais (prints) acoplados ao fluxo HTTP.
Recommendation: Extrair para `services/pedido_service.py` como `processar_criacao()`.

### [HIGH] Business Logic in Model
File: `models.py:133-169`
Description: `criar_pedido()` no model calcula total, valida estoque e aplica regras de domínio indevidas para a camada de persistência.
Impact: Model deixa de ser abstração de dados; difícil reutilização.
Recommendation: Mover validação/cálculo para `services/pedido_service`; model só persiste.

### [HIGH] Global Mutable State
File: `database.py:4`
Description: Conexão de banco em variável global mutável (`db_connection = None`).
Impact: Comportamento imprevisível em concorrência.
Recommendation: Inicialização preguiçosa via getter, centralizada no módulo de banco.

### [HIGH] Deprecated / Unsafe Config (DEBUG no código)
File: `app.py:8,88`
Description: `app.config['DEBUG']=True` e `app.run(debug=True)` fixos no código.
Impact: Debug/online errors expostos; risco em produção.
Recommendation: Ler do ambiente (`FLASK_DEBUG`).

### [MEDIUM] N+1 Query
File: `models.py:139-166,188-192,220-224`
Description: Loops executam `SELECT` por item (stocks de produtos por item dentro do pedido; itens por pedido dentro de loop).
Impact: Degradação de performance à medida que o volume cresce.
Recommendation: JOIN para itens por pedido; busca única de produtos por lista de IDs.

### [MEDIUM] Lack of Input Validation
File: `models.py:122-130`, `controllers.py:146-165`
Description: Senha armazenada e comparada em texto puro; endpoints admin sem qualquer checagem de autorientação.
Impact: Credenciais expostas; acesso indevido.
Recommendation: Hash (sha256/bcrypt) da senha + leitura de env para admin.

### [MEDIUM] Implicit Configuration
File: hardcoded em `app.py`/`database.py`
Description: Porta `5000`, host `0.0.0.0`, `loja.db`, status de pedidos, categorias válidas — tudo magic no código.
Impact: Difícil mudar de ambiente (test/prod).
Recommendation: Mover para `config/settings.py` via variáveis de ambiente.

### [MEDIUM] Mixed Responsibilities
File: `models.py` (várias)
Description: O módulo de persistência também formata e manipula respostas JSON (construção de dict).
Impact: Acoplamento entre persistência e apresentação.
Recommendation: Manter models somente com acesso a dados; formato de resposta definido no controller.

### [LOW] Magic Numbers / Poor Naming
File: `controllers.py:43-50` / falta de nomes de constantes
Description: Faixas de desconto magicas `10000/5000/1000` e `0.10/0.05/0.02` no relatório; variáveis genéricas (`id`, `dados`).
Impact: Legibilidade reduzida.
Recommendation: Extrair para `config/settings.py` (`DESCONTO_FAIXAS`).

### [LOW] Duplicate Code
File: `models.py:171-233`
Description: `get_pedidos_usuario` e `get_todos_pedidos` quase idênticos (duplicação de lógica de montagem de itens).
Impact: Manutenção difícil; correções duplicadas.
Recommendation: Extrair helper `_pedido_com_itens()` reutilizável.

### [LOW] Debug Prints Leftovers
File: `controllers.py` (espalhado)
Description: `print(...)` em várias rotas para logs de debug (listando, criando, login, pedido).
Impact: Ruído; não é logging estruturado.
Recommendation: Remover ou substituir por module-level logging.

---
**Total: 16 findings** (ordenação por severidade CRITICAL → LOW)