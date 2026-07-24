'use strict';

class EnrollmentRepository {
    constructor(connection) {
        this.db = connection;
    }

    async create({ userId, courseId }) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return { id: lastID, userId, courseId };
    }

    /**
     * Relatório financeiro em uma única query.
     * O legado fazia 1 + N + 2×M queries encadeadas em callbacks, com contadores manuais.
     */
    financialReportRows() {
        return this.db.all(`
            SELECT c.id           AS course_id,
                   c.title        AS course_title,
                   u.name         AS student_name,
                   p.amount       AS payment_amount,
                   p.status       AS payment_status
              FROM courses c
              LEFT JOIN enrollments e ON e.course_id = c.id
              LEFT JOIN users u       ON u.id = e.user_id
              LEFT JOIN payments p    ON p.enrollment_id = e.id
             ORDER BY c.id, e.id
        `);
    }
}

module.exports = { EnrollmentRepository };
