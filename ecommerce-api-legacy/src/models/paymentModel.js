const db = require('./database');

class PaymentModel {
    static async createEnrollment(userId, courseId) {
        const result = await db.run(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            [userId, courseId]
        );
        return result.lastID;
    }

    static async createPayment(enrollmentId, amount, status) {
        const result = await db.run(
            "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
            [enrollmentId, amount, status]
        );
        return result.lastID;
    }

    static async createAuditLog(action) {
        const now = new Date().toISOString();
        const result = await db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action]
        );
        return result.lastID;
    }

    /**
     * Gera relatório financeiro consolidado eliminando completamente o anti-pattern N+1.
     * Executa 1 única consulta via LEFT JOIN em vez de loops de queries aninhadas.
     * @returns {Promise<Array<{course: string, revenue: number, students: Array<{student: string, paid: number}>}>>}
     */
    static async getFinancialReport() {
        const query = `
            SELECT 
                c.id AS course_id,
                c.title AS course_title,
                e.id AS enrollment_id,
                u.name AS student_name,
                p.amount AS payment_amount,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            LEFT JOIN users u ON e.user_id = u.id
            LEFT JOIN payments p ON e.id = p.enrollment_id
            ORDER BY c.id ASC, e.id ASC
        `;

        const rows = await db.all(query);
        const reportMap = new Map();

        for (const row of rows) {
            if (!reportMap.has(row.course_id)) {
                reportMap.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: []
                });
            }

            const courseEntry = reportMap.get(row.course_id);

            if (row.enrollment_id) {
                if (row.payment_status === 'PAID' && typeof row.payment_amount === 'number') {
                    courseEntry.revenue += row.payment_amount;
                }

                courseEntry.students.push({
                    student: row.student_name || 'Unknown',
                    paid: row.payment_amount !== null && row.payment_amount !== undefined ? row.payment_amount : 0
                });
            }
        }

        return Array.from(reportMap.values());
    }
}

module.exports = PaymentModel;
