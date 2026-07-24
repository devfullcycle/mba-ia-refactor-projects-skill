'use strict';

class CourseRepository {
    constructor(connection) {
        this.db = connection;
    }

    findActiveById(id) {
        return this.db.get(
            'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1',
            [id]
        );
    }

    listAll() {
        return this.db.all('SELECT id, title, price, active FROM courses ORDER BY id');
    }
}

module.exports = { CourseRepository };
