const express = require('express');
const config = require('./config/config');
const logger = require('./config/logger');
const database = require('./config/database');
const { seedDatabase } = require('./config/seed');
const routes = require('./routes');
const { errorHandler, notFoundHandler } = require('./middlewares/errorHandler');

function createApp() {
    const app = express();
    app.disable('x-powered-by');
    app.use(express.json());
    app.use('/api', routes);
    app.use(notFoundHandler);
    app.use(errorHandler);
    return app;
}

async function start() {
    await database.connect();
    await seedDatabase();
    const app = createApp();
    return app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        logger.error('Falha ao iniciar a aplicação', { error: err.message, stack: err.stack });
        process.exit(1);
    });
}

module.exports = { createApp, start };
