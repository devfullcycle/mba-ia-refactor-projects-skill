class CourseModel {
    constructor(db) {
        this._db = db;
    }

    findActiveById(id) {
        return this._db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }

    all() {
        return this._db.all('SELECT * FROM courses');
    }
}

module.exports = CourseModel;
