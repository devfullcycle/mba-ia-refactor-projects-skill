// Relatório financeiro. Antes: N+1 em callbacks aninhados com contadores
// manuais. Agora: uma única query com JOIN + agrupamento em memória.
class ReportService {
    constructor(db) {
        this._db = db;
    }

    async financialReport() {
        const rows = await this._db.all(`
            SELECT c.id          AS course_id,
                   c.title       AS course_title,
                   e.id          AS enrollment_id,
                   u.name        AS student_name,
                   p.amount      AS amount,
                   p.status      AS status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u       ON u.id = e.user_id
            LEFT JOIN payments p    ON p.enrollment_id = e.id
            ORDER BY c.id, e.id
        `);

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            const data = byCourse.get(row.course_id);

            // Linha sem matrícula (curso sem alunos) — não gera entrada de aluno.
            if (row.enrollment_id === null) continue;

            if (row.status === 'PAID') {
                data.revenue += row.amount;
            }
            data.students.push({
                student: row.student_name || 'Unknown',
                paid: row.amount !== null ? row.amount : 0,
            });
        }

        return Array.from(byCourse.values());
    }
}

module.exports = ReportService;
