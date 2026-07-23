'use strict';

const { createAuthenticatedIdentity } = require('../domain/identity');

/**
 * Configuração validada, lida exclusivamente de variáveis de ambiente.
 * Nenhum segredo deve viver como literal neste repositório (F-002).
 */
function requireEnv(env, name) {
    const value = env[name];
    if (!value || value.trim() === '') {
        throw new Error(`Configuração ausente: defina a variável de ambiente ${name}`);
    }
    return value;
}

function loadConfig(env = process.env) {
    const port = Number(env.PORT || 3000);
    if (!Number.isInteger(port) || port <= 0) {
        throw new Error('Configuração inválida: PORT deve ser um inteiro positivo');
    }

    const paymentGatewayKey = requireEnv(env, 'PAYMENT_GATEWAY_KEY');
    const adminApiKey = requireEnv(env, 'ADMIN_API_KEY');
    const userApiKey = requireEnv(env, 'USER_API_KEY');
    const userEmail = requireEnv(env, 'USER_EMAIL');

    if (adminApiKey === userApiKey) {
        throw new Error('Configuração inválida: ADMIN_API_KEY e USER_API_KEY devem ser distintas');
    }

    return {
        port,
        paymentGatewayKey,
        seedDemoData: env.SEED_DEMO_DATA !== 'false',
        apiKeys: new Map([
            [adminApiKey, createAuthenticatedIdentity({ role: 'admin', canCheckoutForAnyEmail: true })],
            [userApiKey, createAuthenticatedIdentity({ role: 'user', email: userEmail })],
        ]),
    };
}

module.exports = { loadConfig, requireEnv };
