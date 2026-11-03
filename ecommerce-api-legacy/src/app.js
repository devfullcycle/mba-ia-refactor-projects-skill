// Composition root: cria infraestrutura, injeta dependências e registra rotas/middlewares.
const express = require('express');

const config = require('./config');
const { createLogger } = require('./utils/logger');
const { createDatabase } = require('./database/connection');
const { createSchema, seed } = require('./database/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentService } = require('./services/paymentService');
const passwordService = require('./services/passwordService');
const CacheService = require('./services/cacheService');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const createRoutes = require('./views/routes');
const { createRequireAdmin } = require('./middlewares/requireAdmin');
const { createErrorHandler, notFoundHandler } = require('./middlewares/errorHandler');

async function createApp(appConfig = config) {
  const logger = createLogger(appConfig.logLevel);

  const db = await createDatabase(appConfig.database);
  await createSchema(db);
  if (appConfig.database.seed) await seed(db, passwordService);

  const userModel = new UserModel(db);
  const courseModel = new CourseModel(db);
  const enrollmentModel = new EnrollmentModel(db);

  const paymentService = new PaymentService({ gatewayKey: appConfig.payment.gatewayKey, logger });
  const cacheService = new CacheService({ logger });

  const checkoutController = new CheckoutController({
    db, userModel, courseModel, enrollmentModel, paymentService, passwordService, cacheService,
  });
  const reportController = new ReportController({ courseModel });
  const userController = new UserController({ db, userModel, logger });

  const app = express();
  app.use(express.json());
  app.use(createRoutes({
    checkoutController,
    reportController,
    userController,
    requireAdmin: createRequireAdmin(appConfig.adminToken),
  }));
  app.use(notFoundHandler);
  app.use(createErrorHandler(logger));

  return { app, db, logger };
}

if (require.main === module) {
  createApp()
    .then(({ app, logger }) => {
      app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
    })
    .catch((err) => {
      console.error('Falha ao iniciar a aplicação:', err);
      process.exit(1);
    });
}

module.exports = { createApp };
