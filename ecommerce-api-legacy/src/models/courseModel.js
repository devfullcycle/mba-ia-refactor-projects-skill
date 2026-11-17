const db = require('./database');

class CourseModel {
    static async findActiveById(id) {
        return db.get(
            "SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1",
            [id]
        );
    }

    static async findById(id) {
        return db.get(
            "SELECT id, title, price, active FROM courses WHERE id = ?",
            [id]
        );
    }

    static async findAll() {
        return db.all(
            "SELECT id, title, price, active FROM courses ORDER BY id ASC"
        );
    }
}

module.exports = CourseModel;
