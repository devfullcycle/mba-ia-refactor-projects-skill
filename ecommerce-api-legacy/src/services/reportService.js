const { PAYMENT_STATUS } = require('../constants');

module.exports = ({ models }) => ({
    async financialReport() {
        const rows = await models.report.findFinancialRows();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue; // curso sem matrículas

            const entry = byCourse.get(row.course_id);
            if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
            entry.students.push({
                student: row.student || 'Unknown',
                paid: row.amount ?? 0
            });
        }

        return [...byCourse.values()];
    }
});
