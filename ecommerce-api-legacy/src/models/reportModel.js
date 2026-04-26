const { all } = require('../database/connection');

function getFinancialReport(db) {
  const sql = `
    SELECT
      c.id AS course_id,
      c.title AS course_title,
      u.id AS user_id,
      u.name AS student_name,
      p.amount AS payment_amount,
      p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON c.id = e.course_id
    LEFT JOIN users u ON e.user_id = u.id
    LEFT JOIN payments p ON e.id = p.enrollment_id
  `;
  return all(db, sql, []);
}

module.exports = { getFinancialReport };
