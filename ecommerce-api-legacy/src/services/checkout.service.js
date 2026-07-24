'use strict';

const { withTransaction } = require('../database/connection');
const { NotFoundError, PaymentDeclinedError } = require('../utils/errors');
const { validateNewUserPassword } = require('../validators/checkout.validator');

/**
 * Regra de checkout: atravessa 5 agregados (curso, usuário, matrícula, pagamento,
 * auditoria), então vive em um service — não no controller.
 *
 * O legado fazia isso em 5 níveis de callback aninhado, sem transação: falha ao registrar o
 * pagamento deixava a matrícula persistida.
 */
class CheckoutService {
    constructor({
        connection,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditRepository,
        paymentGateway,
        cache,
        logger,
        passwordMinLength = 6,
    }) {
        this.passwordMinLength = passwordMinLength;
        this.connection = connection;
        this.users = userRepository;
        this.courses = courseRepository;
        this.enrollments = enrollmentRepository;
        this.payments = paymentRepository;
        this.audit = auditRepository;
        this.gateway = paymentGateway;
        this.cache = cache;
        this.logger = logger;
    }

    async execute({ name, email, password, courseId, card }) {
        const course = await this.courses.findActiveById(courseId);
        if (!course) {
            throw new NotFoundError('Curso não encontrado');
        }

        // A cobrança acontece antes da transação: pagamento recusado não cria nada.
        const payment = await this.gateway.charge({ card, amount: course.price });
        if (!payment.approved) {
            throw new PaymentDeclinedError('Pagamento recusado');
        }

        const enrollmentId = await withTransaction(this.connection, async () => {
            const existing = await this.users.findByEmail(email);
            const user =
                existing ||
                (await this.users.create({
                    name,
                    email,
                    // Conta nova exige senha válida — o legado usava "123456" como default.
                    password: validateNewUserPassword(password, {
                        passwordMinLength: this.passwordMinLength,
                    }),
                }));

            const enrollment = await this.enrollments.create({
                userId: user.id,
                courseId: course.id,
            });
            await this.payments.create({
                enrollmentId: enrollment.id,
                amount: payment.amount,
                status: payment.status,
            });
            await this.audit.log(`Checkout curso ${course.id} por ${user.id}`);

            this.cache.set(`last_checkout_${user.id}`, course.title);
            this.logger.info('Checkout concluído', {
                userId: user.id,
                courseId: course.id,
                enrollmentId: enrollment.id,
            });
            return enrollment.id;
        });

        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = { CheckoutService };
