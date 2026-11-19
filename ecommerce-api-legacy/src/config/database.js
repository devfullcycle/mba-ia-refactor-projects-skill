const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');

/**
 * Wrapper Promise em torno do sqlite3 (elimina a API legada de callbacks).
 * `run` resolve com { lastID, changes }.
 */
class Database {
    constructor(path) {
        this._db = new sqlite3.Database(path);
        this.get = promisify(this._db.get.bind(this._db));
        this.all = promisify(this._db.all.bind(this._db));
        this._exec = promisify(this._db.exec.bind(this._db));
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this._db.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    exec(sql) {
        return this._exec(sql);
    }
}

/** Cria o schema e popula dados iniciais (senha com hash forte). */
async function initSchema(db, passwordService) {
    await db.exec(`
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
        CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
        CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
        CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
        CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
    `);

    const row = await db.get('SELECT COUNT(*) AS c FROM users');
    if (row.c === 0) {
        const hash = await passwordService.hash('123');
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', hash]);
        await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
    }
}

module.exports = { Database, initSchema };
