# 📖 Playbook de Refatoração (Exemplos Antes vs. Depois)

Este documento contém os padrões concretos de código para corrigir cada um dos anti-patterns catalogados durante a Fase 3 e garantir a transição limpa da aplicação monolítica legada para a arquitetura MVC.

---

### 1. Hardcoded Secrets → Environment Variables

**ANTES (Inseguro):**
```javascript
// src/config/database.js
const DB_SECRET_KEY = "super-secret-master-key-123";
```

**DEPOIS (Refatorado):**

```javascript
// src/config/config.js
require('dotenv').config();

module.exports = {
    adminToken: process.env.ADMIN_TOKEN || 'default-fallback-token',
    port: process.env.PORT || 3000
};
```

### 2. SQL Injection Vulnerability → Parameterized Queries
ANTES (Vulnerável):

```javascript
// src/models/userModel.js
db.all(`SELECT * FROM users WHERE email = '${userEmail}'`, (err, rows) => { ... });
DEPOIS (Refatorado - Seguro):
```

```javascript
// src/models/userModel.js
db.all(`SELECT * FROM users WHERE email = ?`, [userEmail], (err, rows) => { ... });
```

### 3. God File / God Class → Modular MVC Architecture

ANTES (Monolítico):
```javascript
// AppManager.js (Milhares de linhas fazendo rotas, queries e regras de negócio juntas)
const express = require('express');
const sqlite3 = require('sqlite3');
const app = express();

app.post('/api/checkout', (req, res) => {
  // Lógica pesada de banco, validação e resposta misturadas
});
```


DEPOIS (Modular MVC):

```javascript
Plaintext
src/
├── app.js
├── config/
├── controllers/
├── models/
├── routes/
└── middlewares/
```

### 4. Bypass de Camadas em Rotas → Controller / Service Isolation

ANTES (Lógica de Negócio na Rota):

```javascript
// src/routes/userRoutes.js
router.post('/checkout', (req, res) => {
    db.run("INSERT INTO enrollments...", function(err) {
        // Regras de negócio direto no arquivo de rota
        res.json({ msg: "Sucesso" });
    });
});
```

DEPOIS (Isolamento via Controller):
```javascript
// src/routes/userRoutes.js
const checkoutController = require('../controllers/checkoutController');
router.post('/checkout', checkoutController.processCheckout);
```

### 5. Callback Hell Assíncrono → Async / Await & Promises

ANTES (Callbacks Aninhados):
```javascript
db.get("SELECT * FROM courses WHERE id = ?", [id], (err, course) => {
    db.all("SELECT * FROM enrollments WHERE course_id = ?", [id], (err, enrollments) => {
        res.json({ course, enrollments });
    });
});
```

DEPOIS (Async / Await Limpo):
```javascript
async function getCourseDetails(req, res) {
    try {
        const course = await courseModel.findById(req.params.id);
        const enrollments = await enrollmentModel.findByCourse(req.params.id);
        res.json({ course, enrollments });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
}
```

### 6. Queries N+1 no Banco → Direct SQL Aggregation / JOINs

ANTES (Múltiplas queries em loop):
```javascript
// Executando queries separadas para cada registro iterado
users.forEach(user => {
    db.get("SELECT * FROM payments WHERE user_id = ?", [user.id], ...);
});
```

DEPOIS (Query Otimizada com JOIN):
```javascript
// src/models/reportModel.js
const query = `
    SELECT c.title as course, SUM(p.amount) as revenue, GROUP_CONCAT(u.name) as students
    FROM courses c
    LEFT JOIN enrollments e ON c.id = e.course_id
    LEFT JOIN users u ON e.user_id = u.id
    LEFT JOIN payments p ON e.id = p.enrollment_id
    GROUP BY c.id
`;
```

### 7. Tratamento Inseguro de Exceções → Centralized Error Middleware

ANTES (Try/Catch repetitivo em cada rota):

```javascript
app.get('/data', (req, res) => {
    try {
        // código que pode falhar
    } catch (err) {
        res.status(500).send(err.message);
    }
});
```

DEPOIS (Middleware Centralizado):
```javascript
// src/middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
    const statusCode = err.status || 500;
    res.status(statusCode).json({
        error: true,
        message: err.message || 'Erro interno no servidor'
    });
}
```

### 8. APIs Deprecated / Obsoletas → Modern Native Middleware

ANTES (Uso de bibliotecas externas legadas para parsing):

```javascript
const bodyParser = require('body-parser');
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
```

DEPOIS (Uso de recursos nativos modernos do Express):
```javascript
// src/app.js
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
```