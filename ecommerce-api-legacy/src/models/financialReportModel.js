class FinancialReportModel {
    constructor(db) {
        this.db = db;
    }

    // Uma única consulta (sem N+1): curso -> matrículas -> aluno -> primeiro pagamento da matrícula.
    findCourseEnrollmentRows() {
        return this.db.all(
            `SELECT c.id AS course_id,
                    c.title AS course_title,
                    e.id AS enrollment_id,
                    u.name AS student_name,
                    p.amount AS payment_amount,
                    p.status AS payment_status
               FROM courses c
               LEFT JOIN enrollments e ON e.course_id = c.id
               LEFT JOIN users u ON u.id = e.user_id
               LEFT JOIN payments p
                      ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
              ORDER BY c.id, e.id`
        );
    }
}

module.exports = FinancialReportModel;
