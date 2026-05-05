const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');
const { hashPassword } = require('./password');

function openDatabase(path = ':memory:') {
  const db = new sqlite3.Database(path);

  const get = promisify(db.get.bind(db));
  const all = promisify(db.all.bind(db));

  function run(sql, params = []) {
    return new Promise((resolve, reject) => {
      db.run(sql, params, function onRun(err) {
        if (err) reject(err);
        else resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  return { db, run, get, all };
}

async function initDb(conn) {
  const { run } = conn;
  await run(`CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)`);
  await run(`CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)`);
  await run(`CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)`);
  await run(`CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)`);
  await run(`CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)`);
  const seedHash = hashPassword('123');
  await run(`INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', ?)`, [seedHash]);
  await run(
    `INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)`
  );
  await run(`INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)`);
  await run(`INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')`);
}

module.exports = { openDatabase, initDb };
