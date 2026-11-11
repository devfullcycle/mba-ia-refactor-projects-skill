const sqlite3 = require('sqlite3');
const config = require('./config');

const SCHEMA = [
    `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )`,
    `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        created_at DATETIME NOT NULL
    )`,
];

let db = null;
// Serializa transações na conexão única: o sqlite3 não suporta BEGIN aninhado/concorrente.
let transactionQueue = Promise.resolve();

function getDb() {
    if (!db) throw new Error('Banco não inicializado. Chame connect() antes.');
    return db;
}

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        getDb().run(sql, params, function onRun(err) {
            if (err) return reject(err);
            return resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        getDb().get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        getDb().all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

function transaction(work) {
    const result = transactionQueue.then(async () => {
        await run('BEGIN IMMEDIATE');
        try {
            const value = await work();
            await run('COMMIT');
            return value;
        } catch (err) {
            await run('ROLLBACK').catch(() => {});
            throw err;
        }
    });
    // Mantém a fila andando mesmo que esta transação falhe.
    transactionQueue = result.catch(() => {});
    return result;
}

async function connect(dbPath = config.dbPath) {
    db = await new Promise((resolve, reject) => {
        const conn = new sqlite3.Database(dbPath, (err) => (err ? reject(err) : resolve(conn)));
    });
    await run('PRAGMA foreign_keys = ON');
    for (const statement of SCHEMA) {
        await run(statement);
    }
    return db;
}

function close() {
    return new Promise((resolve, reject) => {
        if (!db) return resolve();
        const conn = db;
        db = null;
        return conn.close((err) => (err ? reject(err) : resolve()));
    });
}

module.exports = { connect, close, run, get, all, transaction };
