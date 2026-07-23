'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { loadConfig } = require('../../src/config');
const { createAuthenticatedIdentity } = require('../../src/domain/identity');

const VALID_ENV = Object.freeze({
    PORT: '3100',
    PAYMENT_GATEWAY_KEY: 'test-payment-key',
    ADMIN_API_KEY: 'test-admin-key',
    USER_API_KEY: 'test-user-key',
    USER_EMAIL: 'Student@Example.com',
    SEED_DEMO_DATA: 'false',
});

test('carrega e valida exclusivamente o ambiente injetado', () => {
    const config = loadConfig(VALID_ENV);

    assert.equal(config.port, 3100);
    assert.equal(config.paymentGatewayKey, 'test-payment-key');
    assert.equal(config.seedDemoData, false);
    assert.deepEqual(config.apiKeys.get('test-admin-key'), {
        role: 'admin',
        email: null,
        canCheckoutForAnyEmail: true,
    });
    assert.deepEqual(config.apiKeys.get('test-user-key'), {
        role: 'user',
        email: 'student@example.com',
        canCheckoutForAnyEmail: false,
    });
});

test('falha claramente quando configuração obrigatória está ausente ou inválida', () => {
    assert.throws(
        () => loadConfig({ ...VALID_ENV, PAYMENT_GATEWAY_KEY: '' }),
        /PAYMENT_GATEWAY_KEY/
    );
    assert.throws(
        () => loadConfig({ ...VALID_ENV, PORT: 'inválida' }),
        /PORT/
    );
    assert.throws(
        () => loadConfig({ ...VALID_ENV, USER_API_KEY: VALID_ENV.ADMIN_API_KEY }),
        /devem ser distintas/
    );
    assert.throws(
        () => loadConfig({ ...VALID_ENV, USER_EMAIL: 'inválido' }),
        /e-mail válido/
    );
    assert.throws(
        () => createAuthenticatedIdentity({ role: 'user', email: 'user@teste.com', canCheckoutForAnyEmail: true }),
        /Apenas identidade admin/
    );
});
