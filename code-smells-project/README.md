# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

---

## Análise Manual

### CRITICAL

#### 1. SQL Injection
- **Arquivo:** `models.py:28, 48-49, 58-60, 68, 92, 109-110, 127-128, 140, 155, 159, 163-165, 174, 187-199, 220, 279, 291-297`
- **Problema:** Todas as queries SQL usam string concatenation em vez de parâmetros preparados. Exemplo: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` e `cursor.execute("INSERT INTO ... VALUES ('" + nome + "', ...")`.
- **Impacto:** Qualquer input do usuário pode injetar SQL arbitrário no banco. Um atacante pode ler, modificar ou deletar todos os dados.
- **Severidade:** CRITICAL

#### 2. Hardcoded SECRET_KEY
- **Arquivo:** `app.py:7`
- **Problema:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — a chave secreta do Flask está hardcoded no código-fonte.
- **Impacto:** Qualquer pessoa com acesso ao código pode forjar sessões e tokens do Flask.
- **Severidade:** CRITICAL

#### 3. Hardcoded Passwords no Seed
- **Arquivo:** `database.py:76-83`
- **Problema:** Senhas de usuários seed hardcoded: `"admin123"`, `"123456"`, `"senha123"`. Senhas armazenadas em plaintext no banco.
- **Impacto:** Credenciais expostas no código-fonte, senhas fracas e sem hash.
- **Severidade:** CRITICAL

#### 4. SQL Execution Endpoint (sem autenticação)
- **Arquivo:** `app.py:59-78`
- **Problema:** Endpoint `/admin/query` aceita SQL arbitrário via body (`dados.get("sql")`) e executa diretamente no banco, sem nenhuma autenticação.
- **Impacto:** Qualquer pessoa pode executar qualquer SQL no banco — DROP TABLE, DELETE, SELECT em dados sensíveis.
- **Severidade:** CRITICAL

#### 5. Unauthenticated Admin Routes
- **Arquivo:** `app.py:47-78`
- **Problema:** `/admin/reset-db` e `/admin/query` não possuem qualquer middleware de autenticação ou autorização.
- **Impacto:** Qualquer usuário anônimo pode resetar o banco inteiro ou executar queries arbitrárias.
- **Severidade:** CRITICAL

### HIGH

#### 6. God File (models.py)
- **Arquivo:** `models.py:1-315`
- **Problema:** Arquivo único de 315 linhas contém toda a lógica de acesso ao banco para 4 domínios diferentes (produtos, usuários, pedidos, relatórios). Mistura queries SQL, serialização e regras de negócio.
- **Impacto:** Impossível testar em isolamento. Qualquer mudança em um domínio pode quebrar outro. Violação total do SRP (Single Responsibility Principle).
- **Severidade:** HIGH

#### 7. Password Exposure em API Responses
- **Arquivo:** `models.py:83-86` (get_todos_usuarios), `models.py:94-102` (get_usuario_por_id), `controllers.py:289-290` (health_check)
- **Problema:** Os endpoints de listagem/busca de usuários retornam o campo `senha`. O health check expõe `secret_key` e `debug` no response.
- **Impacto:** Senhas e secrets visíveis para qualquer consumidor da API.
- **Severidade:** HIGH

#### 8. Business Logic in Controllers
- **Arquivo:** `controllers.py:208-210` (notificações), `controllers.py:247-251` (notificações de status)
- **Problema:** Notificações (email, SMS, push) são simuladas via `print()` diretamente nos controllers. Lógica de negócio misturada com apresentação.
- **Impacto:** Impossível testar notificações, impossível trocar o mecanismo sem alterar o controller.
- **Severidade:** HIGH

### MEDIUM

#### 9. N+1 Query Problem
- **Arquivo:** `models.py:186-201` (get_pedidos_usuario), `models.py:218-231` (get_todos_pedidos)
- **Problema:** Para cada pedido, uma query busca os itens; para cada item, outra query busca o nome do produto. Com 100 pedidos de 5 itens cada = 600 queries ao invés de 1 JOIN.
- **Impacto:** Performance degrada linearmente com o volume de pedidos.
- **Severidade:** MEDIUM

#### 10. Duplicated Code
- **Arquivo:** `models.py:171-201` vs `models.py:203-233`
- **Problema:** `get_pedidos_usuario()` e `get_todos_pedidos()` são quase idênticas — só diferem no WHERE. A serialização de produtos em dicts está repetida 5+ vezes (linhas 10-21, 29-40, 78-87, 93-102, 302-313).
- **Impacto:** Manutenção difícil — mudanças precisam ser replicadas em múltiplos lugares.
- **Severidade:** MEDIUM

#### 11. Duplicated Validation Logic
- **Arquivo:** `controllers.py:28-55` vs `controllers.py:64-95`
- **Problema:** A validação de produto (nome obrigatório, preco obrigatório, estoque obrigatório, preço negativo, etc.) está duplicada entre `criar_produto` e `atualizar_produto`.
- **Impacto:** Mudança de regra de negócio precisa ser feita em 2+ lugares.
- **Severidade:** MEDIUM

### LOW

#### 12. Debug Mode Enabled
- **Arquivo:** `app.py:8`, `app.py:88`
- **Problema:** `app.config["DEBUG"] = True` e `app.run(debug=True)`.
- **Impacto:** Em produção, expõe stack traces detalhados e permite execução de código via debugger.
- **Severidade:** LOW

#### 13. Magic Numbers
- **Arquivo:** `models.py:257-262`
- **Problema:** Thresholds de desconto hardcoded: `> 10000` (10%), `> 5000` (5%), `> 1000` (2%). Sem constantes nomeadas.
- **Impacto:** Difícil entender a regra de negócio sem ler o código. Mudanças exigem caça aos números.
- **Severidade:** LOW

#### 14. print() como Logging
- **Arquivo:** `controllers.py:8, 57, 106, 161, 179, 208-210, 218, 248-250` e `database.py:56`
- **Problema:** Uso de `print()` em vez de um framework de logging estruturado. Mensagens como `"ERRO: " + str(e)` sem nível ou contexto.
- **Impacto:** Impossível filtrar logs por nível, enviar para sistema externo ou rastrear em produção.
- **Severidade:** LOW
