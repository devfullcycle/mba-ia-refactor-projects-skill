const { all } = require('../db');

async function financialReport() {
  const rows = await all(`
    SELECT c.title AS course, u.name AS student, p.amount AS paid, p.status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
     ORDER BY c.id
  `);

  const byCourse = new Map();
  for (const r of rows) {
    if (!byCourse.has(r.course)) {
      byCourse.set(r.course, { course: r.course, revenue: 0, students: [] });
    }
    const entry = byCourse.get(r.course);
    if (r.student) {
      if (r.status === 'PAID') entry.revenue += r.paid || 0;
      entry.students.push({ student: r.student, paid: r.paid || 0 });
    }
  }
  return [...byCourse.values()];
}

module.exports = { financialReport };
