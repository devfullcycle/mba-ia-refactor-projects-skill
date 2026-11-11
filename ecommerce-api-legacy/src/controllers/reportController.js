const CourseModel = require('../models/courseModel');
const { PAYMENT_STATUS } = require('../utils/constants');

const UNKNOWN_STUDENT = 'Unknown';

// Agrupa as linhas (curso x matrícula) no formato legado:
// [{ course, revenue, students: [{ student, paid }] }]
function buildFinancialReport(rows) {
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }
        if (row.enrollment_id === null) continue; // curso sem matrículas

        const entry = byCourse.get(row.course_id);
        const hasPayment = row.payment_amount !== null;
        if (hasPayment && row.payment_status === PAYMENT_STATUS.PAID) {
            entry.revenue += row.payment_amount;
        }
        entry.students.push({
            student: row.student_name ?? UNKNOWN_STUDENT,
            paid: hasPayment ? row.payment_amount : 0,
        });
    }

    return [...byCourse.values()];
}

async function getFinancialReport(req, res) {
    const rows = await CourseModel.findFinancialRows();
    res.json(buildFinancialReport(rows));
}

module.exports = { getFinancialReport, buildFinancialReport };
