const { run, get } = require('../db');
const { log } = require('../utils/logger');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');

const APPROVED_PREFIX = '4';

class HttpError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function checkout({ name, email, password, courseId, card }) {
  const course = await courseModel.findActiveById(courseId);
  if (!course) throw new HttpError('Curso nao encontrado', 404);

  const status = card.startsWith(APPROVED_PREFIX) ? 'PAID' : 'DENIED';
  log(`Processando cartao (ultimos 4: ${card.slice(-4)})`);
  if (status === 'DENIED') throw new HttpError('Pagamento recusado', 400);

  let userId;
  const existing = await userModel.findByEmail(email);
  if (existing) {
    userId = existing.id;
  } else {
    userId = await userModel.create(name, email, password || '123456');
  }

  await run('BEGIN');
  let enrollmentId;
  try {
    const res = await enrollmentModel.create(userId, courseId);
    enrollmentId = res.lastID;
    await paymentModel.create(enrollmentId, course.price, status);
    await auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);
    await run('COMMIT');
  } catch (err) {
    await run('ROLLBACK');
    throw err;
  }

  return { enrollment_id: enrollmentId };
}

module.exports = { checkout, HttpError };
