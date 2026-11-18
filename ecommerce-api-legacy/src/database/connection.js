const sqlite3 = require('sqlite3');

// Cria uma conexão SQLite com helpers baseados em Promise.
// Não há estado de módulo: cada chamada devolve uma instância independente.
function createDatabase(filename) {
    const raw = new sqlite3.Database(filename);

    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function (err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });

    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });

    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    // Transações são serializadas: uma conexão só suporta uma transação por vez.
    let queue = Promise.resolve();
    const transaction = (work) => {
        const result = queue.then(async () => {
            await run('BEGIN');
            try {
                const value = await work();
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };

    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    return { run, get, all, transaction, close };
}

module.exports = { createDatabase };
