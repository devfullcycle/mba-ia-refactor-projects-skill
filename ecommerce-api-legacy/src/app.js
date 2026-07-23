const express = require('express');
const routes = require('./routes');
const { notFound, errorHandler } = require('./middlewares/errorHandler');

function createApp() {
  const app = express();
  app.use(express.json());
  app.use(routes);
  app.use(notFound);
  app.use(errorHandler);
  return app;
}

module.exports = { createApp };
