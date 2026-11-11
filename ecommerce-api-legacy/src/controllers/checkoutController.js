const db = require('../config/database');
const logger = require('../config/logger');
const { BadRequestError, NotFoundError } = require('../utils/errors');
const { PAYMENT_STATUS } = require('../utils/constants');
const { hashPassword } = require('../utils/password');
const PaymentService = require('../services/paymentService');
const UserModel = require('../models/userModel');
const CourseModel = require('../models/courseModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');
const AuditLogModel = require('../models/auditLogModel');

function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim() !== '';
}

// Contrato legado mantido: { usr, eml, pwd, c_id, card }.
function parseCheckoutInput(body = {}) {
    const input = {
        name: body.usr,
        email: body.eml,
        password: body.pwd,
        courseId: Number(body.c_id),
        cardNumber: body.card === undefined || body.card === null ? '' : String(body.card),
    };

    const valid = isNonEmptyString(input.name)
        && isNonEmptyString(input.email)
        && Number.isInteger(input.courseId) && input.courseId > 0
        && input.cardNumber !== ''
        && (input.password === undefined || typeof input.password === 'string');
    if (!valid) throw new BadRequestError();

    input.email = input.email.trim();
    return input;
}

async function findOrCreateUser({ name, email, password }) {
    const existing = await UserModel.findIdByEmail(email);
    if (existing) return existing.id;

    // Antes o usuário novo recebia a senha padrão "123456"; agora a senha é obrigatória.
    if (!isNonEmptyString(password)) throw new BadRequestError();
    return UserModel.create({ name, email, passwordHash: await hashPassword(password) });
}

async function checkout(req, res) {
    const input = parseCheckoutInput(req.body);

    const course = await CourseModel.findActiveById(input.courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    // O pagamento é autorizado antes de qualquer escrita: compra recusada não deixa usuário/matrícula no banco.
    const status = PaymentService.authorize({ cardNumber: input.cardNumber, amount: course.price });
    if (status !== PAYMENT_STATUS.PAID) throw new BadRequestError('Pagamento recusado');

    const { userId, enrollmentId } = await db.transaction(async () => {
        const newUserId = await findOrCreateUser(input);
        const newEnrollmentId = await EnrollmentModel.create({ userId: newUserId, courseId: course.id });
        await PaymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
        await AuditLogModel.create(`Checkout curso ${course.id} por ${newUserId}`);
        return { userId: newUserId, enrollmentId: newEnrollmentId };
    });

    logger.info('Checkout concluído', { userId, courseId: course.id, enrollmentId });
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
}

module.exports = { checkout };
