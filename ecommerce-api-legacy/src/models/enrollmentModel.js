const { db } = require('../database/connection')

function create(userId, courseId) {
  const result = db.prepare(
    'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)'
  ).run(userId, courseId)
  return result.lastInsertRowid
}

function createPayment(enrollmentId, amount, status) {
  const result = db.prepare(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)'
  ).run(enrollmentId, amount, status)
  return result.lastInsertRowid
}

function getFinancialReport() {
  return db.prepare(`
    SELECT
      c.id AS course_id,
      c.title AS course_title,
      u.name AS student_name,
      p.amount AS paid,
      p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    WHERE c.active = 1
    ORDER BY c.id
  `).all()
}

module.exports = { create, createPayment, getFinancialReport }
