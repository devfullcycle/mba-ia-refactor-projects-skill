const { createApp } = require('./app');
const config = require('./config');
const { initDb } = require('./db');
const { log, logError } = require('./utils/logger');

async function start() {
  await initDb();
  const app = createApp();
  const server = app.listen(config.port, () =>
    log(`LMS API rodando na porta ${config.port} (${config.nodeEnv})`)
  );
  const shutdown = () => server.close(() => process.exit(0));
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
  server.on('error', logError);
}

if (require.main === module) {
  start().catch((err) => {
    logError('Falha ao iniciar:', err);
    process.exit(1);
  });
}

module.exports = { start };
