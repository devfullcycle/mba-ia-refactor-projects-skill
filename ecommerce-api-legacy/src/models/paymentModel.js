const { run } = require('../db');

const create = (enrollmentId, amount, status) =>
  run(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [enrollmentId, amount, status]
  );

const deleteByEnrollment = (enrollmentId) =>
  run('DELETE FROM payments WHERE enrollment_id = ?', [enrollmentId]);

module.exports = { create, deleteByEnrollment };
