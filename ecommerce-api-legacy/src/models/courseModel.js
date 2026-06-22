const { db } = require('../database/connection')

function findById(id) {
  return db.prepare('SELECT * FROM courses WHERE id = ? AND active = 1').get(id)
}

function findAll() {
  return db.prepare('SELECT * FROM courses WHERE active = 1').all()
}

module.exports = { findById, findAll }
