const { all } = require('../database/connection');
const userModel = require('../models/userModel');
const paymentModel = require('../models/paymentModel');
const enrollmentModel = require('../models/enrollmentModel');
const { AppError } = require('../middlewares/errorHandler');

async function deleteUser(db, userId) {
  const user = await userModel.findById(db, userId);
  if (!user) {
    throw new AppError('User not found', 404, true);
  }

  const enrollments = await all(db, 'SELECT id FROM enrollments WHERE user_id = ?', [userId]);
  const enrollmentIds = enrollments.map((e) => e.id);

  await paymentModel.deleteByEnrollmentIds(db, enrollmentIds);
  await enrollmentModel.deleteByUserId(db, userId);
  await userModel.deleteById(db, userId);

  return { message: 'User deleted successfully' };
}

module.exports = { deleteUser };
