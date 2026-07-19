// Model de relatório — busca todos os dados do relatório financeiro numa única query
// com JOINs, eliminando o N+1 (antes: uma query por curso, matrícula, usuário e pagamento).
class ReportModel {
    constructor(db) {
        this.db = db;
    }

    financialRows() {
        return this.db.all(
            `SELECT c.id           AS course_id,
                    c.title        AS course_title,
                    e.id           AS enrollment_id,
                    u.name         AS user_name,
                    p.amount       AS pay_amount,
                    p.status       AS pay_status
             FROM courses c
             LEFT JOIN enrollments e ON e.course_id = c.id
             LEFT JOIN users u       ON u.id = e.user_id
             LEFT JOIN payments p    ON p.enrollment_id = e.id
             ORDER BY c.id`,
            []
        );
    }
}

module.exports = ReportModel;
