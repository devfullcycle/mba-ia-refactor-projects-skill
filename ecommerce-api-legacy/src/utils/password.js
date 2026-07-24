'use strict';

/**
 * Hash de senha com scrypt (KDF do módulo `crypto` nativo) e salt por usuário.
 *
 * Substitui o `badCrypto` do legado, que concatenava base64 em laço de 10.000
 * iterações, truncava em 10 caracteres e não usava salt.
 */

const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

const SALT_BYTES = 16;
const KEY_BYTES = 64;
const FORMAT_VERSION = 'scrypt';

async function hashPassword(plain) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const derived = await scrypt(plain, salt, KEY_BYTES);
    return `${FORMAT_VERSION}$${salt.toString('hex')}$${derived.toString('hex')}`;
}

async function verifyPassword(plain, stored) {
    if (typeof stored !== 'string') return false;
    const [version, saltHex, hashHex] = stored.split('$');
    if (version !== FORMAT_VERSION || !saltHex || !hashHex) return false;

    const derived = await scrypt(plain, Buffer.from(saltHex, 'hex'), KEY_BYTES);
    const expected = Buffer.from(hashHex, 'hex');
    if (expected.length !== derived.length) return false;
    return crypto.timingSafeEqual(derived, expected);
}

module.exports = { hashPassword, verifyPassword };
