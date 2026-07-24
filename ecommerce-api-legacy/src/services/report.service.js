'use strict';

const { STATUS_PAID } = require('../models/payment.repository');

/**
 * Relatório financeiro por curso.
 *
 * Consome as linhas de uma única query com JOIN e agrupa em memória, preservando o formato
 * de resposta do legado: [{ course, revenue, students: [{ student, paid }] }].
 */
class ReportService {
    constructor({ enrollmentRepository }) {
        this.enrollments = enrollmentRepository;
    }

    async financialReport() {
        const rows = await this.enrollments.financialReportRows();
        const porCurso = new Map();

        for (const row of rows) {
            if (!porCurso.has(row.course_id)) {
                porCurso.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }
            const curso = porCurso.get(row.course_id);

            // LEFT JOIN sem matrícula devolve linha só com o curso.
            if (row.student_name === null && row.payment_amount === null) continue;

            if (row.payment_status === STATUS_PAID) {
                curso.revenue += row.payment_amount;
            }
            curso.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount || 0,
            });
        }

        return [...porCurso.values()];
    }
}

module.exports = { ReportService };
