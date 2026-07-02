const env = require('../config/env');

function adminAuth(req, res, next) {
    const providedKey = req.header('x-admin-key');

    if (providedKey !== env.adminApiKey) {
        return res.status(401).json({ error: 'Não autorizado' });
    }

    next();
}

module.exports = adminAuth;
