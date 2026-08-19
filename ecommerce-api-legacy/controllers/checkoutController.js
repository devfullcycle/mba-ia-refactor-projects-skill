const UserModel = require('../models/userModel');
const CourseModel = require('../models/courseModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');
const AuditLogModel = require('../models/auditLogModel');
const { logAndCache, secureCrypto } = require('../utils/utils');
const config = require('../config/config');

const checkout = async (req, res, next) => {
    try {
        const username = req.body.usr;
        const email = req.body.eml;
        const password = req.body.pwd;
        const courseId = req.body.c_id;
        const cardNumber = req.body.card;

        if (!username || !email || !courseId || !cardNumber) {
            return res.status(400).send("Bad Request");
        }

        const course = await CourseModel.getActiveById(courseId);
        if (!course) {
            return res.status(404).send("Curso não encontrado");
        }

        let user = await UserModel.getByEmail(email);
        let userId;

        if (!user) {
            const passwordHash = secureCrypto(password || "123456");
            userId = await UserModel.create(username, email, passwordHash);
        } else {
            userId = user.id;
        }

        console.log(`Processando cartão ${cardNumber} na chave ${config.paymentGatewayKey}`);
        const status = cardNumber.startsWith("4") ? "PAID" : "DENIED";

        if (status === "DENIED") {
            return res.status(400).send("Pagamento recusado");
        }

        const enrollmentId = await EnrollmentModel.create(userId, courseId);
        await PaymentModel.create(enrollmentId, course.price, status);
        await AuditLogModel.log(`Checkout curso ${courseId} por ${userId}`);

        logAndCache(`last_checkout_${userId}`, course.title);

        return res.status(200).json({ msg: "Sucesso", enrollment_id: enrollmentId });
    } catch (err) {
        next(err);
    }
};

module.exports = { checkout };
