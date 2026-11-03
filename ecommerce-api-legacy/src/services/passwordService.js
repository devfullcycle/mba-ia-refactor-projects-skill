// Hash de senha com scrypt (salt aleatório) usando apenas o módulo crypto nativo.
const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;
const SALT_BYTES = 16;
const PREFIX = 'scrypt';

async function hashPassword(password) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const derived = await scrypt(password, salt, KEY_LENGTH);
  return `${PREFIX}$${salt}$${derived.toString('hex')}`;
}

async function verifyPassword(password, stored) {
  const [prefix, salt, hash] = String(stored).split('$');
  if (prefix !== PREFIX || !salt || !hash) return false;
  const derived = await scrypt(password, salt, KEY_LENGTH);
  const expected = Buffer.from(hash, 'hex');
  return expected.length === derived.length && crypto.timingSafeEqual(derived, expected);
}

module.exports = { hashPassword, verifyPassword };
