// Express 4 não captura rejeições de handlers async: encaminha para o error handler.
module.exports = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};
