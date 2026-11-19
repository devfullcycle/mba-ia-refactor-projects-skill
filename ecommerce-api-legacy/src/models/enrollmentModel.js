class EnrollmentModel {
    constructor(db) {
        this._db = db;
    }

    async create(userId, courseId) {
        const result = await this._db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return result.lastID;
    }
}

module.exports = EnrollmentModel;
