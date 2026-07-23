'use strict';

function createUserRepository(connection) {
    return {
        findByEmail(email) {
            return connection.prepare('SELECT id, name, email, password_hash FROM users WHERE email = ?').get(email) || null;
        },
        findById(id) {
            return connection.prepare('SELECT id, name, email, password_hash FROM users WHERE id = ?').get(id) || null;
        },
        create({ name, email, passwordHash }, tx = connection) {
            const info = tx.prepare('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)').run(name, email, passwordHash);
            return { id: Number(info.lastInsertRowid), name, email };
        },
        delete(id, tx = connection) {
            const info = tx.prepare('DELETE FROM users WHERE id = ?').run(id);
            return info.changes > 0;
        },
    };
}

module.exports = { createUserRepository };
