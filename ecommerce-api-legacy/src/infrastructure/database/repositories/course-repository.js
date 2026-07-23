'use strict';

function createCourseRepository(connection) {
    return {
        findActiveById(id) {
            return connection.prepare('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1').get(id) || null;
        },
        listAll() {
            return connection.prepare('SELECT id, title, price, active FROM courses').all();
        },
        create({ title, price, active = 1 }, tx = connection) {
            const info = tx.prepare('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)').run(title, price, active);
            return { id: Number(info.lastInsertRowid), title, price, active };
        },
    };
}

module.exports = { createCourseRepository };
