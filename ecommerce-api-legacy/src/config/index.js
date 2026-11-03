// Configuração centralizada: único módulo que lê process.env.
const toBool = (value, fallback = false) =>
  value === undefined ? fallback : ['1', 'true', 'yes', 'on'].includes(String(value).toLowerCase());

module.exports = Object.freeze({
  env: process.env.NODE_ENV || 'development',
  port: Number(process.env.PORT) || 3000,
  logLevel: process.env.LOG_LEVEL || 'info',
  database: Object.freeze({
    filename: process.env.DATABASE_FILE || ':memory:',
    verbose: toBool(process.env.DATABASE_VERBOSE, false),
    seed: toBool(process.env.DATABASE_SEED, true),
  }),
  payment: Object.freeze({
    gatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  }),
  smtp: Object.freeze({
    user: process.env.SMTP_USER || '',
  }),
  // Endpoints administrativos ficam desabilitados (403) enquanto ADMIN_TOKEN não for definido.
  adminToken: process.env.ADMIN_TOKEN || '',
});
