// Express 4 não encaminha rejeições de handlers assíncronos ao tratador de erros.
const asyncHandler = handler => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = asyncHandler;
