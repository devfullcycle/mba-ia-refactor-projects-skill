const { run } = require('../db');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');

async function deleteUser(id) {
  await run('BEGIN');
  try {
    const enrollments = await enrollmentModel.listByUser(id);
    for (const e of enrollments) {
      await paymentModel.deleteByEnrollment(e.id);
    }
    await run('DELETE FROM enrollments WHERE user_id = ?', [id]);
    await run('DELETE FROM users WHERE id = ?', [id]);
    await run('COMMIT');
  } catch (err) {
    await run('ROLLBACK');
    throw err;
  }
  return userModel.findById(id);
}

module.exports = { deleteUser };
