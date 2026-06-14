function errorHandler(err, req, res, next) {
    const status = err.status || 500
    if (status >= 500) {
        console.error('[ERROR]', err)
    }
    res.status(status).json({ error: status < 500 ? err.message : 'Internal server error' })
}

module.exports = errorHandler
