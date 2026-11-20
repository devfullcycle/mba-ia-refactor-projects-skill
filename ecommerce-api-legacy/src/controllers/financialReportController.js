const { PaymentStatus } = require('../models/paymentModel');

const UNKNOWN_STUDENT = 'Unknown';

class FinancialReportController {
    constructor({ financialReport }) {
        this.financialReport = financialReport;
    }

    // Receita por curso = soma dos pagamentos PAID; lista todos os alunos matriculados.
    async build() {
        const rows = await this.financialReport.listCourseEnrollmentRows();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { title: row.course_title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const course = byCourse.get(row.course_id);
            if (row.payment_status === PaymentStatus.PAID) course.revenue += row.payment_amount;
            course.students.push({ name: row.student_name ?? UNKNOWN_STUDENT, paid: row.payment_amount ?? 0 });
        }

        return [...byCourse.values()];
    }
}

module.exports = FinancialReportController;
