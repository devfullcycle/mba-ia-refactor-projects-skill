class FinancialReportController {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    getReport = async (req, res) => {
        const rows = await this.reportModel.findFinancialReportRows();

        const reportByCourseId = new Map();

        for (const row of rows) {
            if (!reportByCourseId.has(row.course_id)) {
                reportByCourseId.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            const courseData = reportByCourseId.get(row.course_id);

            if (row.student_name) {
                const paid = row.payment_status === 'PAID' ? row.paid_amount : 0;
                courseData.students.push({ student: row.student_name, paid });
                if (row.payment_status === 'PAID') courseData.revenue += row.paid_amount;
            }
        }

        res.json(Array.from(reportByCourseId.values()));
    };
}

module.exports = FinancialReportController;
