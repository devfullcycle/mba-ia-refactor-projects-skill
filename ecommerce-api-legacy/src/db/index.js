const sqlite3 = require('sqlite3');
const { hashPassword } = require('../utils/hash');
const { log } = require('../utils/logger');

let db = null;

function getDb() {
  if (!db) {
    db = new sqlite3.Database(process.env.DB_PATH || ':memory:');
  }
  return db;
}

const run = (sql, params = []) =>
  new Promise((resolve, reject) => {
    getDb().run(sql, params, function (err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
    });
  });

const get = (sql, params = []) =>
  new Promise((resolve, reject) => {
    getDb().get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });

const all = (sql, params = []) =>
  new Promise((resolve, reject) => {
    getDb().all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });

const exec = (sql) =>
  new Promise((resolve, reject) => {
    getDb().exec(sql, (err) => (err ? reject(err) : resolve()));
  });

const SCHEMA = `
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

async function initDb() {
  await exec(SCHEMA);
  const count = await get('SELECT COUNT(*) AS n FROM users');
  if (count.n === 0) {
    const adminHash = await hashPassword('123');
    await run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
      'Leonan',
      'leonan@fullcycle.com.br',
      adminHash,
    ]);
    await run(
      'INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
      ['Clean Architecture', 997.0, 1, 'Docker', 497.0, 1]
    );
    await run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await run(
      "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
      [1, 997.0, 'PAID']
    );
    log('Banco inicializado e populado.');
  }
}

module.exports = { getDb, run, get, all, exec, initDb };
