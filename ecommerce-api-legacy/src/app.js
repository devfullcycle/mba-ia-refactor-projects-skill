const express = require('express');

const env = require('./config/env');
const logger = require('./config/logger');
const { createDatabase } = require('./config/database');
const { initDatabase } = require('./seed');

const CourseModel = require('./models/courseModel');
const UserModel = require('./models/userModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const ReportModel = require('./models/reportModel');

const CacheService = require('./services/cacheService');

const CheckoutController = require('./controllers/checkoutController');
const FinancialReportController = require('./controllers/financialReportController');
const UserController = require('./controllers/userController');

const createCheckoutRoutes = require('./routes/checkoutRoutes');
const createAdminRoutes = require('./routes/adminRoutes');
const createUserRoutes = require('./routes/userRoutes');

const asyncHandler = require('./middlewares/asyncHandler');
const errorHandler = require('./middlewares/errorHandler');

async function createApp() {
    const db = createDatabase();
    await initDatabase(db);

    const courseModel = new CourseModel(db);
    const userModel = new UserModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);
    const reportModel = new ReportModel(db);
    const cacheService = new CacheService();

    const checkoutController = new CheckoutController({
        courseModel,
        userModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        cacheService,
    });
    const financialReportController = new FinancialReportController({ reportModel });
    const userController = new UserController({ userModel, enrollmentModel, paymentModel });

    const app = express();
    app.use(express.json());

    app.use('/api', createCheckoutRoutes(checkoutController, asyncHandler));
    app.use('/api/admin', createAdminRoutes(financialReportController, asyncHandler));
    app.use('/api', createUserRoutes(userController, asyncHandler));

    app.use(errorHandler);

    return app;
}

async function start() {
    const app = await createApp();
    app.listen(env.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${env.port}...`);
    });
}

if (require.main === module) {
    start();
}

module.exports = { createApp };
