const UserModel = require('../models/userModel');
const CourseModel = require('../models/courseModel');
const PaymentModel = require('../models/paymentModel');
const config = require('../config/config');
const { maskCardNumber } = require('../utils/security');

class CheckoutController {
    static async processCheckout(req, res, next) {
        try {
            const username = req.body.usr || req.body.username;
            const email = req.body.eml || req.body.email;
            const password = req.body.pwd || req.body.password;
            const courseId = req.body.c_id || req.body.courseId;
            const cardNumber = req.body.card || req.body.cardNumber;

            // Validação de campos obrigatórios
            if (!username || !email || !courseId || !cardNumber) {
                return res.status(400).send("Bad Request");
            }

            // Busca curso ativo
            const course = await CourseModel.findActiveById(courseId);
            if (!course) {
                return res.status(404).send("Curso não encontrado");
            }

            // Localiza ou cria usuário
            let user = await UserModel.findByEmail(email);
            if (!user) {
                user = await UserModel.create({
                    name: username,
                    email: email,
                    password: password || "123456"
                });
            }

            // Simulação de gateway de pagamento com mascaramento de dados (PCI-DSS)
            const maskedCard = maskCardNumber(cardNumber);
            console.log(`Processando cartão ${maskedCard} na chave ${config.paymentGatewayKey}`);

            const paymentStatus = cardNumber.startsWith("4") ? "PAID" : "DENIED";
            if (paymentStatus === "DENIED") {
                return res.status(400).send("Pagamento recusado");
            }

            // Cria matrícula e pagamento de forma sequencial e segura
            const enrollmentId = await PaymentModel.createEnrollment(user.id, course.id);
            await PaymentModel.createPayment(enrollmentId, course.price, paymentStatus);

            // Registro de auditoria
            await PaymentModel.createAuditLog(`Checkout curso ${course.id} por ${user.id}`);

            return res.status(200).json({
                msg: "Sucesso",
                enrollment_id: enrollmentId
            });
        } catch (error) {
            next(error);
        }
    }
}

module.exports = CheckoutController;
