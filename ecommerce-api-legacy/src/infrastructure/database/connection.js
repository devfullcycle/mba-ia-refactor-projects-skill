'use strict';

const { DatabaseSync } = require('node:sqlite');

const SCHEMA = `
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    );
    CREATE TABLE courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        course_id INTEGER NOT NULL REFERENCES courses(id)
    );
    CREATE TABLE payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
        amount REAL NOT NULL,
        status TEXT NOT NULL
    );
    CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
`;

/**
 * Cria e devolve uma conexão node:sqlite (substitui o driver deprecated
 * sqlite3, ver F-011), com schema aplicado e utilitário de transação.
 * Ciclo de vida é responsabilidade de quem cria (bootstrap ou testes),
 * nunca um singleton implícito (F-008).
 */
function createConnection({ location = ':memory:' } = {}) {
    const db = new DatabaseSync(location);
    db.exec('PRAGMA foreign_keys = ON');
    db.exec(SCHEMA);

    return {
        raw: db,
        prepare: (sql) => db.prepare(sql),
        transaction(work) {
            db.exec('BEGIN');
            try {
                const result = work();
                db.exec('COMMIT');
                return result;
            } catch (error) {
                db.exec('ROLLBACK');
                throw error;
            }
        },
        close() {
            db.close();
        },
    };
}

module.exports = { createConnection };
