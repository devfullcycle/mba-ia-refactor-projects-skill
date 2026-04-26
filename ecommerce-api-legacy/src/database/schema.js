const { run } = require('./connection');
const bcrypt = require('bcryptjs');

async function initializeSchema(db) {
  await run(db, `CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)`);
  await run(db, `CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)`);
  await run(db, `CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)`);
  await run(db, `CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)`);
  await run(db, `CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)`);
}

async function seedData(db) {
  const hash = await bcrypt.hash('123', 10);

  await run(db, `INSERT INTO users (name, email, pass) VALUES (?, ?, ?)`, ['Leonan', 'leonan@fullcycle.com.br', hash]);
  await run(db, `INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)`, ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]);
  await run(db, `INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)`, [1, 1]);
  await run(db, `INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)`, [1, 997.00, 'PAID']);
}

module.exports = { initializeSchema, seedData };
