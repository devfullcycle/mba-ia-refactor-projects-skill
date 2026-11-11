# 📑 Relatório de Auditoria Arquitetural — `code-smells-project` (Reauditoria pós-refatoração MVC)

**Data da Auditoria:** `2026-11-09`  
**Stack Detectada:** `Python 3` / `Flask 3.1.1 (+ flask-cors 5.0.1, python-dotenv 1.0.1)`  
**Domínio da Aplicação:** `E-commerce (produtos, usuários, pedidos, relatórios de vendas)`  

> Esta é uma **reauditoria** da versão já refatorada para MVC (commit `dac8a56`). A auditoria original da versão legada continua em `reports/audit-project-1.md`.
> Os 15 achados originais (God Files, SQL Injection, segredo exposto no `/health`, N+1, senhas em texto plano etc.) foram **corrigidos**. Os achados abaixo são **residuais** ou **novos**.

---

## 📊 1. Resumo Executivo por Severidade

| Severidade | Quantidade Identificada |
|---|---|
| 🚨 **CRITICAL** | `2` |
| ⚠️ **HIGH** | `1` |
| ⚡ **MEDIUM** | `4` |
| 🔵 **LOW** | `5` |
| **TOTAL** | **`12`** |

> **APIs Deprecated:** nenhuma encontrada (`@app.before_first_request` e `json.loads(request.data)` ausentes; usa `request.get_json(silent=True)` e `with app.app_context()`).
> **Itens do catálogo já resolvidos:** God File (#3), SQL Injection por concatenação (#2), Bypass de camadas em rotas (#4), N+1 (#6), exceções vazando stacktrace (#7), `print()` disperso (#9). Callback Hell (#5) não se aplica (Python).

---

## 🔍 2. Detalhamento dos Achados

### Achado #1: Ausência de Autenticação/Autorização nos endpoints de negócio
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `src/routes/produto_routes.py (Linhas 29 a 44)`, `src/routes/pedido_routes.py (Linhas 14 a 27)`, `src/routes/usuario_routes.py (Linhas 8 a 15)`, `src/routes/relatorio_routes.py (Linha 8)`, `src/controllers/usuario_controller.py (Linhas 40 a 53)`
- **Descrição do Problema:** `POST /login` apenas valida a senha e devolve os dados do usuário — não emite token nem sessão. Nenhuma rota de negócio exige identidade: qualquer cliente anônimo pode criar, editar e excluir produtos, alterar o status de qualquer pedido, listar todos os pedidos, ler o relatório de faturamento e listar todos os usuários (com e-mails). O campo `tipo = 'admin'` não é usado em nenhum lugar.
- **Recomendação de Refatoração:** Emitir token assinado (ex.: `itsdangerous`/JWT com `SECRET_KEY`) no login; criar middleware `login_required` e `role_required("admin")` em `src/middlewares/auth.py`; aplicar `admin` em escrita de produtos, status de pedidos, relatórios e listagem de usuários; restringir `/pedidos/usuario/<id>` ao próprio usuário.

### Achado #2: Hardcoded Secrets — credenciais padrão do seed
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `src/config/settings.py (Linhas 21, 30 e 31)`, `src/config/seed.py (Linhas 27 a 31)`, `.env.example (Linha 11)`
- **Descrição do Problema:** `SEED_DB` vale `true` por padrão e `SEED_ADMIN_PASSWORD` tem padrão `admin123`; os usuários de exemplo têm senhas fixas `123456` e `senha123` no código. Como `APP_ENV` padrão é `producao`, um boot sem `.env` em produção cria `admin@loja.com / admin123` com login válido. O impacto hoje é atenuado pelo Achado #1 (o papel admin não concede nada), mas passa a ser crítico assim que a autorização for implementada.
- **Recomendação de Refatoração:** `SEED_DB` padrão `false`; recusar seed quando `APP_ENV=producao`; exigir `SEED_ADMIN_PASSWORD` via ambiente sem default (ou gerar senha aleatória e registrá-la no log apenas em desenvolvimento); remover senhas literais dos clientes de exemplo.

### Achado #3: Endpoint de execução de SQL arbitrário (`/admin/query`)
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `src/controllers/sistema_controller.py (Linhas 46 a 56)`, `src/models/sistema_model.py (Linhas 22 a 28)`, `src/routes/sistema_routes.py (Linhas 26 a 30)`
- **Descrição do Problema:** O endpoint aceita SQL livre do cliente. As mitigações atuais (token `X-Admin-Token`, conexão SQLite `mode=ro`, filtro `startswith("SELECT")`) impedem escrita, mas quem possui o token pode ler o banco inteiro, inclusive `usuarios.senha` (hashes). É uma injeção de SQL "por design" e o filtro por prefixo é frágil.
- **Recomendação de Refatoração:** Remover o endpoint (preferível) ou substituí-lo por consultas pré-definidas no Model; no mínimo, aplicar `sqlite3` authorizer (`set_authorizer`) negando leitura de `usuarios.senha` e restringir a `APP_ENV != producao`.

### Achado #4: `usuario_id` do pedido sem validação (integridade / IDOR)
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/controllers/pedido_controller.py (Linhas 30 a 33)`, `src/routes/pedido_routes.py (Linhas 19 a 21)`
- **Descrição do Problema:** `criar_pedido` só verifica se `usuario_id` é truthy: aceita string (`"abc"`), inteiro de usuário inexistente, etc., gerando pedidos órfãos. O id vem do corpo da requisição em vez da identidade autenticada, então qualquer um cria pedidos em nome de outro usuário.
- **Recomendação de Refatoração:** Validar tipo inteiro e existência via `usuario_model.buscar_por_id`; após o Achado #1, derivar o `usuario_id` do token.

### Achado #5: Schema sem restrições de integridade / e-mail duplicado
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/config/database.py (Linhas 6 a 47)`, `src/controllers/usuario_controller.py (Linhas 25 a 37)`, `src/config/seed.py (Linhas 20 a 22)`
- **Descrição do Problema:** Nenhuma tabela tem `UNIQUE`, `FOREIGN KEY`, `NOT NULL` ou `CHECK`. `POST /usuarios` aceita e-mail já cadastrado e `autenticar` retorna o primeiro registro encontrado. `seed_if_empty` decide pelo número de **produtos**: se todos os produtos forem excluídos via API, o próximo boot recria os usuários de seed duplicados.
- **Recomendação de Refatoração:** Adicionar `UNIQUE(email)`, FKs (`PRAGMA foreign_keys = ON`) e `NOT NULL`/`CHECK (preco >= 0, estoque >= 0)` com migração; verificar e-mail existente no controller (retornar 409); tornar o seed idempotente por tabela/e-mail.

### Achado #6: Regras de domínio incompletas no ciclo de vida do pedido
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/controllers/pedido_controller.py (Linhas 67 a 75)`, `src/services/notificacao_service.py (Linhas 14 e 15)`, `src/models/pedido_model.py (Linha 100)`
- **Descrição do Problema:** Qualquer transição de status é permitida (ex.: `cancelado → aprovado`, `entregue → pendente`). Cancelar um pedido **não devolve o estoque**, embora a notificação diga "Devolver estoque". O relatório soma o `total` de pedidos cancelados no faturamento bruto e no desconto. O campo `produtos.ativo` existe mas é ignorado na listagem/busca.
- **Recomendação de Refatoração:** Máquina de estados (`TRANSICOES_VALIDAS`) no controller; no Model, cancelar com devolução de estoque na mesma transação; excluir cancelados do faturamento; filtrar `ativo = 1` nas consultas públicas.

### Achado #7: Duplicação de código
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `src/routes/*.py` (envelope `jsonify({"dados": ..., "sucesso": True})` repetido em 14 handlers), `src/models/produto_model.py (Linhas 6 e 7)` / `src/models/usuario_model.py (Linhas 10 e 11)`, `src/controllers/pedido_controller.py (Linhas 9 e 10)` / `src/controllers/produto_controller.py (Linhas 14 e 15)`
- **Descrição do Problema:** Envelope de resposta, conversão `row → dict` e checagens de tipo (`_is_inteiro`, `_is_numero`) reimplementados em vários módulos; mudanças de contrato exigem editar todos.
- **Recomendação de Refatoração:** Criar `src/utils/responses.py` (`sucesso(dados, status=200, mensagem=None)`), `src/utils/validators.py` e um helper `row_to_dict(row, campos)` compartilhado pelos Models.

### Achado #8: Vazamento de infraestrutura para o Controller
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/controllers/sistema_controller.py (Linhas 2, 4 e 52 a 56)`
- **Descrição do Problema:** O controller importa `sqlite3` e captura `sqlite3.Error`, acoplando a regra de negócio ao driver do banco; também lê `current_app.config` diretamente.
- **Recomendação de Refatoração:** O Model deve traduzir `sqlite3.Error` para uma exceção de domínio (ex.: `ConsultaInvalidaError`); configurações injetadas por parâmetro.

### Achado #9: Magic strings de status espalhadas
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/controllers/pedido_controller.py (Linha 6)`, `src/models/pedido_model.py (Linhas 19 e 101 a 103)`, `src/services/notificacao_service.py (Linhas 12 e 14)`
- **Descrição do Problema:** Os literais `'pendente'`, `'aprovado'`, `'cancelado'` são repetidos em controller, SQL e service; um erro de digitação passa despercebido.
- **Recomendação de Refatoração:** `enum StatusPedido(str, Enum)` em `src/models/` usado por todas as camadas.

### Achado #10: CORS liberado para qualquer origem
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/app.py (Linha 20)`
- **Descrição do Problema:** `CORS(app)` sem `origins` aceita qualquer domínio; combinado com o Achado #1, qualquer site pode operar a API pelo navegador da vítima.
- **Recomendação de Refatoração:** Variável `CORS_ORIGINS` em `settings.py` e `CORS(app, origins=Config.CORS_ORIGINS)`.

### Achado #11: `DB_PATH` relativo ao diretório de execução
- **Severidade:** `LOW`
- **Arquivo / Localização:** `src/config/settings.py (Linha 29)`
- **Descrição do Problema:** `loja.db` é resolvido a partir do CWD; executar a app de outro diretório cria silenciosamente um banco novo e vazio.
- **Recomendação de Refatoração:** Resolver relativo à raiz do projeto (`Path(__file__).resolve().parents[2] / "loja.db"`) quando o caminho não for absoluto.

### Achado #12: Ausência de testes automatizados
- **Severidade:** `LOW`
- **Arquivo / Localização:** `code-smells-project/` (sem diretório `tests/`)
- **Descrição do Problema:** A validação da refatoração foi manual (chamadas HTTP). Não há regressão automatizada para contrato, validações e regras de estoque.
- **Recomendação de Refatoração:** `pytest` + `app.test_client()` usando `create_app` com `DB_PATH` temporário; cobrir controllers e rotas principais.

---

## 🏗️ 3. Plano de Reestruturação para MVC

1. **Camada Model:** Adicionar constraints (`UNIQUE email`, FKs, `CHECK`) com migração; `StatusPedido` enum; `pedido_model.cancelar()` com devolução de estoque transacional; filtro `ativo = 1`; traduzir `sqlite3.Error` para exceções de domínio; helper `row_to_dict` compartilhado.
2. **Camada Controller:** Máquina de estados de pedido; validação de `usuario_id` (tipo + existência); e-mail único (409); faturamento sem cancelados; remover dependência de `sqlite3`/`current_app` em `sistema_controller`.
3. **Camada Routes / Views:** Middlewares `login_required` / `role_required` aplicados por Blueprint; helper de resposta padronizada; remover ou restringir `/admin/query`.
4. **Configurações:** `SEED_DB=false` por padrão e bloqueio de seed em produção; sem senha padrão de admin; `CORS_ORIGINS`; `DB_PATH` resolvido a partir da raiz do projeto; adicionar suíte `pytest`.
