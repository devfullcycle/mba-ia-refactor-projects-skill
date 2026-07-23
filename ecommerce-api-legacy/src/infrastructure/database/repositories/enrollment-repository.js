'use strict';

function createEnrollmentRepository(connection) {
    return {
        create({ userId, courseId }, tx = connection) {
            const info = tx.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(userId, courseId);
            return { id: Number(info.lastInsertRowid), userId, courseId };
        },
        listAllWithRelations() {
            // Consulta única com JOIN para eliminar o padrão N+1 (F-009/T07).
            return connection
                .prepare(
                    `SELECT
                        e.id AS enrollment_id,
                        e.course_id AS course_id,
                        c.title AS course_title,
                        u.name AS student_name,
                        p.amount AS payment_amount,
                        p.status AS payment_status
                    FROM enrollments e
                    JOIN users u ON u.id = e.user_id
                    JOIN courses c ON c.id = e.course_id
                    LEFT JOIN payments p ON p.enrollment_id = e.id`
                )
                .all();
        },
        countByUserId(userId) {
            const row = connection.prepare('SELECT COUNT(*) AS total FROM enrollments WHERE user_id = ?').get(userId);
            return row ? Number(row.total) : 0;
        },
    };
}

module.exports = { createEnrollmentRepository };
