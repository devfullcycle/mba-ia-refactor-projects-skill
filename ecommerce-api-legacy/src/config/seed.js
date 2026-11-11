const crypto = require('crypto');
const config = require('./config');
const logger = require('./logger');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../utils/constants');
const UserModel = require('../models/userModel');
const CourseModel = require('../models/courseModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br' };
const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0 },
    { title: 'Docker', price: 497.0 },
];

async function seedDatabase() {
    if (!config.seedDb) return;
    if ((await CourseModel.count()) > 0) return; // banco já populado

    let seedPassword = config.seedUserPassword;
    if (!seedPassword) {
        seedPassword = crypto.randomBytes(12).toString('base64url');
        logger.warn('SEED_USER_PASSWORD não definida; usuário de exemplo criado com senha aleatória');
    }

    const userId = await UserModel.create({
        ...SEED_USER,
        passwordHash: await hashPassword(seedPassword),
    });
    const courseIds = [];
    for (const course of SEED_COURSES) {
        courseIds.push(await CourseModel.create(course));
    }
    const enrollmentId = await EnrollmentModel.create({ userId, courseId: courseIds[0] });
    await PaymentModel.create({
        enrollmentId,
        amount: SEED_COURSES[0].price,
        status: PAYMENT_STATUS.PAID,
    });
    logger.info('Banco populado com dados de exemplo');
}

module.exports = { seedDatabase };
