const crypto = require('crypto');
const { UnauthorizedError } = require('../utils/errors');

// Exige o header `x-admin-token` igual ao token configurado.
module.exports = (adminToken) => (req, res, next) => {
    const provided = Buffer.from(String(req.get('x-admin-token') || ''));
    const expected = Buffer.from(adminToken);
    const valid = provided.length === expected.length && crypto.timingSafeEqual(provided, expected);
    next(valid ? undefined : new UnauthorizedError());
};
