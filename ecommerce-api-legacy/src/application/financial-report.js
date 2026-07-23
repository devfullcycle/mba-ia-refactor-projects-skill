'use strict';

const { isPaid } = require('../domain/payment');

/**
 * Caso de uso: relatório financeiro. Uma única consulta com JOIN substitui
 * o padrão N+1 original (F-009/T07); agregação acontece em memória.
 */
function createFinancialReportUseCase({ courseRepository, enrollmentRepository }) {
    return {
        execute() {
            const courses = courseRepository.listAll();
            const rows = enrollmentRepository.listAllWithRelations();

            const byCourseId = new Map(courses.map((course) => [
                course.id,
                { course: course.title, revenue: 0, students: [] },
            ]));

            for (const row of rows) {
                const courseData = byCourseId.get(row.course_id);
                if (!courseData) continue;

                const payment = row.payment_status
                    ? { amount: row.payment_amount, status: row.payment_status }
                    : null;

                if (isPaid(payment)) {
                    courseData.revenue += payment.amount;
                }

                courseData.students.push({
                    student: row.student_name || 'Unknown',
                    paid: payment ? payment.amount : 0,
                });
            }

            return Array.from(byCourseId.values());
        },
    };
}

module.exports = { createFinancialReportUseCase };
