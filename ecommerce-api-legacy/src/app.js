const express = require('express');

const { loadConfig } = require('./config');
const logger = require('./utils/logger');
const Database = require('./database/Database');
const { initSchema, seed } = require('./database/schema');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const FinancialReportModel = require('./models/financialReportModel');

const passwordService = require('./services/passwordService');
const paymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const FinancialReportService = require('./services/financialReportService');
const UserService = require('./services/userService');

const CheckoutController = require('./controllers/checkoutController');
const AdminController = require('./controllers/adminController');
const UserController = require('./controllers/userController');

const createAdminAuth = require('./middlewares/adminAuth');
const createErrorHandler = require('./middlewares/errorHandler');
const createRoutes = require('./routes');

// Composition root: cria e injeta as dependências, registra rotas e middlewares.
async function buildApp(config) {
    const db = new Database(config.databaseFile);
    await initSchema(db);
    await seed(db, passwordService);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);
    const financialReportModel = new FinancialReportModel(db);

    const checkoutService = new CheckoutService({
        userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, passwordService, paymentGateway, logger
    });
    const financialReportService = new FinancialReportService({ financialReportModel });
    const userService = new UserService({ userModel, logger });

    const routes = createRoutes({
        checkoutController: new CheckoutController({ checkoutService }),
        adminController: new AdminController({ financialReportService }),
        userController: new UserController({ userService }),
        adminAuth: createAdminAuth(config.adminToken)
    });

    const app = express();
    app.use(express.json());
    app.use('/api', routes);
    app.use(createErrorHandler(logger));

    return app;
}

async function main() {
    const config = loadConfig();
    const app = await buildApp(config);

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
        if (!config.adminToken) {
            logger.warn('ADMIN_TOKEN não definido: rotas administrativas estão bloqueadas (403).');
        }
    });
}

main().catch(err => {
    logger.error('Falha ao iniciar a aplicação', err);
    process.exit(1);
});
