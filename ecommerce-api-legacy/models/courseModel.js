const { dbGet, dbAll } = require('../database');

class CourseModel {
    static async getActiveById(id) {
        return await dbGet("SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
    }

    static async getAll() {
        return await dbAll("SELECT * FROM courses");
    }
}

module.exports = CourseModel;
