const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;

// Hash de senha com scrypt + salt aleatório (stdlib do Node), formato `scrypt$<salt>$<hash>`.
class PasswordHasher {
    async hash(password) {
        const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
        const derived = await scrypt(password, salt, KEY_LENGTH);
        return `scrypt$${salt}$${derived.toString('hex')}`;
    }
}

module.exports = PasswordHasher;
