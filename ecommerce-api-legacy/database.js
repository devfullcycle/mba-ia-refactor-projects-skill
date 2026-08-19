const sqlite3 = require('sqlite3').verbose();

// Centralized SQLite connection in memory
const db = new sqlite3.Database(':memory:');

const initDb = () => {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, pass TEXT)", (err) => {
                if (err) return reject(err);
            });
            db.run("CREATE TABLE courses (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL, active INTEGER)");
            db.run("CREATE TABLE enrollments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, course_id INTEGER)");
            db.run("CREATE TABLE payments (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_id INTEGER, amount REAL, status TEXT)");
            db.run("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, created_at DATETIME)");
            
            db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
            db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
            db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
            db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')", () => {
                resolve(db);
            });
        });
    });
};

// Promisified database helpers to eliminate Callback Hell
const dbGet = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
};

const dbAll = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
};

const dbRun = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function(err) {
            if (err) reject(err);
            else resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
};

module.exports = { db, initDb, dbGet, dbAll, dbRun };
