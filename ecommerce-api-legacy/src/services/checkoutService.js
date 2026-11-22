const AppError = require('../errors/AppError');
const { PAYMENT_STATUS } = require('../config/constants');

class CheckoutService {
    constructor({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, passwordService, paymentGateway, logger }) {
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.passwordService = passwordService;
        this.paymentGateway = paymentGateway;
        this.logger = logger;
    }

    async checkout({ name, email, password, courseId, card }) {
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new AppError('Curso não encontrado', 404);

        const existingUser = await this.userModel.findByEmail(email);
        if (!existingUser && !password) throw new AppError('Bad Request', 400);

        const status = this.paymentGateway.authorize(card);
        if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

        const userId = existingUser
            ? existingUser.id
            : await this.userModel.create({
                name,
                email,
                passwordHash: await this.passwordService.hash(password)
            });

        const enrollmentId = await this.enrollmentModel.create(userId, courseId);
        await this.paymentModel.create({ enrollmentId, amount: course.price, status });
        await this.auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);

        this.logger.info(`Checkout concluído: curso ${courseId}, usuário ${userId}, matrícula ${enrollmentId}`);
        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = CheckoutService;
