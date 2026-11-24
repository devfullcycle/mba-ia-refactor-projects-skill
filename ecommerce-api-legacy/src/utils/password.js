const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;
const SALT_BYTES = 16;

// Formato armazenado: "<salt hex>:<hash hex>"
async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const key = await scrypt(password, salt, KEY_LENGTH);
    return `${salt}:${key.toString('hex')}`;
}

async function verifyPassword(password, stored) {
    const [salt, hash] = stored.split(':');
    const key = await scrypt(password, salt, KEY_LENGTH);
    const expected = Buffer.from(hash, 'hex');
    return expected.length === key.length && crypto.timingSafeEqual(key, expected);
}

module.exports = { hashPassword, verifyPassword };
