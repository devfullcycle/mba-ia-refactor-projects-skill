const express = require('express');
const config = require('./config/config');
const database = require('./models/database');
const apiRoutes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();

// Middlewares globais
app.use(express.json());

// Registro de rotas desacopladas
app.use('/api', apiRoutes);

// Middleware centralizado de tratamento de erros
app.use(errorHandler);

async function startServer() {
    try {
        await database.initDb();
        const server = app.listen(config.port, () => {
            console.log(`LMS API refatorada (MVC) rodando na porta ${config.port}...`);
        });
        return { app, server };
    } catch (error) {
        console.error("Falha fatal na inicialização do servidor:", error);
        process.exit(1);
    }
}

if (require.main === module) {
    startServer();
}

module.exports = { app, startServer };
