'use strict';

const { ValidationError } = require('./errors');

/**
 * Model de domínio: representa estado e invariantes, sem conhecer
 * protocolo externo (guideline "Models").
 */
function createUser({ id = null, name, email, passwordHash }) {
    if (!name || typeof name !== 'string') {
        throw new ValidationError('Nome é obrigatório');
    }
    if (!email || typeof email !== 'string' || !email.includes('@')) {
        throw new ValidationError('E-mail é inválido');
    }
    return Object.freeze({ id, name, email, passwordHash });
}

function toPublicUser(user) {
    return { id: user.id, name: user.name, email: user.email };
}

module.exports = { createUser, toPublicUser };
