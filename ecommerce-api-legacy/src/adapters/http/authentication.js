'use strict';

const { AuthenticationError, AuthorizationError } = require('../../domain/errors');

/**
 * Autenticação por API key estática (header x-api-key) — decisão aprovada
 * pelo usuário para este desafio. Corrige F-003 (operações privilegiadas
 * e checkout sem identidade verificada).
 */
function authenticate(apiKeys) {
    return (req, _res, next) => {
        const key = req.header('x-api-key');
        const identity = key ? apiKeys.get(key) : null;
        if (!identity) {
            return next(new AuthenticationError('Credencial ausente ou inválida'));
        }
        req.auth = identity;
        next();
    };
}

function requireRole(role) {
    return (req, _res, next) => {
        if (!req.auth || req.auth.role !== role) {
            return next(new AuthorizationError(`Operação exige papel '${role}'`));
        }
        next();
    };
}

module.exports = { authenticate, requireRole };
