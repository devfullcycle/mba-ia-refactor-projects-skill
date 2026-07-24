'use strict';

/**
 * Conexão com o banco e fronteira transacional.
 *
 * O driver sqlite3 é baseado em callback; aqui ele é promisificado uma única vez, para que
 * as camadas acima usem `async/await` (o legado empilhava 5 níveis de callback).
 */

const sqlite3 = require('sqlite3');

function createConnection(config) {
    const db = new sqlite3.Database(config.database.file);
    db.run('PRAGMA foreign_keys = ON');

    return {
        raw: db,

        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
            });
        },

        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows || [])));
            });
        },

        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                db.run(sql, params, function onDone(err) {
                    if (err) return reject(err);
                    resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },

        exec(sql) {
            return new Promise((resolve, reject) => {
                db.exec(sql, (err) => (err ? reject(err) : resolve()));
            });
        },

        close() {
            return new Promise((resolve, reject) => {
                db.close((err) => (err ? reject(err) : resolve()));
            });
        },
    };
}

/**
 * Executa `work` em uma transação: COMMIT no sucesso, ROLLBACK em qualquer falha.
 */
async function withTransaction(connection, work) {
    await connection.run('BEGIN');
    try {
        const result = await work();
        await connection.run('COMMIT');
        return result;
    } catch (error) {
        await connection.run('ROLLBACK');
        throw error;
    }
}

module.exports = { createConnection, withTransaction };
