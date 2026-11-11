// Encaminha rejeições de handlers async para o middleware de erro (Express 4 não faz isso sozinho).
module.exports = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};
