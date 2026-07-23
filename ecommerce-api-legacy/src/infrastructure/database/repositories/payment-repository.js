'use strict';

function createPaymentRepository(connection) {
    return {
        create({ enrollmentId, amount, status }, tx = connection) {
            const info = tx.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)').run(enrollmentId, amount, status);
            return { id: Number(info.lastInsertRowid), enrollmentId, amount, status };
        },
        countByUserId(userId) {
            const row = connection
                .prepare(
                    `SELECT COUNT(*) AS total
                    FROM payments p
                    JOIN enrollments e ON e.id = p.enrollment_id
                    WHERE e.user_id = ?`
                )
                .get(userId);
            return row ? Number(row.total) : 0;
        },
    };
}

module.exports = { createPaymentRepository };
