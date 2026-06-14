class CourseModel {
    constructor(db) {
        this.db = db
    }

    async findActiveById(id) {
        return this.db.getAsync(
            "SELECT id, title, price FROM courses WHERE id = ? AND active = 1",
            [id]
        )
    }

    async findAll() {
        return this.db.allAsync("SELECT id, title, price, active FROM courses")
    }
}

module.exports = CourseModel
