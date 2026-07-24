'use strict';

/**
 * Composition root: monta as camadas e devolve o app Express.
 *
 * Não escuta porta (isso é responsabilidade de `server.js`), o que permite instanciar a
 * aplicação em teste sem abrir socket.
 */

const express = require('express');

const { createConnection } = require('./database/connection');
const { UserRepository } = require('./models/user.repository');
const { CourseRepository } = require('./models/course.repository');
const { EnrollmentRepository } = require('./models/enrollment.repository');
const { PaymentRepository } = require('./models/payment.repository');
const { AuditRepository } = require('./models/audit.repository');
const { FakePaymentGateway } = require('./services/payment-gateway');
const { CheckoutService } = require('./services/checkout.service');
const { ReportService } = require('./services/report.service');
const { CheckoutController } = require('./controllers/checkout.controller');
const { ReportController } = require('./controllers/report.controller');
const { UserController } = require('./controllers/user.controller');
const { createRequireAdmin } = require('./middlewares/auth');
const { createErrorHandler, notFoundHandler } = require('./middlewares/errorHandler');
const { createRouter } = require('./routes');
const { MemoryCache } = require('./utils/memory-cache');

function createApp({ config, logger, connection }) {
    const db = connection || createConnection(config);

    // Camada de dados
    const userRepository = new UserRepository(db);
    const courseRepository = new CourseRepository(db);
    const enrollmentRepository = new EnrollmentRepository(db);
    const paymentRepository = new PaymentRepository(db);
    const auditRepository = new AuditRepository(db);

    // Infra de apoio e serviços
    const cache = new MemoryCache({ maxEntries: 500 });
    const paymentGateway = new FakePaymentGateway({
        logger,
        apiKey: config.payment.gatewayKey,
    });
    const checkoutService = new CheckoutService({
        connection: db,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditRepository,
        paymentGateway,
        cache,
        logger,
        passwordMinLength: config.security.passwordMinLength,
    });
    const reportService = new ReportService({ enrollmentRepository });

    // Controllers
    const checkoutController = new CheckoutController({ checkoutService });
    const reportController = new ReportController({ reportService });
    const userController = new UserController({ userRepository, logger });

    // Aplicação
    const app = express();
    app.use(express.json());
    app.use(
        '/api',
        createRouter({
            checkoutController,
            reportController,
            userController,
            requireAdmin: createRequireAdmin({
                adminApiKey: config.security.adminApiKey,
                logger,
            }),
        })
    );

    app.use(notFoundHandler);
    app.use(createErrorHandler({ logger })); // registrado por último

    return { app, connection: db, cache };
}

module.exports = { createApp };
