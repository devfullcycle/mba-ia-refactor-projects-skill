const express = require('express');

const config = require('./config');
const logger = require('./logger');
const { Database, initSchema } = require('./config/database');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');

const passwordService = require('./services/passwordService');
const PaymentGateway = require('./services/paymentGateway');
const Cache = require('./services/cache');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const registerRoutes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

// Composition root: cria tudo, injeta dependências e sobe o servidor.
async function main() {
    const app = express();
    app.use(express.json());

    const db = new Database(config.dbPath);
    await initSchema(db, passwordService);

    // Models (repositories)
    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    // Services
    const paymentGateway = new PaymentGateway(config.paymentGatewayKey, logger);
    const cache = new Cache(logger);
    const checkoutService = new CheckoutService({
        userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
        passwordService, paymentGateway, cache,
    });
    const reportService = new ReportService(db);

    // Controllers
    const checkoutController = new CheckoutController(checkoutService);
    const reportController = new ReportController(reportService);
    const userController = new UserController(userModel);

    registerRoutes(app, { checkoutController, reportController, userController });
    app.use(errorHandler(logger));

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS (refatorado) rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', err);
    process.exit(1);
});
