'use strict';

const express = require('express');
const { loadConfig } = require('./config');
const { createLogger } = require('./infrastructure/logging/logger');
const { createMemoryCache } = require('./infrastructure/cache/memory-cache');
const { createPasswordHasher } = require('./infrastructure/security/password-hasher');
const { createPaymentGateway } = require('./infrastructure/payment/payment-gateway');
const { createConnection } = require('./infrastructure/database/connection');
const { seedDemoData } = require('./infrastructure/database/seed');
const { createUserRepository } = require('./infrastructure/database/repositories/user-repository');
const { createCourseRepository } = require('./infrastructure/database/repositories/course-repository');
const { createEnrollmentRepository } = require('./infrastructure/database/repositories/enrollment-repository');
const { createPaymentRepository } = require('./infrastructure/database/repositories/payment-repository');
const { createAuditLogRepository } = require('./infrastructure/database/repositories/audit-log-repository');
const { createCheckoutUseCase } = require('./application/checkout');
const { createFinancialReportUseCase } = require('./application/financial-report');
const { createDeleteUserUseCase } = require('./application/delete-user');
const { createRouter } = require('./adapters/http/routes');
const { createErrorHandler } = require('./adapters/http/error-handler');

/**
 * Composition root: carrega configuração, constrói infraestrutura,
 * repositories, casos de uso e adapters HTTP, e devolve a app pronta
 * para escutar. Nenhuma lógica de domínio vive aqui.
 */
function createApp(overrides = {}) {
    const config = overrides.config || loadConfig();
    const logger = overrides.logger || createLogger();
    const cache = overrides.cache || createMemoryCache();
    const passwordHasher = overrides.passwordHasher || createPasswordHasher();
    const paymentGateway = overrides.paymentGateway || createPaymentGateway(config.paymentGatewayKey);
    const connection = overrides.connection || createConnection();

    const userRepository = createUserRepository(connection);
    const courseRepository = createCourseRepository(connection);
    const enrollmentRepository = createEnrollmentRepository(connection);
    const paymentRepository = createPaymentRepository(connection);
    const auditLogRepository = createAuditLogRepository(connection);

    if (config.seedDemoData) {
        seedDemoData({ connection, userRepository, courseRepository, enrollmentRepository, paymentRepository, passwordHasher });
    }

    const checkoutUseCase = createCheckoutUseCase({
        connection,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        passwordHasher,
        paymentGateway,
        cache,
        logger,
    });
    const financialReportUseCase = createFinancialReportUseCase({ courseRepository, enrollmentRepository });
    const deleteUserUseCase = createDeleteUserUseCase({ connection, userRepository, enrollmentRepository, paymentRepository });

    const app = express();
    app.use(express.json());
    app.use(
        createRouter({
            apiKeys: config.apiKeys,
            checkoutUseCase,
            financialReportUseCase,
            deleteUserUseCase,
        })
    );
    app.use(createErrorHandler(logger));

    const repositories = { userRepository, courseRepository, enrollmentRepository, paymentRepository, auditLogRepository };

    return { app, config, connection, logger, repositories };
}

function start(overrides = {}) {
    const { app, config, connection, logger } = createApp(overrides);
    const server = app.listen(config.port, () => {
        logger.info(`API rodando na porta ${config.port}`);
    });
    return {
        server,
        close: () => new Promise((resolve) => server.close(() => {
            connection.close();
            resolve();
        })),
    };
}

if (require.main === module) {
    start();
}

module.exports = { createApp, start };
