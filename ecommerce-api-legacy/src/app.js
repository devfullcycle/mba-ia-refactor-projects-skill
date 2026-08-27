const express = require('express');
const { initDb } = require('../database');
const routes = require('../routes/routes');
const errorHandler = require('../middlewares/errorHandler');
const config = require('../config/config');

const app = express();
app.use(express.json());

// Registrar rotas globais da API
app.use('/api', routes);

// Registrar middleware de erro unificado
app.use(errorHandler);

// Inicializar banco de dados e subir o servidor HTTP
initDb()
    .then(() => {
        app.listen(config.port, () => {
            console.log(`Frankenstein LMS rodando na porta ${config.port} (ARQUITETURA MVC)...`);
        });
    })
    .catch((err) => {
        console.error("Falha ao iniciar o servidor devido ao banco de dados:", err);
    });
