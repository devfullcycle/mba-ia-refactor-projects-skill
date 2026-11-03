const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

class EnrollmentModel {
  constructor(db) {
    this.db = db;
  }

  async create(userId, courseId, conn = this.db) {
    const { lastID } = await conn.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return lastID;
  }

  async addPayment(enrollmentId, amount, status, conn = this.db) {
    const { lastID } = await conn.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status],
    );
    return lastID;
  }

  recordAudit(action, conn = this.db) {
    return conn.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
  }
}

module.exports = { EnrollmentModel, PAYMENT_STATUS };
