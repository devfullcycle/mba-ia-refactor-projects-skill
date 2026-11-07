const HttpError = require('../middlewares/httpError');

// Regra de negócio do checkout — antes espalhada em callbacks aninhados no
// handler da rota. Agora linear, com async/await e dependências injetadas.
class CheckoutService {
    constructor({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, passwordService, paymentGateway, cache }) {
        this._users = userModel;
        this._courses = courseModel;
        this._enrollments = enrollmentModel;
        this._payments = paymentModel;
        this._auditLogs = auditLogModel;
        this._passwords = passwordService;
        this._gateway = paymentGateway;
        this._cache = cache;
    }

    async checkout({ name, email, password, courseId, card }) {
        const course = await this._courses.findActiveById(courseId);
        if (!course) {
            throw new HttpError(404, 'Curso não encontrado');
        }

        let user = await this._users.findByEmail(email);
        if (!user) {
            const passwordHash = await this._passwords.hash(password || '123456');
            const userId = await this._users.create({ name, email, passwordHash });
            user = { id: userId };
        }

        const payment = this._gateway.charge(card, course.price);
        if (payment.status === 'DENIED') {
            throw new HttpError(400, 'Pagamento recusado');
        }

        const enrollmentId = await this._enrollments.create(user.id, courseId);
        await this._payments.create(enrollmentId, course.price, payment.status);
        await this._auditLogs.create(`Checkout curso ${courseId} por ${user.id}`);
        this._cache.set(`last_checkout_${user.id}`, course.title);

        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = CheckoutService;
