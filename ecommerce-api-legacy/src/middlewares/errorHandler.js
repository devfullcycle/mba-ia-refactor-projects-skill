const { logError } = require('../utils/logger');

function notFound(req, res) {
  res.status(404).json({ error: 'Rota nao encontrada' });
}

function errorHandler(err, _req, res, _next) {
  const status = err.status || 500;
  if (status >= 500) logError(err);
  res.status(status).json({ error: err.message || 'Erro interno do servidor' });
}

module.exports = { notFound, errorHandler };
