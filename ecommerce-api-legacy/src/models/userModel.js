const { run, get } = require('../db');
const { hashPassword } = require('../utils/hash');

const findByEmail = (email) =>
  get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);

const findById = (id) =>
  get('SELECT id, name, email FROM users WHERE id = ?', [id]);

const create = async (name, email, plainPassword) => {
  const hash = await hashPassword(plainPassword);
  const res = await run(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    [name, email, hash]
  );
  return res.lastID;
};

module.exports = { findByEmail, findById, create };
