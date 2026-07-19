// Model de matrículas — acesso a dados da entidade Enrollment.
class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create(userId, courseId) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return lastID;
    }
}

module.exports = EnrollmentModel;
