'use strict';

const crypto = require('crypto');

const { UnauthorizedError } = require('../utils/errors');

/**
 * Autorização de rotas administrativas por chave de API (header `x-api-key`).
 *
 * Nega por default: se `ADMIN_API_KEY` não estiver configurada, a rota responde 401 em vez
 * de ficar aberta. No legado, `/api/admin/financial-report` e `DELETE /api/users/:id`
 * não tinham qualquer verificação.
 */
function createRequireAdmin({ adminApiKey, logger }) {
    return function requireAdmin(req, _res, next) {
        if (!adminApiKey) {
            logger.warn('Rota administrativa acessada sem ADMIN_API_KEY configurada', {
                path: req.originalUrl,
            });
            return next(new UnauthorizedError('Não autorizado'));
        }

        const provided = req.get('x-api-key') || '';
        const expected = Buffer.from(adminApiKey);
        const received = Buffer.from(provided);

        const autorizado =
            expected.length === received.length && crypto.timingSafeEqual(expected, received);

        if (!autorizado) {
            logger.warn('Tentativa de acesso administrativo não autorizada', {
                path: req.originalUrl,
            });
            return next(new UnauthorizedError('Não autorizado'));
        }
        return next();
    };
}

module.exports = { createRequireAdmin };
