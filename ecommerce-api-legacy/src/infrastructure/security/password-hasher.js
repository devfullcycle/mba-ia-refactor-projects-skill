'use strict';

const crypto = require('node:crypto');

/**
 * Hash adaptativo com salt (scrypt), substituindo a transformação
 * reversível/determinística encontrada em F-004.
 */
const SALT_BYTES = 16;
const KEY_LENGTH = 64;

function createPasswordHasher() {
    return {
        hash(rawPassword) {
            if (typeof rawPassword !== 'string' || rawPassword.length === 0) {
                throw new Error('Senha inválida para hashing');
            }
            const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
            const derived = crypto.scryptSync(rawPassword, salt, KEY_LENGTH).toString('hex');
            return `scrypt$${salt}$${derived}`;
        },
        verify(passwordHash, candidate) {
            if (typeof passwordHash !== 'string' || typeof candidate !== 'string') return false;
            const parts = passwordHash.split('$');
            if (parts.length !== 3 || parts[0] !== 'scrypt') return false;
            const [, salt, expected] = parts;
            const actual = crypto.scryptSync(candidate, salt, KEY_LENGTH).toString('hex');
            const expectedBuffer = Buffer.from(expected, 'hex');
            const actualBuffer = Buffer.from(actual, 'hex');
            if (expectedBuffer.length !== actualBuffer.length) return false;
            return crypto.timingSafeEqual(expectedBuffer, actualBuffer);
        },
    };
}

module.exports = { createPasswordHasher };
