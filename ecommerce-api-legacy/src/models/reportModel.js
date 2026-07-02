class ReportModel {
    constructor(db) {
        this.db = db;
    }

    findFinancialReportRows() {
        return this.db.all(
            `SELECT c.id AS course_id, c.title AS course_title,
                    u.name AS student_name,
                    p.amount AS paid_amount, p.status AS payment_status
             FROM courses c
             LEFT JOIN enrollments e ON e.course_id = c.id
             LEFT JOIN users u ON u.id = e.user_id
             LEFT JOIN payments p ON p.enrollment_id = e.id
             ORDER BY c.id`,
            []
        );
    }
}

module.exports = ReportModel;
