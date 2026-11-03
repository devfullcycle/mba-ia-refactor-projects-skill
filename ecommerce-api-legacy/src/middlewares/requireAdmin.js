// Protege endpoints administrativos/destrutivos com token configurado via ADMIN_TOKEN.
const crypto = require('crypto');
const { ForbiddenError, UnauthorizedError } = require('../utils/errors');

const ADMIN_TOKEN_HEADER = 'x-admin-token';

function safeEqual(a, b) {
  const left = Buffer.from(String(a));
  const right = Buffer.from(String(b));
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function createRequireAdmin(adminToken) {
  return function requireAdmin(req, res, next) {
    if (!adminToken) return next(new ForbiddenError('Endpoint administrativo desabilitado (defina ADMIN_TOKEN)'));
    if (!safeEqual(req.get(ADMIN_TOKEN_HEADER) || '', adminToken)) {
      return next(new UnauthorizedError('Token administrativo inválido'));
    }
    return next();
  };
}

module.exports = { createRequireAdmin };
