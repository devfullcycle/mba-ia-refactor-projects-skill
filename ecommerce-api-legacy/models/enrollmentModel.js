const { dbRun, dbAll } = require('../database');

class EnrollmentModel {
    static async create(userId, courseId) {
        const result = await dbRun(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            [userId, courseId]
        );
        return result.lastID;
    }

    static async getByCourseId(courseId) {
        return await dbAll("SELECT * FROM enrollments WHERE course_id = ?", [courseId]);
    }
}

module.exports = EnrollmentModel;
