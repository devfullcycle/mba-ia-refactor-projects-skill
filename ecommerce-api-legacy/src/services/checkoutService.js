const AppError = require('../errors/AppError');
const passwordService = require('./passwordService');
const paymentGateway = require('./paymentGateway');

const DEFAULT_PASSWORD = '123456';

// Orquestra a regra de negócio do checkout: valida curso, resolve/cria usuário,
// cobra o pagamento e persiste matrícula + pagamento + auditoria de forma atômica.
class CheckoutService {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel }) {
        this.db = db;
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
    }

    async checkout({ name, email, password, courseId, card }) {
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new AppError('Curso não encontrado', 404);

        let user = await this.userModel.findByEmail(email);
        let userId;
        if (!user) {
            const passHash = passwordService.hash(password || DEFAULT_PASSWORD);
            userId = await this.userModel.create(name, email, passHash);
        } else {
            userId = user.id;
        }

        const status = paymentGateway.charge(card);
        if (status === paymentGateway.PaymentStatus.DENIED) {
            throw new AppError('Pagamento recusado', 400);
        }

        // Matrícula + pagamento + log numa única transação (atomicidade).
        const enrollmentId = await this.db.transaction(async () => {
            const enrId = await this.enrollmentModel.create(userId, courseId);
            await this.paymentModel.create(enrId, course.price, status);
            await this.auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);
            return enrId;
        });

        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = CheckoutService;
