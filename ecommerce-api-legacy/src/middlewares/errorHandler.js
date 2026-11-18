// Tratamento central de erros, formato uniforme: { "error": "..." }.
// eslint-disable-next-line no-unused-vars
module.exports = (err, req, res, next) => {
    const status = err.status || 500;
    if (status >= 500) console.error(err);
    res.status(status).json({ error: status >= 500 ? 'Erro interno' : err.message });
};
