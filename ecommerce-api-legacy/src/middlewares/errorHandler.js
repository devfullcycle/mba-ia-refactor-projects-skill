function errorHandler(err, req, res, next) {
  console.error('[ERROR]', err.message, err.stack)
  const status = err.status || 500
  res.status(status).json({ error: err.message || 'Erro interno do servidor' })
}

module.exports = { errorHandler }
