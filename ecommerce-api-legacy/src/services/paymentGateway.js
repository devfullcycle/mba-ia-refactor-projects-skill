const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../constants');

// Gateway simulado. Nunca registra o número do cartão completo nem a chave do gateway.
function charge(card) {
    console.log(`Processando cartão final ${card.slice(-4)}`);
    return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

module.exports = { charge };
