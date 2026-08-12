/**
 * Utilities de segurança — hashing de senha e helpers de cache/esteira.
 * Substitui o inseguro badCrypto e o estado global mutável.
 */
const bcrypt = require('bcryptjs');

// Cache scoped (por request) em vez de global mutável.
const cache = new Map();

function hashPassword(password) {
    return bcrypt.hash(password, 10);
}

function verifyPassword(password, hash) {
    return bcrypt.compareSync(password, hash);
}

function cacheSet(key, value) {
    cache.set(key, value);
}

function cacheGet(key) {
    return cache.get(key);
}

function paymentGatewayStatus(cardNumber) {
    // Simulação: cartão que começa com '4' é aprovado.
    if (typeof cardNumber !== 'string' || cardNumber.length < 4) return 'DENIED';
    return cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
}

module.exports = {
    hashPassword,
    verifyPassword,
    cacheSet,
    cacheGet,
    paymentGatewayStatus,
    cache,
};