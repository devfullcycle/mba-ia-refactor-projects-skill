const crypto = require('crypto');
const config = require('../config/config');
const { ForbiddenError, UnauthorizedError } = require('../utils/errors');

function digest(value) {
    return crypto.createHash('sha256').update(String(value)).digest();
}

// Protege rotas administrativas com o header X-Admin-Token (valor de ADMIN_TOKEN).
// Sem ADMIN_TOKEN configurado, as rotas ficam desabilitadas (fail-closed).
function requireAdminToken(req, res, next) {
    if (!config.adminToken) {
        return next(new ForbiddenError('Endpoint administrativo desabilitado'));
    }
    const received = req.get('X-Admin-Token') || '';
    if (!crypto.timingSafeEqual(digest(received), digest(config.adminToken))) {
        return next(new UnauthorizedError('Token administrativo inválido'));
    }
    return next();
}

module.exports = { requireAdminToken };
