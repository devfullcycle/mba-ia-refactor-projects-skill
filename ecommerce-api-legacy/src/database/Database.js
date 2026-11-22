const sqlite3 = require('sqlite3');

// Adaptador de promessas sobre o driver sqlite3 (baseado em callbacks).
class Database {
    constructor(filename) {
        this.connection = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastId: this.lastID, changes: this.changes });
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

    close() {
        return new Promise((resolve, reject) => {
            this.connection.close(err => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = Database;
