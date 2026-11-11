const config = require('../config/config');
const logger = require('../config/logger');
const { PAYMENT_STATUS } = require('../utils/constants');

// Simulação do gateway herdada do legado: só cartões com bandeira Visa (prefixo "4") são aprovados.
const APPROVED_CARD_PREFIX = '4';
const MASK_VISIBLE_DIGITS = 4;

function maskCard(cardNumber) {
    return `****${String(cardNumber).slice(-MASK_VISIBLE_DIGITS)}`;
}

const PaymentService = {
    // A chave do gateway (config.paymentGatewayKey) seria usada aqui na integração real; nunca é logada.
    authorize({ cardNumber, amount }) {
        const status = String(cardNumber).startsWith(APPROVED_CARD_PREFIX)
            ? PAYMENT_STATUS.PAID
            : PAYMENT_STATUS.DENIED;
        logger.info('Pagamento processado', {
            card: maskCard(cardNumber),
            amount,
            status,
            gatewayConfigured: Boolean(config.paymentGatewayKey),
        });
        return status;
    },
};

module.exports = PaymentService;
