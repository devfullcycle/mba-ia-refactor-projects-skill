class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findActiveById(id) {
        return this.db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

module.exports = CourseModel;
