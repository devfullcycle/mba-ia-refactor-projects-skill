class CourseModel {
  constructor(db) {
    this.db = db;
  }

  findActiveById(id) {
    return this.db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
  }

  /**
   * Relatório financeiro por curso em uma única query (sem N+1).
   * Retorna [{ course, revenue, students: [{ student, paid }] }].
   */
  async financialReport(paidStatus) {
    const rows = await this.db.all(`
      SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
             u.name AS student_name, p.amount, p.status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id
    `);

    const report = new Map();
    for (const row of rows) {
      if (!report.has(row.course_id)) {
        report.set(row.course_id, { course: row.title, revenue: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;
      const courseData = report.get(row.course_id);
      if (row.status === paidStatus) courseData.revenue += row.amount;
      courseData.students.push({
        student: row.student_name ?? 'Unknown',
        paid: row.amount ?? 0,
      });
    }
    return [...report.values()];
  }
}

module.exports = CourseModel;
