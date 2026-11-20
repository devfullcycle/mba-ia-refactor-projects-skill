const { NotFoundError, PaymentDeniedError, ValidationError } = require('./errors');
const { validateCheckoutInput } = require('./validators');
const { PaymentStatus } = require('../models/paymentModel');

class CheckoutController {
    constructor({ db, users, courses, enrollments, payments, auditLogs, paymentGateway, passwordHasher, logger }) {
        Object.assign(this, { db, users, courses, enrollments, payments, auditLogs, paymentGateway, passwordHasher, logger });
    }

    async checkout(rawInput) {
        const input = validateCheckoutInput(rawInput);

        const course = await this.courses.findActiveById(input.courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');
        // Falha cedo (antes de cobrar o cartão) quando um usuário novo não informa senha.
        if (!input.password && !(await this.users.findByEmail(input.email))) throw new ValidationError();

        const { approved } = await this.paymentGateway.authorize({ cardNumber: input.cardNumber, amount: course.price });
        if (!approved) throw new PaymentDeniedError();

        // Usuário, matrícula, pagamento e auditoria são gravados atomicamente.
        const result = await this.db.transaction(async () => {
            const userId = await this.findOrCreateUser(input);
            const enrollmentId = await this.enrollments.create(userId, course.id);
            await this.payments.create(enrollmentId, course.price, PaymentStatus.PAID);
            await this.auditLogs.record(`Checkout curso ${course.id} por ${userId}`);
            return { userId, enrollmentId };
        });

        this.logger.info(`Checkout concluído: curso=${course.id} usuario=${result.userId} matricula=${result.enrollmentId}`);
        return { enrollmentId: result.enrollmentId };
    }

    async findOrCreateUser({ name, email, password }) {
        const existing = await this.users.findByEmail(email);
        if (existing) return existing.id;

        // Novo usuário precisa informar senha (o legado usava a senha padrão "123456").
        if (!password) throw new ValidationError();
        const passwordHash = await this.passwordHasher.hash(password);
        return this.users.create({ name, email, passwordHash });
    }
}

module.exports = CheckoutController;
