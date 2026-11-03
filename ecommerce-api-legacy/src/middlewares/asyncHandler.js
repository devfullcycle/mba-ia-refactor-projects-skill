// Encaminha rejeições de handlers async para o middleware de erro (Express 4 não faz isso sozinho).
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

module.exports = asyncHandler;
