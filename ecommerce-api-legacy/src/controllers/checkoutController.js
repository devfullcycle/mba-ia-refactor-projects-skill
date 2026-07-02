const { hashPassword } = require('../services/passwordService');
const { chargeCard } = require('../services/paymentGatewayService');
const logger = require('../config/logger');

class CheckoutController {
    constructor({ courseModel, userModel, enrollmentModel, paymentModel, auditLogModel, cacheService }) {
        this.courseModel = courseModel;
        this.userModel = userModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.cacheService = cacheService;
    }

    checkout = async (req, res) => {
        const {
            usr: userName,
            eml: userEmail,
            pwd: userPassword,
            c_id: courseId,
            card: cardNumber,
        } = req.body;

        if (!userName || !userEmail || !courseId || !cardNumber) {
            return res.status(400).send('Bad Request');
        }

        const course = await this.courseModel.findActiveById(courseId);
        if (!course) return res.status(404).send('Curso não encontrado');

        const existingUser = await this.userModel.findByEmail(userEmail);
        let userId;

        if (!existingUser) {
            const passwordHash = await hashPassword(userPassword || '123456');
            const createdUser = await this.userModel.create({
                name: userName,
                email: userEmail,
                passwordHash,
            });
            userId = createdUser.lastID;
        } else {
            userId = existingUser.id;
        }

        logger.info('Processando checkout', { courseId, userId });
        const { status } = chargeCard(cardNumber);
        if (status === 'DENIED') return res.status(400).send('Pagamento recusado');

        const enrollment = await this.enrollmentModel.create(userId, courseId);
        await this.paymentModel.create(enrollment.lastID, course.price, status);
        await this.auditLogModel.create(`Checkout curso ${courseId} por ${userId}`);

        this.cacheService.set(`last_checkout_${userId}`, course.title);

        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollment.lastID });
    };
}

module.exports = CheckoutController;
