const jwt = require('jsonwebtoken')
const { secret } = require('../config/settings')

function requireAdmin(req, res, next) {
  const token = (req.headers.authorization || '').replace('Bearer ', '')
  if (!token) {
    return res.status(401).json({ error: 'Token de autenticação obrigatório' })
  }
  try {
    const payload = jwt.verify(token, secret)
    if (payload.role !== 'admin') {
      return res.status(403).json({ error: 'Acesso negado — requer perfil admin' })
    }
    req.user = payload
    next()
  } catch {
    res.status(401).json({ error: 'Token inválido ou expirado' })
  }
}

module.exports = { requireAdmin }
