const crypto = require('crypto');

/**
 * Cria hash criptograficamente seguro para senhas utilizando PBKDF2 com Salt aleatório
 * @param {string} password 
 * @returns {string} salt:hash
 */
function hashPassword(password) {
    const rawPassword = password || crypto.randomBytes(8).toString('hex');
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.pbkdf2Sync(rawPassword, salt, 10000, 64, 'sha512').toString('hex');
    return `${salt}:${hash}`;
}

/**
 * Verifica se a senha fornecida corresponde ao hash armazenado
 * @param {string} password 
 * @param {string} storedHash 
 * @returns {boolean}
 */
function verifyPassword(password, storedHash) {
    if (!password || !storedHash || !storedHash.includes(':')) {
        return false;
    }
    const [salt, originalHash] = storedHash.split(':');
    const hash = crypto.pbkdf2Sync(password, salt, 10000, 64, 'sha512').toString('hex');
    return crypto.timingSafeEqual(Buffer.from(hash), Buffer.from(originalHash));
}

/**
 * Mascara o número do cartão de crédito preservando apenas os últimos 4 dígitos
 * para conformidade com PCI-DSS e proteção de dados sensíveis em logs.
 * @param {string} cardNumber 
 * @returns {string}
 */
function maskCardNumber(cardNumber) {
    if (!cardNumber || typeof cardNumber !== 'string') {
        return '****';
    }
    const clean = cardNumber.replace(/\s+/g, '');
    if (clean.length <= 4) {
        return '****';
    }
    const last4 = clean.slice(-4);
    return `**** **** **** ${last4}`;
}

module.exports = {
    hashPassword,
    verifyPassword,
    maskCardNumber
};
