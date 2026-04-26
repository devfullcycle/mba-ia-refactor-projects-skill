const { run, get } = require('../database/connection');
const bcrypt = require('bcryptjs');

function findByEmail(db, email) {
  return get(db, 'SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
}

function findById(db, id) {
  return get(db, 'SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function create(db, name, email, plainPassword) {
  const hash = await bcrypt.hash(plainPassword, 10);
  const result = await run(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, hash]);
  return { id: result.lastID, name, email };
}

function deleteById(db, id) {
  return run(db, 'DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, findById, create, deleteById };
