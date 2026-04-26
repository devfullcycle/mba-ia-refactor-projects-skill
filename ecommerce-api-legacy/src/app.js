const express = require('express');
const config = require('./config');
const { createDatabase } = require('./database/connection');
const { initializeSchema, seedData } = require('./database/schema');
const registerRoutes = require('./routes');
const { errorHandler } = require('./middlewares/errorHandler');

async function start() {
  const app = express();
  app.use(express.json());

  const db = await createDatabase(config.dbPath);
  await initializeSchema(db);
  await seedData(db);

  registerRoutes(app, db);
  app.use(errorHandler);

  app.listen(config.port, () => {
    console.log(`LMS API running on port ${config.port}`);
  });
}

start().catch((err) => {
  console.error('Failed to start application:', err);
  process.exit(1);
});
