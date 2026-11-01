const {
    NotFoundError,
    PaymentDeniedError,
    UnauthorizedError,
    ValidationError,
} = require('../errors');
const { createEnrollment } = require('../models/Enrollment');
const { createPayment, PAYMENT_STATUS } = require('../models/Payment');
const { createUser } = require('../models/User');
const { isPurchasable } = require('../models/Course');
const { hashPassword, verifyPassword } = require('../utils/password');

class CheckoutService {
    constructor({
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        paymentGateway,
        unitOfWork,
        logger,
    }) {
        this.userRepository = userRepository;
        this.courseRepository = courseRepository;
        this.enrollmentRepository = enrollmentRepository;
        this.paymentRepository = paymentRepository;
        this.auditLogRepository = auditLogRepository;
        this.paymentGateway = paymentGateway;
        this.unitOfWork = unitOfWork;
        this.logger = logger;
    }

    async checkout({ name, email, password, courseId, card }) {
        const course = await this.courseRepository.findActiveById(courseId);
        if (!isPurchasable(course)) throw new NotFoundError('Curso não encontrado');

        const existingUser = await this.userRepository.findByEmail(email);
        if (existingUser) {
            // SEC-04: o dono da matrícula não pode ser escolhido apenas pelo
            // e-mail enviado no body. Para operar em nome de uma conta já
            // existente, o cliente precisa provar a posse dela com a senha.
            if (!password || !verifyPassword(password, existingUser.pass)) {
                throw new UnauthorizedError('Credenciais inválidas');
            }
        } else if (!password) {
            throw new ValidationError('pwd é obrigatório para novo usuário');
        }

        const status = this.paymentGateway.charge({ card });
        this.logger.info({
            event: 'payment.processed',
            userId: existingUser ? existingUser.id : null,
            courseId: course.id,
            cardLast4: String(card).slice(-4),
            status,
        }, 'Payment processed');

        if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeniedError('Pagamento recusado');

        return this.unitOfWork.transaction(async (tx) => {
            const userId = existingUser
                ? existingUser.id
                : await this.userRepository.create(createUser({
                    name,
                    email,
                    pass: hashPassword(password),
                }), tx);

            const enrollmentId = await this.enrollmentRepository.create(
                createEnrollment({ userId, courseId: course.id }),
                tx
            );
            await this.paymentRepository.create(
                createPayment({ enrollmentId, amount: course.price, status }),
                tx
            );
            await this.auditLogRepository.create(`Checkout curso ${course.id} por ${userId}`, tx);

            return { enrollmentId };
        });
    }
}

module.exports = { CheckoutService };
