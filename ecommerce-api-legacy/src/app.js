const express = require('express');
const config = require('./config');
const { createDatabase } = require('./database/connection');
const { initSchema } = require('./database/schema');
const paymentGateway = require('./services/paymentGateway');
const { hashPassword } = require('./utils/password');
const createRoutes = require('./routes');
const createAdminAuth = require('./middlewares/adminAuth');
const errorHandler = require('./middlewares/errorHandler');

// Composition root: monta dependências e inicia o servidor.
async function main() {
    const db = createDatabase(config.dbPath);
    await initSchema(db, config);

    const models = {
        user: require('./models/userModel')(db),
        course: require('./models/courseModel')(db),
        enrollment: require('./models/enrollmentModel')(db),
        payment: require('./models/paymentModel')(db),
        auditLog: require('./models/auditLogModel')(db),
        report: require('./models/reportModel')(db)
    };

    const checkoutService = require('./services/checkoutService')({ db, models, paymentGateway, hashPassword });
    const reportService = require('./services/reportService')({ models });

    const controllers = {
        checkout: require('./controllers/checkoutController')({ checkoutService }),
        report: require('./controllers/reportController')({ reportService }),
        user: require('./controllers/userController')({ models })
    };

    const app = express();
    app.use(express.json());
    app.use('/api', createRoutes({ controllers, adminAuth: createAdminAuth(config.adminToken) }));
    app.use(errorHandler);

    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    console.error('Falha ao iniciar a aplicação:', err);
    process.exit(1);
});
