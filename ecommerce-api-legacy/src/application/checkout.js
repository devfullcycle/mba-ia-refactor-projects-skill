'use strict';

const crypto = require('node:crypto');
const { createUser, toPublicUser } = require('../domain/user');
const { assertActiveCourse } = require('../domain/course');
const { assertCanCheckoutForEmail } = require('../domain/identity');
const { PAID } = require('../domain/payment');
const { ValidationError, PaymentDeniedError } = require('../domain/errors');

/**
 * Caso de uso: checkout. Orquestra domínio + repositories + payment gateway
 * dentro de uma única fronteira transacional (F-005/T06). Nenhuma escrita
 * acontece antes da cobrança ser aprovada, evitando estado parcial.
 */
function createCheckoutUseCase({
    connection,
    userRepository,
    courseRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    passwordHasher,
    paymentGateway,
    cache,
    logger,
}) {
    return {
        execute(command, identity) {
            const { name, email, password, courseId, card } = command;

            if (!name || !email || !courseId || !card) {
                throw new ValidationError('Campos obrigatórios ausentes para o checkout');
            }
            if (password !== undefined && (typeof password !== 'string' || password.length === 0)) {
                throw new ValidationError('Senha inválida');
            }

            assertCanCheckoutForEmail(identity, email);

            const course = courseRepository.findActiveById(courseId);
            assertActiveCourse(course);

            const existingUser = userRepository.findByEmail(email);
            if (!existingUser) {
                // Valida invariantes de domínio antes de cobrar, sem persistir ainda.
                createUser({ name, email, passwordHash: 'placeholder' });
            }

            const charge = paymentGateway.charge({ card, amount: course.price });
            if (charge.status !== PAID) {
                throw new PaymentDeniedError('Pagamento recusado pelo gateway');
            }

            const result = connection.transaction(() => {
                let user = existingUser;
                if (!user) {
                    const passwordHash = passwordHasher.hash(password || crypto.randomBytes(12).toString('hex'));
                    user = userRepository.create({ name, email, passwordHash });
                }

                const enrollment = enrollmentRepository.create({ userId: user.id, courseId: course.id });
                paymentRepository.create({ enrollmentId: enrollment.id, amount: course.price, status: charge.status });
                auditLogRepository.record(`Checkout curso ${course.id} por ${user.id}`);

                return { user, enrollment };
            });

            cache.set(`last_checkout_${result.user.id}`, course.title);
            logger.info('Checkout concluído', { userId: result.user.id, courseId: course.id, enrollmentId: result.enrollment.id });

            return {
                message: 'Sucesso',
                enrollmentId: result.enrollment.id,
                user: toPublicUser(result.user),
            };
        },
    };
}

module.exports = { createCheckoutUseCase };
