const express = require('express');
const { loadConfig } = require('./config');
const Database = require('./models/database');
const { seedDatabase } = require('./models/seed');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const FinancialReportModel = require('./models/financialReportModel');
const CheckoutController = require('./controllers/checkoutController');
const FinancialReportController = require('./controllers/financialReportController');
const UserController = require('./controllers/userController');
const { buildCheckoutRoutes } = require('./routes/checkoutRoutes');
const { buildAdminRoutes } = require('./routes/adminRoutes');
const { buildUserRoutes } = require('./routes/userRoutes');
const { buildErrorHandler } = require('./middlewares/errorHandler');
const { requireAdmin } = require('./middlewares/adminAuth');
const { createLogger } = require('./services/logger');
const PasswordHasher = require('./services/passwordHasher');
const FakePaymentGateway = require('./services/paymentGateway');

// Composition root: config → DB → models → services → controllers → routes.
async function createApp(config = loadConfig()) {
    const logger = createLogger(config.logLevel);

    const db = await Database.open(config.dbPath, { verbose: config.nodeEnv === 'development' });
    await db.initSchema();
    const passwordHasher = new PasswordHasher();
    await seedDatabase(db, passwordHasher);

    const users = new UserModel(db);
    const paymentGateway = new FakePaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    const checkoutController = new CheckoutController({
        db,
        users,
        courses: new CourseModel(db),
        enrollments: new EnrollmentModel(db),
        payments: new PaymentModel(db),
        auditLogs: new AuditLogModel(db),
        paymentGateway,
        passwordHasher,
        logger,
    });
    const financialReportController = new FinancialReportController({ financialReport: new FinancialReportModel(db) });
    const userController = new UserController({ db, users, logger });

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas responderão 403');
    const adminGuard = requireAdmin(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use('/api', buildCheckoutRoutes(checkoutController));
    app.use('/api', buildAdminRoutes(financialReportController, adminGuard));
    app.use('/api', buildUserRoutes(userController, adminGuard));
    app.use(buildErrorHandler(logger));

    return { app, db, logger };
}

async function start() {
    const config = loadConfig();
    const { app, logger } = await createApp(config);
    app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
}

if (require.main === module) {
    start().catch((err) => {
        process.stderr.write(`Falha ao iniciar a aplicação: ${err.stack || err}\n`);
        process.exit(1);
    });
}

module.exports = { createApp };
