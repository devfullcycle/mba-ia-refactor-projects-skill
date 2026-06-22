const Database = require('better-sqlite3')
const bcrypt = require('bcrypt')
const { dbPath } = require('../config/settings')

const db = new Database(dbPath)
db.pragma('journal_mode = WAL')

function initSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT DEFAULT 'student'
    );
    CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      price REAL NOT NULL,
      active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS enrollments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      course_id INTEGER NOT NULL REFERENCES courses(id)
    );
    CREATE TABLE IF NOT EXISTS payments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
      amount REAL NOT NULL,
      status TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      action TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `)

  const count = db.prepare('SELECT COUNT(*) AS n FROM courses').get()
  if (count.n === 0) {
    const SALT_ROUNDS = 10
    const hash = bcrypt.hashSync('123', SALT_ROUNDS)
    db.prepare('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)').run(
      'Leonan', 'leonan@fullcycle.com.br', hash, 'admin'
    )
    db.prepare("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)").run()
    db.prepare("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)").run()
    db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)').run()
    db.prepare("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')").run()
  }
}

module.exports = { db, initSchema }
