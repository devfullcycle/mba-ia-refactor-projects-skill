const env = require('../config/env');
const logger = require('../config/logger');

const APPROVED_CARD_PREFIX = '4';

function chargeCard(cardNumber) {
    logger.info('Processando cobrança no gateway de pagamento', {
        gatewayKeyPrefix: env.paymentGatewayKey.slice(0, 6),
    });

    const approved = cardNumber.startsWith(APPROVED_CARD_PREFIX);
    return { status: approved ? 'PAID' : 'DENIED' };
}

module.exports = { chargeCard };
