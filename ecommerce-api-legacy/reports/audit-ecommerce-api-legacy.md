# Audit Report — ecommerce-api-legacy

> Gerado pela skill `refactor-arch` (Fase 2 — Auditoria).
> Data: 2026-11-05 | Atualizado: 2026-11-05 (Etapa 7 — revalidação com gate de CRITICAL/HIGH)
> Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/ecommerce-api-legacy`
> Baseado na análise de: `reports/analysis-ecommerce-api-legacy.md`
> Reexecução da Etapa 7: os achados abaixo são os da auditoria original e servem de critério de aceite para a validação. Os critérios objetivos de fechamento de CRITICAL/HIGH foram adicionados na seção 2.1.

## 1. Resumo

| Métrica | Valor |
|---|---|
| Arquivos auditados | 3 arquivos de código, ~180 LOC |
| Total de achados | 13 |
| CRITICAL | 2 |
| HIGH | 4 |
| MEDIUM | 4 |
| LOW | 3 |

## 2. Achados detalhados

---

### [CRITICAL] SEC-02 — Credenciais hardcoded

**Onde:** `src/utils.js:2-5`

**Evidência:**
```javascript
// src/utils.js:1-7
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123", 
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

**Impacto:** Usuário e senha do banco, chave live do gateway de pagamento e usuário SMTP estão literais no repositório. Qualquer pessoa com acesso ao código (ou ao histórico Git) obtém credenciais de produção. A chave `pk_live_...` permite interagir com o gateway real conforme o provedor.

**Recomendação:** Mover para variáveis de ambiente com validação na inicialização:
```javascript
// src/config/index.js
const required = ['DB_USER', 'DB_PASS', 'PAYMENT_GATEWAY_KEY', 'SMTP_USER'];
for (const key of required) {
  if (!process.env[key]) throw new Error(`Missing env var: ${key}`);
}
module.exports = {
  dbUser: process.env.DB_USER,
  dbPass: process.env.DB_PASS,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  smtpUser: process.env.SMTP_USER,
  port: Number(process.env.PORT) || 3000,
};
```
Adicionar `.env.example` sem valores reais e `.env` ao `.gitignore`. **Rotacionar as chaves expostas** — removê-las do código não invalida o vazamento.

**Referência:** `references/anti-patterns.md` → SEC-02

---

### [CRITICAL] SEC-03 — Criptografia fraca / hash inseguro

**Onde:** `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68`

**Evidência:**
```javascript
// src/utils.js:17-23
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```
```javascript
// src/AppManager.js:18
this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");

// src/AppManager.js:68
let hash = badCrypto(p || "123456");
```

**Impacto:** `badCrypto` não é função de hash: é repetição de base64 (codificação reversível) truncada em 10 caracteres, sem salt e sem custo computacional efetivo. O espaço de saída é mínimo, permitindo colisões e reversão trivial. A seed armazena senha em texto puro (`'123'`) e há fallback silencioso para `"123456"` quando a senha não é enviada. Comprometimento de senhas de usuários é direto.

**Recomendação:** Usar `bcrypt`/`argon2` com salt e custo adequado, e rejeitar senha ausente em vez de usar default:
```javascript
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
// verificação: await bcrypt.compare(password, user.pass)
```
Nunca inserir senha em texto puro em seeds; usar usuário de teste com hash gerado.

**Referência:** `references/anti-patterns.md` → SEC-03

---

### [HIGH] SEC-04 — Rota sem autenticação/autorização

**Onde:** `src/AppManager.js:28-77` (POST /api/checkout), `src/AppManager.js:131` (DELETE), `src/AppManager.js:80` (GET administrativo)

**Evidência:**
```javascript
// src/AppManager.js:80
app.get('/api/admin/financial-report', (req, res) => {
// ...
// src/AppManager.js:131-137
app.delete('/api/users/:id', (req, res) => {
    let id = req.params.id;
    this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
        res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
    });
});
// src/AppManager.js:38-43,69-71 — identidade vem do body e não é provada
this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
    if (err) return res.status(500).send("Erro DB");
    // ...
    if (!user) {
        // cria usuário com badCrypto(p || "123456")
    } else {
        processPaymentAndEnroll(user.id); // sem validar a senha do titular
    }
});
```

**Impacto:** Qualquer cliente anônimo pode excluir usuários e obter o relatório financeiro completo, incluindo nome, e-mail e valores pagos de todos os estudantes. Não há token, sessão, role ou middleware de autorização em nenhuma rota. Além disso, `POST /api/checkout` aceita o e-mail de uma conta existente e cria matrícula/pagamento em nome dela sem verificar a senha: conhecendo apenas o e-mail, um cliente compra em nome de terceiro (IDOR). A regra expandida de SEC-04 cobre exatamente rotas de cadastro/criação que aceitam identidade ou dono vindo do cliente sem validar a autorização do titular.

**Recomendação:** Adicionar middleware de autenticação e guard de role `admin` nas rotas administrativas/destrutivas e derivar o dono do checkout da identidade autenticada, não do body:
```javascript
app.delete('/api/users/:id', requireAuth, requireRole('admin'), userController.remove);
app.get('/api/admin/financial-report', requireAuth, requireRole('admin'), reportController.financial);
// checkout: novo usuário pode ser público; e-mail existente exige senha do titular
// sem senha ou senha incorreta → 401; nunca aceitar usuario_id/owner_id/role do body
```
Enquanto não houver autenticação, remover ou bloquear essas rotas.

**Referência:** `references/anti-patterns.md` → SEC-04

---

### [HIGH] SEC-06 — Log com dados sensíveis

**Onde:** `src/AppManager.js:45`

**Evidência:**
```javascript
// src/AppManager.js:45
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

**Impacto:** O número completo do cartão (`cc`, vindo de `req.body.card`) e a chave live do gateway são impressos em texto puro no stdout. Logs costumam ser agregados, retidos e acessados por mais pessoas que o banco; isso expõe dados de cartão (escopo PCI DSS) e credencial de pagamento. O valor de `cc` também permanece em memória e pode vazar em stack traces.

**Recomendação:** Nunca logar PAN nem chave. Se necessário, mascarar e logar apenas metadados:
```javascript
const masked = `****${String(cc).slice(-4)}`;
logger.info({ event: 'payment_attempt', card: masked }, 'Processando pagamento');
```
Não logar `config.paymentGatewayKey` em nenhuma circunstância.

**Referência:** `references/anti-patterns.md` → SEC-06

---

### [HIGH] ARCH-01 — Lógica de negócio no Controller

**Onde:** `src/AppManager.js:29-75` (checkout), `src/AppManager.js:81-129` (relatório)

**Evidência:**
```javascript
// src/AppManager.js:43-64 (recorte)
let processPaymentAndEnroll = (userId) => {
    console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
    let status = cc.startsWith("4") ? "PAID" : "DENIED";

    if (status === "DENIED") return res.status(400).send("Pagamento recusado");

    this.db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
        // ...
        self.db.run("INSERT INTO payments ...", [enrId, course.price, status], function(err) {
            // ...
            self.db.run("INSERT INTO audit_logs ...", (err) => {
                logAndCache(`last_checkout_${userId}`, course.title);
                res.status(200).json({ msg: "Sucesso", enrollment_id: enrId });
            });
        });
    });
};
```
```javascript
// src/AppManager.js:89-127 (recorte)
courses.forEach(c => {
    let courseData = { course: c.title, revenue: 0, students: [] };
    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
        // ...
        enrollments.forEach(enr => {
            this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                // ...
                if (payment && payment.status === 'PAID') {
                    courseData.revenue += payment.amount;
                }
```

**Impacto:** Os handlers HTTP contêm regra de aprovação de pagamento (prefixo do cartão), decisão de criar usuário, orquestração de matrícula/pagamento/auditoria e agregação de receita por curso. Isso acopla transporte à regra de domínio: não é possível testar checkout ou cálculo de receita sem subir Express e SQLite, e qualquer mudança de regra exige editar o arquivo de rotas.

**Recomendação:** Extrair casos de uso para services e deixar o handler apenas orquestrar:
```javascript
// src/services/checkoutService.js
async function checkout({ user, email, password, courseId, card }) {
  const course = await courseRepository.findActive(courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');
  const status = paymentGateway.charge({ card, amount: course.price });
  if (status !== 'PAID') throw new PaymentDeniedError();
  return enrollmentRepository.createWithPayment({ user, email, password, course, status });
}
// rota: const result = await checkoutService.checkout(req.body); res.status(201).json(result);
```
O relatório deve delegar a `reportService.financialReport()`.

**Referência:** `references/anti-patterns.md` → ARCH-01

---

### [HIGH] ARCH-02 — Acesso a dados no Controller

**Onde:** `src/AppManager.js:37,40,50,54,57,69,83,92,104,106,133`

**Evidência:**
```javascript
// src/AppManager.js:37
this.db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid], (err, course) => {
// src/AppManager.js:50
this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, cid], function(err) {
// src/AppManager.js:83
this.db.all("SELECT * FROM courses", [], (err, courses) => {
// src/AppManager.js:133
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
```

**Impacto:** Todo o SQL está dentro dos handlers de rota. Não há repository/DAO nem modelo de acesso: trocar SQLite por outro banco, adicionar cache ou reutilizar a consulta exige alterar handlers HTTP. Consultas ficam impossíveis de testar isoladamente e não há ponto único de parametrização/paginação.

**Recomendação:** Introduzir repositories por agregado (`UserRepository`, `CourseRepository`, `EnrollmentRepository`, `PaymentRepository`, `AuditLogRepository`) e injetá-los nos services:
```javascript
class CourseRepository {
  constructor(db) { this.db = db; }
  findActiveById(id) { return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]); }
}
```
Handlers não devem referenciar `db` diretamente.

**Referência:** `references/anti-patterns.md` → ARCH-02

---

### [MEDIUM] PERF-01 — N+1 queries

**Onde:** `src/AppManager.js:89-127`

**Evidência:**
```javascript
// src/AppManager.js:89-106
courses.forEach(c => {
    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
        enrollments.forEach(enr => {
            this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {
```

**Impacto:** Para `C` cursos e `E` matrículas, o endpoint executa `1 + C + 2E` queries (uma por curso, duas por matrícula). O custo cresce linearmente com o volume e o endpoint administrativo fica progressivamente mais lento; em produção com muitas matrículas pode esgotar o pool/conexão. Além disso, a resposta só é enviada quando todos os contadores chegam a zero, tornando o fluxo frágil.

**Recomendação:** Usar `JOIN`/agregação única e montar o relatório em memória:
```sql
SELECT c.title AS course, e.id AS enrollment_id, u.name AS student,
       COALESCE(p.amount, 0) AS paid, p.status
FROM courses c
LEFT JOIN enrollments e ON e.course_id = c.id
LEFT JOIN users u ON u.id = e.user_id
LEFT JOIN payments p ON p.enrollment_id = e.id
```
Agrupar por curso no service (ou usar `Promise.all` de poucas queries agregadas).

**Referência:** `references/anti-patterns.md` → PERF-01

---

### [MEDIUM] QUAL-02 — Validação de entrada ausente

**Onde:** `src/AppManager.js:29-35`, `src/AppManager.js:132`

**Evidência:**
```javascript
// src/AppManager.js:29-35
let u = req.body.usr;
let e = req.body.eml;
let p = req.body.pwd;
let cid = req.body.c_id;
let cc = req.body.card;

if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```
```javascript
// src/AppManager.js:132
let id = req.params.id;
```

**Impacto:** A validação é apenas de presença. Não há checagem de tipo, formato de e-mail, formato/comprimento do cartão, nem `cid`/`id` numéricos. Valores como objeto/array em `cid` viram binding estranho no SQLite; `id` não numérico em `DELETE /api/users/:id` é aceito silenciosamente. A senha é opcional e recebe default `"123456"` (`:68`), mascarando erro de contrato. Entradas inválidas geram respostas 500 ou efeitos inesperados em vez de 400 preciso.

**Recomendação:** Validar com schema (ex.: `zod`/`joi`) no boundary HTTP e rejeitar campos obrigatórios ausentes:
```javascript
const checkoutSchema = z.object({
  usr: z.string().min(1),
  eml: z.string().email(),
  pwd: z.string().min(8),
  c_id: z.number().int().positive(),
  card: z.string().regex(/^\d{13,19}$/),
});
// handler: const data = checkoutSchema.parse(req.body); (erro → 400)
```
Validar `:id` como inteiro positivo antes de chamar o repository.

**Referência:** `references/anti-patterns.md` → QUAL-02

---

### [MEDIUM] QUAL-03 — Tratamento de erro genérico / erro engolido

**Onde:** `src/AppManager.js:57`, `src/AppManager.js:83`, `src/AppManager.js:92`, `src/AppManager.js:104`, `src/AppManager.js:106`, `src/AppManager.js:133-136`

**Evidência:**
```javascript
// src/AppManager.js:57-61
this.db.run("INSERT INTO audit_logs ...", (err) => {
    logAndCache(`last_checkout_${userId}`, course.title);
    res.status(200).json({ msg: "Sucesso", enrollment_id: enrId });
});
```
```javascript
// src/AppManager.js:92-93
this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
    let enrPending = enrollments.length;
```
```javascript
// src/AppManager.js:133-136
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
    res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
});
```

**Impacto:** Callbacks recebem `err` mas não o verificam. A falha ao gravar auditoria ainda retorna sucesso; falha nas queries do relatório causa `TypeError` em `enrollments.length`/`payment.amount` (500 não tratado); o DELETE retorna sucesso mesmo se o usuário não existir ou o banco falhar, e deixa matrículas/pagamentos órfãos (integridade referencial quebrada). Não há middleware central de erro nem logs de falha, dificultando diagnóstico.

**Recomendação:** Checar todo `err`, centralizar o tratamento e usar transação no delete/checkout:
```javascript
this.db.run('DELETE FROM users WHERE id = ?', [id], function (err) {
  if (err) return next(err);
  if (this.changes === 0) return res.status(404).json({ error: 'User not found' });
  res.status(204).end();
});
// middleware final: (err, req, res, next) => { logger.error(err); res.status(500).json({ error: 'Internal error' }); }
```
Executar limpeza/soft-delete das dependências na mesma transação.

**Referência:** `references/anti-patterns.md` → QUAL-03

---

### [MEDIUM] QUAL-04 — Estado global mutável

**Onde:** `src/utils.js:9-10`, `src/utils.js:12-15`, `src/utils.js:25`

**Evidência:**
```javascript
// src/utils.js:9-15
let globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
    console.log(`[LOG] Salvando no cache: ${key}`);
    globalCache[key] = data;
}
```
```javascript
// src/utils.js:25
module.exports = { config, logAndCache, badCrypto, globalCache, totalRevenue };
```

**Impacto:** `globalCache` é um objeto de módulo compartilhado entre todos os requests, sem TTL, limite ou isolamento — cresce indefinidamente (memory leak) e cria estado entre requisições, impedindo testes determinísticos e pods de réplica de compartilharem visão. `totalRevenue` é exportado por valor e nunca atualizado: qualquer consumidor lê sempre `0` (dead code enganoso).

**Recomendação:** Injetar cache como dependência com escopo explícito (ex.: Redis com TTL) e remover `totalRevenue`:
```javascript
class CheckoutService {
  constructor({ cache }) { this.cache = cache; } // cache com TTL e limite
  async checkout(data) { /* ... */ await this.cache.set(key, value, { ttl: 300 }); }
}
```
Se o cache for realmente necessário, usar `Map` com política de expiração encapsulada em classe testável.

**Referência:** `references/anti-patterns.md` → QUAL-04

---

### [LOW] QUAL-06 — Schema sem versionamento (no migrations)

**Onde:** `src/AppManager.js:10-23`

**Evidência:**
```javascript
// src/AppManager.js:10-22
initDb() {
    this.db.serialize(() => {
        this.db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
        this.db.run("CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)");
        this.db.run("CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)");
        this.db.run("CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)");
        this.db.run("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)");

        this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
```

**Impacto:** O DDL e os seeds vivem no boot e o banco é `:memory:`; não há histórico de schema, nem forma de replicar/evoluir um banco real. Não há chaves estrangeiras declaradas (`user_id`, `course_id`, `enrollment_id`), o que permite os órfãos observados no DELETE.

**Recomendação:** Adicionar migrations versionadas (ex.: `knex` migrations) com FKs e seeds separados:
```javascript
// migrations/001_create_users.js
exports.up = (knex) => knex.schema.createTable('users', (t) => {
  t.increments('id').primary();
  t.string('name').notNullable();
  t.string('email').notNullable().unique();
  t.string('pass').notNullable();
});
exports.down = (knex) => knex.schema.dropTable('users');
```
Declarar FKs com `onDelete('CASCADE')` ou soft-delete consciente.

**Referência:** `references/anti-patterns.md` → QUAL-06

---

### [LOW] QUAL-07 — Configuração hardcoded

**Onde:** `src/utils.js:1-7`

**Evidência:**
```javascript
// src/utils.js:1-7
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123", 
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

**Impacto:** Porta, usuário SMTP e demais parâmetros exigem alteração de código para cada ambiente (dev/staging/prod). O banco é fixo em `:memory:` (`src/AppManager.js:7`), então nem é possível apontar para outro engine sem editar código.

**Recomendação:** Centralizar config por ambiente com `process.env` e valores default apenas para desenvolvimento:
```javascript
module.exports = {
  port: Number(process.env.PORT) || 3000,
  smtpUser: process.env.SMTP_USER,
  databaseUrl: process.env.DATABASE_URL || ':memory:',
};
```
Os segredos em si são tratados no achado SEC-02 (CRITICAL).

**Referência:** `references/anti-patterns.md` → QUAL-07

---

### [LOW] QUAL-08 — Sem testes automatizados

**Onde:** `package.json:6-8` (ausência de script/dependências de teste); nenhum `tests/`, `__tests__/`, `*.test.js`

**Evidência:**
```json
// package.json:6-8
"scripts": {
  "start": "node src/app.js"
},
```
```json
// package.json:9-12 — nenhuma dependência de teste
"dependencies": {
  "express": "^4.18.2",
  "sqlite3": "^5.1.6"
}
```

**Impacto:** Não há rede de segurança para a refatoração. As três rotas (checkout, relatório, delete) e as regras de pagamento/agregação não têm testes; qualquer mudança estrutural pode quebrar comportamento sem detecção. Também não há script `test`, o que impede CI.

**Recomendação:** Adicionar suíte mínima com `jest` + `supertest` cobrindo os contratos atuais (incluindo os casos de sucesso/recusa do checkout e o shape do relatório):
```json
"scripts": { "test": "jest --runInBand" },
"devDependencies": { "jest": "^29.7.0", "supertest": "^7.0.0" }
```
Testar primeiro os contratos inventariados na Fase 1 antes de mover código.

**Referência:** `references/anti-patterns.md` → QUAL-08

---

### 2.1 Critérios objetivos de fechamento (CRITICAL/HIGH)

Um achado só é considerado **RESOLVIDO** na Fase 4 quando todos os critérios
abaixo são comprovados por código e por execução (`npm test` + HTTP real).
Qualquer critério pendente bloqueia o gate da Etapa 7.

| ID | Severidade | Critério de fechamento |
|---|---|---|
| **SEC-02** | CRITICAL | (a) nenhuma credencial literal no código ou `.env.example`; (b) `ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` lidos exclusivamente de variáveis de ambiente; (c) em produção, ausência de segredo falha no boot; (d) nenhum segredo em resposta HTTP ou log. |
| **SEC-03** | CRITICAL | (a) hash de senha com salt e custo adequado (scrypt/bcrypt/argon2), sem codificação reversível; (b) seed grava apenas hash — nenhuma senha em texto puro; (c) verificação em tempo constante; (d) `users.pass` no banco em repouso contém apenas hash. |
| **SEC-04** | HIGH | (a) `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `Bearer` de admin; (b) sem `ADMIN_TOKEN` as rotas falham fechado (`503`); (c) checkout de conta existente exige a senha do titular (`401` sem senha/senha errada) e nunca aceita id/dono/role do body; (d) novo usuário pode ser público, mas não cria matrícula em nome de terceiro. |
| **SEC-06** | HIGH | (a) logs não contêm PAN completo, chave de pagamento nem senha; (b) no máximo metadados mascarados (`cardLast4`); (c) nenhuma linha de log expõe `paymentGatewayKey`. |
| **ARCH-01** | HIGH | controllers apenas validam/orquestram/serializam; regra de negócio (pagamento, criação de usuário, agregação) está em services. |
| **ARCH-02** | HIGH | nenhum SQL em controllers/rotas; acesso a dados concentrado em repositories. |

## 3. Mapa de calor por arquivo

| Arquivo | CRIT | HIGH | MED | LOW | Total |
|---|---|---|---|---|---|
| `src/AppManager.js` | 0 | 4 | 3 | 1 | 8 |
| `src/utils.js` | 2 | 0 | 1 | 1 | 4 |
| `package.json` | 0 | 0 | 0 | 1 | 1 |

## 4. Achados por categoria

### Segurança
- **SEC-02, SEC-03, SEC-04, SEC-06** — credenciais e chave live hardcoded, hash de senha caseiro/reversível com senha seed em texto puro, rotas administrativa e destrutiva sem autenticação, checkout que aceita o e-mail de terceiro sem prova de posse (IDOR), e log do PAN completo do cartão + chave do gateway.

### Arquitetura
- **ARCH-01, ARCH-02** — checkout e relatório concentram regra de negócio e SQL dentro dos handlers; não há services nem repositories. A classe `AppManager` é o ponto único de schema, rota, negócio e persistência (embora com 141 LOC, abaixo do limiar de QUAL-01).

### Performance
- **PERF-01** — relatório financeiro executa `1 + C + 2E` queries em loops aninhados, sem JOIN/agregação.

### Qualidade
- **QUAL-02, QUAL-03, QUAL-04, QUAL-06, QUAL-07, QUAL-08** — validação só de presença, erros de callback ignorados e DELETE que deixa órfãos, cache global sem TTL e `totalRevenue` morto, DDL/seeds inline sem migrations ou FKs, config/porta hardcoded, e ausência total de testes.

## 5. Recomendações prioritárias

1. **[CRITICAL]** Remover credenciais e chave live de `src/utils.js:2-5` e migrar para env vars — **rotacionar os segredos expostos**.
2. **[CRITICAL]** Substituir `badCrypto` (`src/utils.js:17-23`) por `bcrypt`/`argon2`; remover senha em texto puro da seed (`src/AppManager.js:18`) e o default `"123456"` (`:68`).
3. **[HIGH]** Remover o log de cartão/chave (`src/AppManager.js:45`).
4. **[HIGH]** Proteger `DELETE /api/users/:id` e `GET /api/admin/financial-report` com autenticação/autorização e exigir prova de posse no checkout de conta existente (`src/AppManager.js:28-77,80,131`).
5. **[HIGH]** Extrair regra de negócio para services e SQL para repositories (`src/AppManager.js`), deixando handlers finos.
6. **[MEDIUM]** Reescrever o relatório com JOIN/agregação (`src/AppManager.js:89-127`).
7. **[MEDIUM]** Adicionar validação de schema no checkout e no `:id` (`src/AppManager.js:29-35,132`).
8. **[MEDIUM]** Tratar erros de todos os callbacks, usar transação no delete/checkout e middleware central de erro (`src/AppManager.js:57,83,92,104,106,133`).
9. **[MEDIUM]** Remover estado global / injetar cache com TTL e eliminar `totalRevenue` (`src/utils.js:9-25`).
10. **[LOW]** Adicionar migrations com FKs (`src/AppManager.js:10-23`), config por env (`src/utils.js:1-7`) e suíte de testes (`package.json`).

## 6. Notas e limitações

- **SEC-01 (SQL Injection) não se aplica:** todas as queries usam placeholders `?` com bindings (`src/AppManager.js:37,40,50,54,57,69,83,92,104,106,133`). A interpolação em `:57` monta apenas o valor do parâmetro de `audit_logs`, não o SQL.
- **SEC-05 (XSS) não se aplica:** a API não renderiza HTML/templates; respostas são `json`/`send` de texto fixo.
- **QUAL-01 (God Class) não foi emitido:** o catálogo exige >400 LOC em JS e `AppManager.js` tem 141 LOC. A concentração de responsabilidades é real, mas está coberta por ARCH-01/ARCH-02 sem inflar severidade.
- **QUAL-05 (dependência morta) não se aplica ao manifesto:** `express` e `sqlite3` são usados. Há código morto (`totalRevenue` importado em `src/AppManager.js:2` e nunca usado; exportado em `src/utils.js:10,25`), registrado dentro de QUAL-04 por ser o mesmo objeto de estado global.
- **ARCH-03 (Model com responsabilidades duplas) não foi emitido como achado separado:** não existe camada de Model; a ausência é consequência de ARCH-02 e está registrada na análise (Fase 1).
- **Riscos não catalogados** observados e não pontuados: checkout faz três inserts sem transação (`src/AppManager.js:50-63`), podendo deixar matrícula sem pagamento/auditoria; não há `db.close()` no shutdown (`src/app.js:12-14`); o relatório pode nunca responder se um contador não zerar; não há rota 404 nem error handler.
- **Ambiente:** `node_modules` não está instalado; a auditoria foi estática e as versões vêm do `package-lock.json`. Não foi executada a aplicação nem testes de exploração.
- **Contrato de negócio:** a aprovação de pagamento por `card.startsWith("4")` é claramente simulada; não há documento externo definindo o comportamento correto, então a refatoração deve preservar esse contrato observável (cartão iniciando em `4` → `PAID`; caso contrário → `DENIED`).
