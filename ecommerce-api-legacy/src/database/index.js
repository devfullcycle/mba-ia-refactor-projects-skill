const sqlite3 = require('sqlite3').verbose()
const bcrypt = require('bcryptjs')
const config = require('../config/settings')

let dbInstance

function getDb() {
    if (!dbInstance) {
        dbInstance = new sqlite3.Database(config.dbPath)

        dbInstance.getAsync = (sql, params = []) =>
            new Promise((resolve, reject) =>
                dbInstance.get(sql, params, (err, row) => err ? reject(err) : resolve(row))
            )

        dbInstance.allAsync = (sql, params = []) =>
            new Promise((resolve, reject) =>
                dbInstance.all(sql, params, (err, rows) => err ? reject(err) : resolve(rows))
            )

        dbInstance.runAsync = (sql, params = []) =>
            new Promise((resolve, reject) =>
                dbInstance.run(sql, params, function(err) {
                    err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes })
                })
            )
    }
    return dbInstance
}

async function initDb() {
    const db = getDb()

    await db.runAsync(`CREATE TABLE IF NOT EXISTS users (
        id    INTEGER PRIMARY KEY,
        name  TEXT    NOT NULL,
        email TEXT    UNIQUE NOT NULL,
        pass  TEXT    NOT NULL
    )`)
    await db.runAsync(`CREATE TABLE IF NOT EXISTS courses (
        id     INTEGER PRIMARY KEY,
        title  TEXT    NOT NULL,
        price  REAL    NOT NULL,
        active INTEGER DEFAULT 1
    )`)
    await db.runAsync(`CREATE TABLE IF NOT EXISTS enrollments (
        id        INTEGER PRIMARY KEY,
        user_id   INTEGER NOT NULL REFERENCES users(id),
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )`)
    await db.runAsync(`CREATE TABLE IF NOT EXISTS payments (
        id            INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
        amount        REAL    NOT NULL,
        status        TEXT    NOT NULL
    )`)
    await db.runAsync(`CREATE TABLE IF NOT EXISTS audit_logs (
        id         INTEGER PRIMARY KEY,
        action     TEXT    NOT NULL,
        created_at DATETIME DEFAULT (datetime('now'))
    )`)

    const existing = await db.getAsync("SELECT id FROM users WHERE email = ?", ['leonan@fullcycle.com.br'])
    if (!existing) {
        const hash = await bcrypt.hash('123456', 10)
        await db.runAsync("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", ['Leonan', 'leonan@fullcycle.com.br', hash])
        await db.runAsync("INSERT INTO courses (id, title, price, active) VALUES (1, 'Clean Architecture', 997.00, 1)")
        await db.runAsync("INSERT INTO courses (id, title, price, active) VALUES (2, 'Docker', 497.00, 1)")
        const { lastID: enrollmentId } = await db.runAsync("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)")
        await db.runAsync("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, 997.00, 'PAID')", [enrollmentId])
    }
}

module.exports = { getDb, initDb }
