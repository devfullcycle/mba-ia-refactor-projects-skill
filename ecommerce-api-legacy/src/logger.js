// Logger simples e configurável — substitui console.log espalhado.
// Nunca deve receber dados sensíveis (cartões, segredos, senhas).
module.exports = {
    info: (...args) => console.log('[INFO]', ...args),
    error: (...args) => console.error('[ERROR]', ...args),
};
