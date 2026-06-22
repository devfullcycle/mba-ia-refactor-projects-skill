const { db } = require('../database/connection')
const bcrypt = require('bcrypt')

const SALT_ROUNDS = 10

function findByEmail(email) {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email)
}

function findById(id) {
  return db.prepare('SELECT id, name, email, role FROM users WHERE id = ?').get(id)
}

function create(name, email, password, role = 'student') {
  const password_hash = bcrypt.hashSync(password, SALT_ROUNDS)
  const result = db.prepare(
    'INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)'
  ).run(name, email, password_hash, role)
  return result.lastInsertRowid
}

function verifyPassword(plainText, hash) {
  return bcrypt.compareSync(plainText, hash)
}

function deleteById(id) {
  db.prepare('DELETE FROM users WHERE id = ?').run(id)
}

module.exports = { findByEmail, findById, create, verifyPassword, deleteById }
