// Configuração lida exclusivamente de variáveis de ambiente.
// Apenas valores seguros para desenvolvimento têm default (porta, banco em memória).
function loadConfig(env = process.env) {
    return Object.freeze({
        nodeEnv: env.NODE_ENV || 'development',
        port: Number(env.PORT || 3000),
        dbPath: env.DB_PATH || ':memory:',
        paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || '',
        adminToken: env.ADMIN_TOKEN || '',
        logLevel: env.LOG_LEVEL || 'info',
    });
}

module.exports = { loadConfig };
