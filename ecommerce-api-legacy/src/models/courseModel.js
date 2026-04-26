const { get, all } = require('../database/connection');

function findActiveById(db, id) {
  return get(db, 'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
}

function findAll(db) {
  return all(db, 'SELECT id, title, price, active FROM courses', []);
}

module.exports = { findActiveById, findAll };
