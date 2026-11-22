const { PAYMENT_STATUS, UNKNOWN_STUDENT_NAME } = require('../config/constants');

class FinancialReportService {
    constructor({ financialReportModel }) {
        this.financialReportModel = financialReportModel;
    }

    async build() {
        const rows = await this.financialReportModel.findCourseEnrollmentRows();
        const coursesById = new Map();

        for (const row of rows) {
            if (!coursesById.has(row.course_id)) {
                coursesById.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const entry = coursesById.get(row.course_id);
            if (row.payment_status === PAYMENT_STATUS.PAID) {
                entry.revenue += row.payment_amount;
            }
            entry.students.push({
                student: row.student_name || UNKNOWN_STUDENT_NAME,
                paid: row.payment_amount || 0
            });
        }

        return [...coursesById.values()];
    }
}

module.exports = FinancialReportService;
