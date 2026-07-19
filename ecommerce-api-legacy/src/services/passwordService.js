const crypto = require('crypto');

// Hashing forte com salt usando scrypt (KDF nativo do Node, resistente a brute-force).
// Formato armazenado: "<salt-hex>:<hash-hex>". Substitui o antigo badCrypto inseguro.
const KEY_LENGTH = 64;

function hash(password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derived = crypto.scryptSync(String(password), salt, KEY_LENGTH).toString('hex');
    return `${salt}:${derived}`;
}

function verify(password, stored) {
    if (!stored || !stored.includes(':')) return false;
    const [salt, expected] = stored.split(':');
    const derived = crypto.scryptSync(String(password), salt, KEY_LENGTH).toString('hex');
    const a = Buffer.from(derived, 'hex');
    const b = Buffer.from(expected, 'hex');
    return a.length === b.length && crypto.timingSafeEqual(a, b);
}

module.exports = { hash, verify };
