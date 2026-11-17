// Único ponto de leitura de variáveis de ambiente.
const env = process.env;
const isProduction = env.NODE_ENV === 'production';

// Em desenvolvimento há um token padrão explícito; em produção ele é obrigatório.
const adminToken = env.ADMIN_TOKEN || (isProduction ? undefined : 'dev-admin-token');
if (!adminToken) {
    throw new Error('ADMIN_TOKEN é obrigatório quando NODE_ENV=production');
}

module.exports = {
    port: Number(env.PORT) || 3000,
    dbPath: env.DB_PATH || ':memory:',
    adminToken,
    paymentGatewayKey: env.PAYMENT_GATEWAY_KEY,
    seedUserPassword: env.SEED_USER_PASSWORD || 'dev-seed-password'
};
