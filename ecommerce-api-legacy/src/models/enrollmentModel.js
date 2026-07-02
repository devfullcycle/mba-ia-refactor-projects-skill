class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    create(userId, courseId) {
        return this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
    }

    findByUserId(userId) {
        return this.db.all('SELECT id FROM enrollments WHERE user_id = ?', [userId]);
    }

    deleteByUserId(userId) {
        return this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
    }
}

module.exports = EnrollmentModel;
