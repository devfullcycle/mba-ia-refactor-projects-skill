const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const FORMAT = 'scrypt';

// Hash de senha com scrypt (módulo crypto nativo do Node), com sal por senha. Formato: scrypt$<sal>$<hash>.
const passwordService = {
    async hash(password) {
        const salt = crypto.randomBytes(SALT_BYTES);
        const derived = await scrypt(password, salt, KEY_LENGTH);
        return `${FORMAT}$${salt.toString('hex')}$${derived.toString('hex')}`;
    },

    async verify(password, stored) {
        const [format, saltHex, hashHex] = String(stored).split('$');
        if (format !== FORMAT || !saltHex || !hashHex) return false;

        const expected = Buffer.from(hashHex, 'hex');
        const derived = await scrypt(password, Buffer.from(saltHex, 'hex'), expected.length);
        return crypto.timingSafeEqual(derived, expected);
    }
};

module.exports = passwordService;
