'use strict';

const { AuthorizationError } = require('./errors');

function normalizeEmail(email) {
    return typeof email === 'string' ? email.trim().toLowerCase() : '';
}

function createAuthenticatedIdentity({ role, email = null, canCheckoutForAnyEmail = false }) {
    if (role !== 'admin' && role !== 'user') {
        throw new Error('Identidade autenticada requer papel admin ou user');
    }
    if (canCheckoutForAnyEmail && role !== 'admin') {
        throw new Error('Apenas identidade admin pode operar checkout para qualquer e-mail');
    }

    const normalizedEmail = email === null ? null : normalizeEmail(email);
    if (!canCheckoutForAnyEmail && (!normalizedEmail || !normalizedEmail.includes('@'))) {
        throw new Error('Identidade autenticada requer um e-mail válido');
    }

    return Object.freeze({ role, email: normalizedEmail, canCheckoutForAnyEmail });
}

function assertCanCheckoutForEmail(identity, checkoutEmail) {
    if (!identity) {
        throw new AuthorizationError('Identidade autenticada é obrigatória para o checkout');
    }
    if (identity.role === 'admin' && identity.canCheckoutForAnyEmail === true) {
        return;
    }
    if (identity.role !== 'user') {
        throw new AuthorizationError('Identidade não autorizada para checkout');
    }
    if (normalizeEmail(identity.email) !== normalizeEmail(checkoutEmail)) {
        throw new AuthorizationError('Checkout permitido apenas para o e-mail da identidade autenticada');
    }
}

module.exports = { normalizeEmail, createAuthenticatedIdentity, assertCanCheckoutForEmail };
