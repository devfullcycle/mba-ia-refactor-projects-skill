const sqlite3 = require('sqlite3').verbose();

// Wrapper fino sobre o driver sqlite3 que expõe uma API baseada em Promises,
// eliminando o callback hell e permitindo async/await + transações explícitas.
class Database {
    constructor(path = ':memory:') {
        this.db = new sqlite3.Database(path);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.db.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    // Executa `work` dentro de uma transação atômica (commit no sucesso, rollback no erro).
    async transaction(work) {
        await this.exec('BEGIN');
        try {
            const result = await work();
            await this.exec('COMMIT');
            return result;
        } catch (err) {
            await this.exec('ROLLBACK');
            throw err;
        }
    }
}

module.exports = Database;
