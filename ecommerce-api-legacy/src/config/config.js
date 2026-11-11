const fs = require('fs');
const path = require('path');

// Carrega o .env da raiz do projeto, se existir (nativo no Node >= 20.12).
const envPath = path.resolve(__dirname, '..', '..', '.env');
if (fs.existsSync(envPath)) {
    process.loadEnvFile(envPath);
}

function toInt(value, fallback) {
    const parsed = Number.parseInt(value, 10);
    return Number.isNaN(parsed) ? fallback : parsed;
}

const nodeEnv = process.env.NODE_ENV || 'development';

const config = Object.freeze({
    nodeEnv,
    isProduction: nodeEnv === 'production',
    port: toInt(process.env.PORT, 3000),
    dbPath: process.env.DB_PATH || ':memory:',
    seedDb: (process.env.SEED_DB || 'true').toLowerCase() === 'true',
    seedUserPassword: process.env.SEED_USER_PASSWORD || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: (process.env.LOG_LEVEL || 'info').toLowerCase(),
});

if (config.isProduction && !config.paymentGatewayKey) {
    throw new Error('PAYMENT_GATEWAY_KEY é obrigatória em produção');
}

module.exports = config;
