const express = require('express');
const config = require('./config');
const { openDatabase, initDb } = require('./database');
const { CacheService } = require('./cache');
const { CheckoutService } = require('./services/checkoutService');
const { ReportService } = require('./services/reportService');
const { UserService } = require('./services/userService');
const { setupRoutes } = require('./routes');

async function buildApp() {
  const app = express();
  app.use(express.json());

  const conn = openDatabase(':memory:');
  await initDb(conn);

  const cache = new CacheService();
  const services = {
    checkout: new CheckoutService(conn, cache, config),
    report: new ReportService(conn),
    users: new UserService(conn),
  };

  setupRoutes(app, services);

  app.use((err, req, res, next) => {
    const status = err.status || 500;
    if (status >= 500) {
      console.error(err);
    }
    res.status(status).send(err.message || 'Erro interno');
  });

  return app;
}

module.exports = { buildApp };

if (require.main === module) {
  buildApp().then((app) => {
    app.listen(config.port, () => {
      console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
  });
}
