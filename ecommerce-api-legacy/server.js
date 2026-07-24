'use strict';

/**
 * Ponto de entrada do servidor.
 * Uso: npm start — configuração por variáveis de ambiente (ver `.env.example`).
 */

const { buildConfig } = require('./src/config');
const { createApp } = require('./src/app');
const { createConnection } = require('./src/database/connection');
const { createSchema } = require('./src/database/schema');
const { seedIfEmpty } = require('./src/database/seed');
const { createLogger } = require('./src/utils/logger');

async function main() {
    const config = buildConfig();
    const logger = createLogger(config.logLevel);

    const connection = createConnection(config);
    await createSchema(connection);
    if (config.database.seedOnBoot) {
        await seedIfEmpty(connection, logger);
    }

    if (!config.security.adminApiKey) {
        logger.warn(
            'ADMIN_API_KEY não configurada — rotas administrativas responderão 401 até que ' +
                'a variável seja definida (ver .env.example)'
        );
    }

    const { app } = createApp({ config, logger, connection });

    const server = app.listen(config.port, () => {
        logger.info('Servidor iniciado', {
            service: 'lms-api',
            port: config.port,
            env: config.env,
            database: config.database.file,
        });
    });

    const shutdown = (signal) => {
        logger.info('Encerrando servidor', { signal });
        server.close(() => {
            connection.close().finally(() => process.exit(0));
        });
    };
    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));
}

main().catch((error) => {
    process.stderr.write(`Falha ao iniciar a aplicação: ${error.message}\n`);
    process.exit(1);
});
