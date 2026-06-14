const config = require('../config/settings')

function requireAdminAuth(req, res, next) {
    const apiKey = req.headers['x-admin-api-key']
    if (!apiKey || apiKey !== config.adminApiKey) {
        return res.status(401).json({ error: 'Unauthorized — x-admin-api-key header required' })
    }
    next()
}

module.exports = { requireAdminAuth }
