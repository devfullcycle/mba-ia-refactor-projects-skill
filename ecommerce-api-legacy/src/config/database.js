const sqlite3 = require('sqlite3').verbose();

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function callback(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

function createDatabase() {
    const raw = new sqlite3.Database(':memory:');
    return {
        run: (sql, params) => run(raw, sql, params),
        get: (sql, params) => get(raw, sql, params),
        all: (sql, params) => all(raw, sql, params),
    };
}

module.exports = { createDatabase };
