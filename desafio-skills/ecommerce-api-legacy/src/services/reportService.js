class ReportService {
  constructor(conn) {
    this.conn = conn;
  }

  async financialReport() {
    const rows = await this.conn.all(
      `
      SELECT
        c.id AS course_id,
        c.title AS course_title,
        e.id AS enrollment_id,
        u.name AS student_name,
        p.amount AS paid_amount,
        p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id
    `
    );

    const byCourse = new Map();
    for (const r of rows) {
      if (!byCourse.has(r.course_id)) {
        byCourse.set(r.course_id, {
          course: r.course_title,
          revenue: 0,
          students: [],
        });
      }
      if (!r.enrollment_id) {
        continue;
      }
      const entry = byCourse.get(r.course_id);
      if (r.payment_status === 'PAID' && r.paid_amount) {
        entry.revenue += r.paid_amount;
      }
      entry.students.push({
        student: r.student_name || 'Unknown',
        paid: r.paid_amount || 0,
      });
    }
    return Array.from(byCourse.values());
  }
}

module.exports = { ReportService };
