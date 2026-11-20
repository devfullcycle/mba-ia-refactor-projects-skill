const sqlite3 = require('sqlite3');

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
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        created_at DATETIME NOT NULL
    )`,
];

// Wrapper promisificado sobre o driver sqlite3 (callback API).
class Database {
    constructor(connection) {
        this.connection = connection;
        this.transactionQueue = Promise.resolve();
    }

    static open(path, { verbose = false } = {}) {
        const driver = verbose ? sqlite3.verbose() : sqlite3;
        return new Promise((resolve, reject) => {
            const connection = new driver.Database(path, (err) => {
                if (err) return reject(err);
                resolve(new Database(connection));
            });
        });
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    // Executa `work` dentro de BEGIN/COMMIT, com ROLLBACK em caso de erro.
    // As transações são serializadas, pois todas compartilham a mesma conexão.
    transaction(work) {
        const result = this.transactionQueue.then(async () => {
            await this.run('BEGIN IMMEDIATE');
            try {
                const value = await work();
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        this.transactionQueue = result.catch(() => {});
        return result;
    }

    async initSchema() {
        await this.run('PRAGMA foreign_keys = ON');
        for (const statement of SCHEMA) {
            await this.run(statement);
        }
    }

    close() {
        return new Promise((resolve, reject) => {
            this.connection.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = Database;
