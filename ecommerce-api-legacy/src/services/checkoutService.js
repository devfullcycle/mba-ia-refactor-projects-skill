const { PAYMENT_STATUS } = require('../constants');
const { NotFoundError, ValidationError, PaymentDeniedError } = require('../utils/errors');

module.exports = ({ db, models, paymentGateway, hashPassword }) => ({
    async checkout({ name, email, password, courseId, card }) {
        const course = await models.course.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const existingUser = await models.user.findByEmail(email);
        if (!existingUser && !password) throw new ValidationError('Bad Request');

        const status = paymentGateway.charge(card);
        if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeniedError();

        const passwordHash = existingUser ? null : await hashPassword(password);

        // Usuário (se novo), matrícula, pagamento e auditoria: tudo ou nada.
        return db.transaction(async () => {
            const userId = existingUser
                ? existingUser.id
                : await models.user.create({ name, email, passwordHash });
            const enrollmentId = await models.enrollment.create(userId, courseId);
            await models.payment.create(enrollmentId, course.price, status);
            await models.auditLog.create(`Checkout curso ${courseId} por ${userId}`);
            return { enrollmentId };
        });
    }
});
