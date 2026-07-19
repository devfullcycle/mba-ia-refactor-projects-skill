const express = require('express');

const config = require('./config');
const Database = require('./db/database');
const initDb = require('./db/init');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const ReportModel = require('./models/reportModel');

const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const buildRouter = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

// Composition root: cria a app, injeta a conexão nos models/services/controllers,
// registra rotas e o middleware de erro, e sobe o servidor.
async function createApp() {
    const db = new Database(config.db.path);
    await initDb(db);

    // Models (data access) com a conexão injetada — sem estado global.
    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);
    const reportModel = new ReportModel(db);

    // Services (regra de negócio / orquestração de domínio).
    const checkoutService = new CheckoutService({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
    });
    const reportService = new ReportService({ reportModel });

    // Controllers (magros).
    const checkoutController = new CheckoutController({ checkoutService });
    const reportController = new ReportController({ reportService });
    const userController = new UserController({ userModel });

    const app = express();
    app.use(express.json());
    app.use('/api', buildRouter({ checkoutController, reportController, userController }));
    app.use(errorHandler);

    return app;
}

async function start() {
    const app = await createApp();
    app.listen(config.port, () => {
        console.log(`LMS API rodando na porta ${config.port}...`);
    });
}

// Só inicia o servidor quando executado diretamente (facilita testes).
if (require.main === module) {
    start().catch((err) => {
        console.error('Falha ao iniciar a aplicação:', err);
        process.exit(1);
    });
}

module.exports = { createApp };
