/**
 * @deprecated AppManager foi refatorado e decomposto na arquitetura MVC limpa:
 * - models/database.js
 * - models/userModel.js
 * - models/courseModel.js
 * - models/paymentModel.js
 * - controllers/checkoutController.js
 * - controllers/reportController.js
 * - controllers/userController.js
 * - routes/index.js
 * Este arquivo foi mantido como um facade de compatibilidade transitória.
 */
const db = require('./models/database');
const apiRoutes = require('./routes');

class AppManager {
    constructor() {
        this.db = db.getDb();
    }

    async initDb() {
        return db.initDb();
    }

    setupRoutes(app) {
        app.use('/api', apiRoutes);
    }
}

module.exports = AppManager;
