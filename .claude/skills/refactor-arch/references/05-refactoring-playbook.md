# Fase 3 — Playbook de Refatoração

Este playbook traz **transformações concretas** (antes → depois) para os anti-patterns do catálogo,
o **loop de correção controlado** e a **validação por execução real**. O objetivo é chegar ao MVC
de `04-mvc-guidelines.md` **preservando os contratos externos** (mesmos paths, métodos, formato de
resposta e schema).

## Processo geral da Fase 3

1. Leia o relatório salvo na Fase 2 (`reports/audit-project-<N>.md`) — ele é a lista de trabalho.
2. Crie a estrutura de pastas MVC (layout conforme a stack, ver `04-mvc-guidelines.md`).
3. Mova o código para as camadas aplicando as transformações abaixo, endereçando cada finding.
4. Rode o **loop de correção** (máx. 3 iterações) com re-auditoria silenciosa.
5. **Valide** subindo a aplicação e batendo em todos os endpoints.
6. Imprima `PHASE 3: REFACTORING COMPLETE` (ver `03-report-templates.md`).

---

## Transformações (antes → depois)

### T-01 — Quebrar God Class em models + controllers por domínio (AP-01)
**Antes:** `models.py` com SQL, regra, validação e formatação de 4 domínios.
**Depois:** `models/produto_model.py`, `models/pedido_model.py`, ... (dados + regra por entidade)
e `controllers/produto_controller.py`, ... (orquestração). Cada arquivo com uma responsabilidade.

### T-02 — Extrair segredos para config via ambiente (AP-02, AP-16)
**Antes (Python):**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois:**
```python
# config/settings.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```
**Node:** trocar literais por `process.env.X` num `config/index.js`. Adicione `.env.example`.

### T-03 — Parametrizar SQL e remover SQL arbitrário (AP-03, AP-13)
**Antes:**
```python
cursor.execute(query)                     # query vinda do usuário
cursor.execute(f"SELECT * FROM produtos WHERE nome = '{nome}'")
```
**Depois:**
```python
cursor.execute("SELECT * FROM produtos WHERE nome = ?", (nome,))
```
Remova endpoints de SQL arbitrário (`/admin/query`) e proteja/remova destrutivos (`/admin/reset-db`).

### T-04 — Hashear senhas (AP-04)
**Antes:** `senha` salva/comparada em texto puro; `badCrypto`.
**Depois (Python):**
```python
from werkzeug.security import generate_password_hash, check_password_hash
hash_ = generate_password_hash(senha)              # ao criar
check_password_hash(user["senha"], senha_informada)  # ao logar
```
**Node:** `bcrypt.hash` / `bcrypt.compare`. **Nunca** retorne o hash/senha na resposta.

### T-05 — Injetar a conexão em vez de estado global (AP-05)
**Antes:** `db_connection` global mutável; `global db_connection`.
**Depois:** criar a conexão no composition root e injetá-la nos models/controllers (parâmetro ou
factory). Escopo por request quando a stack permitir. Remover `check_same_thread=False` como gambiarra.

### T-06 — Mover regra da rota para model/service; controller magro (AP-06)
**Antes:** handler da rota abre cursor, faz query, aplica regra, formata resposta.
**Depois:**
```python
# views/routes.py  → só mapeia
app.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
# controllers/produto_controller.py → orquestra
def listar():
    produtos = ProdutoModel.listar_todos()
    return jsonify(produtos), 200
# models/produto_model.py → dados + regra
class ProdutoModel:
    @staticmethod
    def listar_todos(): ...
```

### T-07 — Desaninhar callbacks / extrair repositório (AP-07)
**Antes (Node):** cadeia de `db.get(... => { db.run(... => { ... }) })` dentro do handler.
**Depois:** promisificar o acesso ao banco (`util.promisify` ou wrapper que retorna Promise),
extrair um repositório (`models`/`repositories`) e usar `async/await` no controller, com
transação explícita para operações relacionadas (checkout: matrícula + pagamento + log).

### T-08 — Eliminar N+1 com JOIN/agregação (AP-08)
**Antes:** loop sobre matrículas buscando usuário e pagamento um a um.
**Depois:** uma query com `JOIN` (ou `WHERE id IN (...)`) trazendo o conjunto de uma vez; montar a
resposta em memória. Preserve o formato final do JSON.

### T-09 — Validar entrada nas rotas (AP-09)
**Antes:** `dados = request.get_json()` usado direto.
**Depois:** validar no controller (schema `marshmallow`/`joi`/checagem explícita); retornar `400`
com mensagem clara quando faltar campo ou o tipo for inválido. Mantenha os campos do contrato.

### T-10 — Centralizar tratamento de erro em middleware (AP-12 parcial, transversal)
**Antes:** `try/except`/`if err return 500` repetido em cada handler.
**Depois:** um middleware/error handler único (`middlewares/error_handler.py` /
`middlewares/errorHandler.js`) registrado no composition root; controllers levantam/repassam erro.

### T-11 — Atomicidade e integridade (AP-12)
**Antes:** múltiplos inserts relacionados sem transação; `DELETE` deixando órfãos.
**Depois:** envolver operações relacionadas em transação (commit/rollback); ao deletar, tratar
dependências (cascata explícita) para não deixar dados órfãos.

### T-12 — Substituir APIs deprecated (AP-11)
Troque cada uso obsoleto pelo equivalente moderno detectado na Fase 1. Exemplos:
`@app.before_first_request` → inicialização no factory; `datetime.utcnow()` →
`datetime.now(timezone.utc)`; `body-parser` avulso → `express.json()`; `new Buffer()` →
`Buffer.from()`. Cite no relatório final o que foi trocado.

### T-13 — Nomear constantes e melhorar legibilidade (AP-14, AP-15)
Extrair magic numbers para constantes nomeadas (em config ou topo do módulo); renomear variáveis
crípticas (`u`, `e`, `cc`) para nomes intencionais. Não altere comportamento.

### T-14 — Eliminar duplicação de código (DRY) (AP-10)
**O que é:** o mesmo trecho (montagem de resposta, query, validação, formatação de erro) repetido
em vários handlers.
**Antes:**
```python
# em várias rotas, o mesmo bloco:
produto = cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
if produto is None:
    return jsonify({"erro": "Produto não encontrado"}), 404
```
**Depois:**
```python
# models/produto_model.py — a query fica num único lugar
class ProdutoModel:
    @staticmethod
    def buscar_por_id(id):
        return cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()

# controllers/produto_controller.py — reuso, sem repetição
def _obter_ou_404(id):
    produto = ProdutoModel.buscar_por_id(id)
    if produto is None:
        abort(404, description="Produto não encontrado")
    return produto
```
Extraia o trecho repetido para uma função/helper/model reutilizável (ou middleware, quando for
formatação de erro). Regra prática: se o mesmo bloco aparece 3+ vezes, vira função. Preserve o
comportamento e o contrato de resposta.

---

## Loop de correção controlado (máx. 3 iterações)

```
iteração = 1
enquanto iteração <= 3:
    aplicar correções pendentes (transformações acima, guiadas pelos findings)
    resultado = RE-AUDITAR silenciosamente (mesmos critérios da Fase 2)
        # NÃO imprimir os findings desta re-auditoria
    se resultado.sem_problemas_e_sem_regressao:
        sucesso = verdadeiro; sair do loop
    senão:
        pendentes = resultado.findings_restantes
        iteração += 1
```

- A re-auditoria usa **os mesmos critérios** de `02-antipattern-catalog.md` e `04-mvc-guidelines.md`.
- Ela verifica **duas** coisas: (a) os findings originais foram resolvidos e (b) a refatoração
  **não introduziu** problemas novos. Se introduziu, trate-os como pendentes na próxima iteração.
- É **silenciosa**: serve para decidir se continua; nada dela vai para o console.
- Ao sair (sucesso ou 3 iterações), siga para a validação e a impressão final.

---

## Validação por execução real (obrigatória)

A aplicação **não pode quebrar**. Prove que funciona:

1. **Instale dependências** no diretório do projeto:
   - Python: `pip install -r requirements.txt` (idealmente num venv).
   - Node: `npm install`.
2. **Suba o servidor** em background e aguarde ele ficar pronto:
   - Python/Flask: `python app.py` (ou `python src/app.py`) — porta detectada na Fase 1 (ex.: 5000).
   - Node/Express: `npm start` ou `node src/app.js` — porta detectada (ex.: 3000).
3. **Exercite todos os endpoints originais** com requisições HTTP reais (`curl` ou similar):
   - Use as rotas mapeadas na Fase 1 e, se existir, o arquivo `api.http` do projeto.
   - Confirme códigos de status esperados e formato de resposta compatível com o contrato original.
   - Cubra os métodos (GET/POST/PUT/DELETE) e ao menos um caminho feliz por recurso.
4. **Encerre o servidor** (mate o processo em background).
5. Só marque `✓ Application boots without errors` e `✓ All endpoints respond correctly` se ambos
   realmente passaram. Se algo falhar, **corrija e revalide** — não finalize quebrado.

> Dica: rode o servidor com `run_in_background`, capture o log de boot para confirmar que subiu sem
> stack trace, faça as chamadas, e então encerre o processo. Se a app usa banco in-memory, o seed
> roda no boot — valide contra os dados semeados.

---

## Checklist de conclusão da Fase 3

- [ ] Estrutura de diretórios segue MVC (layout idiomático da stack).
- [ ] Config/segredos fora do código (via ambiente).
- [ ] Models abstraem dados e regra; sem SQL em rotas/controllers.
- [ ] Views/Routes só mapeiam e delegam.
- [ ] Controllers magros orquestrando.
- [ ] Tratamento de erro centralizado (middleware).
- [ ] Entry point/composition root claro.
- [ ] Contratos externos preservados (paths, métodos, formato, schema).
- [ ] Loop de correção executado (≤ 3 iterações).
- [ ] App sobe sem erros e todos os endpoints respondem (validação real).
- [ ] Saída final impressa no formato de `03-report-templates.md`, refletindo o estado real.
