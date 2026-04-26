const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const { processPayment, PAYMENT_STATUS } = require('../services/paymentService');
const { AppError } = require('../middlewares/errorHandler');

async function checkout(db, { userName, email, password, courseId, cardNumber }) {
  if (!userName || !email || !courseId || !cardNumber) {
    throw new AppError('Missing required fields: userName, email, courseId, cardNumber', 400, true);
  }

  const course = await courseModel.findActiveById(db, courseId);
  if (!course) {
    throw new AppError('Course not found', 404, true);
  }

  let user = await userModel.findByEmail(db, email);
  if (!user) {
    user = await userModel.create(db, userName, email, password || '123456');
  }

  const paymentStatus = processPayment(cardNumber);
  if (paymentStatus === PAYMENT_STATUS.DENIED) {
    throw new AppError('Payment denied', 400, true);
  }

  const enrollment = await enrollmentModel.create(db, user.id, courseId);
  await paymentModel.create(db, enrollment.lastID, course.price, paymentStatus);
  await auditLogModel.create(db, `Checkout course ${courseId} by user ${user.id}`);

  return { message: 'Checkout completed', enrollmentId: enrollment.lastID };
}

module.exports = { checkout };
