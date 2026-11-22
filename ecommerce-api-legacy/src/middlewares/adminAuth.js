const crypto = require('crypto');
const AppError = require('../errors/AppError');

const ADMIN_TOKEN_HEADER = 'x-admin-token';

const digest = value => crypto.createHash('sha256').update(String(value)).digest();

// Protege rotas administrativas/destrutivas. Sem ADMIN_TOKEN configurado, todas são recusadas.
function createAdminAuth(adminToken) {
    return function adminAuth(req, res, next) {
        if (!adminToken) return next(new AppError('Forbidden', 403));

        const provided = req.get(ADMIN_TOKEN_HEADER);
        if (!provided || !crypto.timingSafeEqual(digest(provided), digest(adminToken))) {
            return next(new AppError('Unauthorized', 401));
        }
        next();
    };
}

module.exports = createAdminAuth;
