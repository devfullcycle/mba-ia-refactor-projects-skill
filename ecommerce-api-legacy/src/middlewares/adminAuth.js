const crypto = require('crypto');
const { ForbiddenError } = require('../controllers/errors');

const ADMIN_TOKEN_HEADER = 'x-admin-token';

const digest = (value) => crypto.createHash('sha256').update(value).digest();

// Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, as rotas ficam bloqueadas.
function requireAdmin(adminToken) {
    return (req, res, next) => {
        const provided = req.get(ADMIN_TOKEN_HEADER) || '';
        const authorized = adminToken !== '' && crypto.timingSafeEqual(digest(provided), digest(adminToken));
        next(authorized ? undefined : new ForbiddenError());
    };
}

module.exports = { requireAdmin };
