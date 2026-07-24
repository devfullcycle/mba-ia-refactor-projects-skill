'use strict';

/**
 * Configuração da aplicação — toda origem é variável de ambiente.
 * Nenhum segredo literal neste módulo (ver `.env.example`).
 */

function required(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(
            `Variável de ambiente obrigatória ausente: ${name}. Ver .env.example.`
        );
    }
    return value;
}

function bool(name, fallback = false) {
    const raw = process.env[name];
    if (raw === undefined) return fallback;
    return ['1', 'true', 'yes', 'on'].includes(raw.trim().toLowerCase());
}

function buildConfig(env = process.env) {
    const appEnv = env.APP_ENV || 'development';
    const isProduction = appEnv === 'production';

    return {
        env: appEnv,
        isProduction,
        port: Number(env.PORT || 3000),
        logLevel: env.LOG_LEVEL || 'info',
        database: {
            file: env.DB_FILE || ':memory:',
            seedOnBoot: bool('SEED_ON_BOOT', !isProduction),
        },
        payment: {
            // Em produção a chave é obrigatória; em desenvolvimento o gateway é simulado.
            gatewayKey: isProduction ? required('PAYMENT_GATEWAY_KEY') : env.PAYMENT_GATEWAY_KEY || null,
        },
        security: {
            // Sem chave configurada, as rotas administrativas negam acesso (fail closed).
            adminApiKey: env.ADMIN_API_KEY || null,
            passwordMinLength: Number(env.PASSWORD_MIN_LENGTH || 6),
        },
    };
}

module.exports = { buildConfig, required, bool };
