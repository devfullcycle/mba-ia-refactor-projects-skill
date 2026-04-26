function errorHandler(err, req, res, _next) {
  console.error('[ERROR]', err.message || err);

  const statusCode = err.statusCode || 500;
  const message = err.expose ? err.message : 'Internal server error';

  res.status(statusCode).json({
    error: {
      code: statusCode,
      message,
    },
  });
}

class AppError extends Error {
  constructor(message, statusCode = 500, expose = false) {
    super(message);
    this.statusCode = statusCode;
    this.expose = expose;
  }
}

module.exports = { errorHandler, AppError };
