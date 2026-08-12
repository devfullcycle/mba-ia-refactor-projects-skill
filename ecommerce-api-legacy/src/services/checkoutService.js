/**
 * Serviço de checkout — orquestra regras de negócio do fluxo de compra.
 * (Rota → controller → service → models)
 */
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const { paymentGatewayStatus, cacheSet } = require('../utils/security');

class CheckoutError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.status = status;
    }
}

function validateInput({ usr, eml, pwd, c_id, card }) {
    if (!usr || !eml || !pwd) throw new CheckoutError('Bad Request', 400);
    if (!c_id) throw new CheckoutError('Bad Request', 400);
    if (!card || typeof card !== 'string' || card.length < 4) {
        throw new CheckoutError('Bad Request', 400);
    }
    if (pwd.length < 6) throw new CheckoutError('Senha deve ter ao menos 6 caracteres', 400);
}

async function processCheckout({ usr, eml, pwd, c_id, card }) {
    validateInput({ usr, eml, pwd, c_id, card });

    const course = await courseModel.findActiveById(c_id);
    if (!course) throw new CheckoutError('Curso não encontrado', 404);

    // Garante usuário (cria se não existir), com senha hasheada.
    let user = await userModel.findByEmail(eml);
    if (!user) {
        user = await userModel.create(usr, eml, pwd);
    } else {
        const ok = userModel.verifyPassword(pwd, user.pass);
        if (!ok) throw new CheckoutError('Senha inválida para usuário existente', 401);
    }

    // Gateway de pagamento (sem expor a chave em logs).
    const status = paymentGatewayStatus(card);
    if (status === 'DENIED') throw new CheckoutError('Pagamento recusado', 400);

    const enrollmentId = await courseModel.createEnrollment(user.id, course.id);
    await courseModel.createPayment(enrollmentId, course.price, status);
    await courseModel.writeAuditLog(`Checkout curso ${course.id} por ${user.id}`);

    // Cache request-scoped (não global mutável).
    cacheSet(`last_checkout_${user.id}`, course.title);

    return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { processCheckout, CheckoutError };