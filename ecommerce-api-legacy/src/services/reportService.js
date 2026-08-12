/**
 * Serviço de relatório financeiro — agrega dados por curso.
 * Usa consulta JOIN única (sem N+1) e monta o payload de resposta.
 */
const courseModel = require('../models/courseModel');

async function buildFinancialReport() {
    const rows = await courseModel.getReportData();

    const report = [];
    const index = new Map();

    for (const row of rows) {
        if (!index.has(row.course_id)) {
            index.set(row.course_id, {
                course: row.title,
                revenue: 0,
                students: [],
            });
            report.push(index.get(row.course_id));
        }
        const course = index.get(row.course_id);

        // Linha com LEFT JOIN sem matrícula (curso sem alunos) — ignora.
        if (row.enrollment_id === null) continue;

        if (row.payment_status === 'PAID' && row.payment_amount != null) {
            course.revenue += row.payment_amount;
        }
        course.students.push({
            student: row.student_name || 'Unknown',
            paid: row.payment_amount || 0,
        });
    }

    return report;
}

module.exports = { buildFinancialReport };