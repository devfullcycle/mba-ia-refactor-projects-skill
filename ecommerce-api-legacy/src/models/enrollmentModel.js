const db = require('../config/database');

const EnrollmentModel = {
    async create({ userId, courseId }) {
        const { lastID } = await db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return lastID;
    },
};

module.exports = EnrollmentModel;
