const config = require('../config');
const AppError = require('../errors/AppError');

// Protege rotas administrativas/destrutivas. Exige o header x-admin-token válido.
module.exports = function requireAdmin(req, res, next) {
    const token = req.get('x-admin-token');
    if (!token || token !== config.adminToken) {
        return next(new AppError('Unauthorized', 401));
    }
    next();
};
