/**
 * Middleware de autenticação para rotas administrativas.
 * Protege endpoints sensíveis (relatório financeiro) exigindo token de admin.
 */
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || null;

function requireAdmin(req, res, next) {
    // Em produção o ADMIN_TOKEN deve existir via env; sem ele, nega por padrão.
    if (!ADMIN_TOKEN) {
        return res.status(403).json({ error: 'Acesso administrativo não configurado' });
    }
    const token = req.headers['x-admin-token'] || req.query.token;
    if (token !== ADMIN_TOKEN) {
        return res.status(401).json({ error: 'Não autorizado' });
    }
    next();
}

module.exports = { requireAdmin };