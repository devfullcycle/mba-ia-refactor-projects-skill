const createCheckoutRoutes = require('./checkoutRoutes');
const createReportRoutes = require('./reportRoutes');
const createUserRoutes = require('./userRoutes');

function registerRoutes(app, db) {
  app.use('/api', createCheckoutRoutes(db));
  app.use('/api', createReportRoutes(db));
  app.use('/api', createUserRoutes(db));
}

module.exports = registerRoutes;
