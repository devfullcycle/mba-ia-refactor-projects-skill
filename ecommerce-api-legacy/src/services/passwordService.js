const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

// Hash forte com salt usando scrypt (nativo do Node, sem dependências extras).
// Substitui o `badCrypto` caseiro e inseguro.
module.exports = {
    async hash(password) {
        const salt = crypto.randomBytes(16).toString('hex');
        const derived = await scrypt(password, salt, 64);
        return `${salt}:${derived.toString('hex')}`;
    },

    async verify(password, stored) {
        const [salt, key] = stored.split(':');
        const derived = await scrypt(password, salt, 64);
        const keyBuffer = Buffer.from(key, 'hex');
        return keyBuffer.length === derived.length && crypto.timingSafeEqual(keyBuffer, derived);
    },
};
