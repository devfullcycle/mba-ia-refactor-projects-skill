/**
 * Entry point / Composition root da aplicação Express.
 * Registra middlewares, rotas e inicializa o banco.
 */
const express = require('express');
const path = require('path');
const routes = require('./routes');
const { config } = require('./config');
const { initDb, seed } = require('./models/db');
const { notFoundHandler, errorHandler } = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

// Inicializa persistência e seed antes de subir.
initDb();
seed();

// Rotas da aplicação.
app.use('/api', routes);

// Tratamento de erros centralizado.
app.use(notFoundHandler);
app.use(errorHandler);

if (require.main === module) {
    app.listen(config.port, () => {
        console.log(`LMS rodando na porta ${config.port}...`);
    });
}

module.exports = app;