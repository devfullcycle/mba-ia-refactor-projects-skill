const { PaymentStatus } = require('./paymentGateway');

// Monta o relatório financeiro a partir das linhas achatadas do JOIN,
// preservando o formato de saída original: [{ course, revenue, students: [{ student, paid }] }].
class ReportService {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    async financialReport() {
        const rows = await this.reportModel.financialRows();

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            const data = byCourse.get(row.course_id);

            // Linha sem matrícula (curso sem alunos) — só registra o curso.
            if (row.enrollment_id == null) continue;

            if (row.pay_status === PaymentStatus.PAID) {
                data.revenue += row.pay_amount;
            }
            data.students.push({
                student: row.user_name || 'Unknown',
                paid: row.pay_amount != null ? row.pay_amount : 0,
            });
        }

        return Array.from(byCourse.values());
    }
}

module.exports = ReportService;
