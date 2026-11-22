const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

// Gateway simulado: decide a autorização apenas pelo prefixo do cartão.
// Não registra nem retorna dados do cartão.
const paymentGateway = {
    authorize(cardNumber) {
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
};

module.exports = paymentGateway;
