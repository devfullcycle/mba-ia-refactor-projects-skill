/**
 * Model de cursos — acesso a dados de cursos, matrículas e pagamentos.
 */
const { getDb } = require('./db');

function findActiveById(id) {
    return new Promise((resolve, reject) => {
        getDb().get('SELECT * FROM courses WHERE id = ? AND active = 1', [id], (err, row) => {
            if (err) return reject(err);
            resolve(row || null);
        });
    });
}

function createEnrollment(userId, courseId) {
    return new Promise((resolve, reject) => {
        getDb().run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
            function (err) {
                if (err) return reject(err);
                resolve(this.lastID);
            }
        );
    });
}

function createPayment(enrollmentId, amount, status) {
    return new Promise((resolve, reject) => {
        getDb().run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
            function (err) {
                if (err) return reject(err);
                resolve(this.lastID);
            }
        );
    });
}

function writeAuditLog(action) {
    return new Promise((resolve, reject) => {
        getDb().run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
            (err) => {
                if (err) return reject(err);
                resolve(true);
            }
        );
    });
}

/**
 * Consulta agregada única (JOIN) para o relatório financeiro,
 * eliminando as infinitas queries aninhadas (N+1).
 */
function getReportData() {
    return new Promise((resolve, reject) => {
        const sql = `
            SELECT c.id AS course_id, c.title,
                   e.id AS enrollment_id, e.user_id,
                   u.name AS student_name, u.email AS student_email,
                   p.amount AS payment_amount, p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            WHERE c.active = 1
            ORDER BY c.id, e.id
        `;
        getDb().all(sql, (err, rows) => {
            if (err) return reject(err);
            resolve(rows || []);
        });
    });
}

module.exports = {
    findActiveById,
    createEnrollment,
    createPayment,
    writeAuditLog,
    getReportData,
};