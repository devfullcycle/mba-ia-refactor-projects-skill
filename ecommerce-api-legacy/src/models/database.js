const sqlite3 = require('sqlite3').verbose();
const { hashPassword } = require('../utils/security');

class Database {
    constructor() {
        this.db = null;
    }

    connect(dbPath = ':memory:') {
        if (!this.db) {
            this.db = new sqlite3.Database(dbPath);
        }
        return this.db;
    }

    getDb() {
        if (!this.db) {
            return this.connect();
        }
        return this.db;
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.getDb().run(sql, params, function (err) {
                if (err) {
                    return reject(err);
                }
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.getDb().get(sql, params, (err, row) => {
                if (err) {
                    return reject(err);
                }
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.getDb().all(sql, params, (err, rows) => {
                if (err) {
                    return reject(err);
                }
                resolve(rows);
            });
        });
    }

    async initDb() {
        const db = this.getDb();

        return new Promise((resolve, reject) => {
            db.serialize(async () => {
                try {
                    await this.run("PRAGMA foreign_keys = ON;");

                    await this.run(`
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            pass TEXT NOT NULL
                        )
                    `);

                    await this.run(`
                        CREATE TABLE IF NOT EXISTS courses (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            price REAL NOT NULL,
                            active INTEGER NOT NULL DEFAULT 1
                        )
                    `);

                    await this.run(`
                        CREATE TABLE IF NOT EXISTS enrollments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            course_id INTEGER NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
                        )
                    `);

                    await this.run(`
                        CREATE TABLE IF NOT EXISTS payments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            enrollment_id INTEGER NOT NULL,
                            amount REAL NOT NULL,
                            status TEXT NOT NULL,
                            FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
                        )
                    `);

                    await this.run(`
                        CREATE TABLE IF NOT EXISTS audit_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            action TEXT NOT NULL,
                            created_at DATETIME NOT NULL
                        )
                    `);

                    // Seeds com hash seguro
                    const existingUser = await this.get("SELECT id FROM users WHERE email = ?", ['leonan@fullcycle.com.br']);
                    if (!existingUser) {
                        const seedPassHash = hashPassword('123');
                        await this.run(
                            "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
                            ['Leonan', 'leonan@fullcycle.com.br', seedPassHash]
                        );
                        await this.run(
                            "INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)",
                            ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]
                        );
                        await this.run(
                            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
                            [1, 1]
                        );
                        await this.run(
                            "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
                            [1, 997.00, 'PAID']
                        );
                    }

                    resolve();
                } catch (error) {
                    reject(error);
                }
            });
        });
    }

    close() {
        return new Promise((resolve, reject) => {
            if (this.db) {
                this.db.close((err) => {
                    if (err) return reject(err);
                    this.db = null;
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }
}

const databaseInstance = new Database();
module.exports = databaseInstance;
