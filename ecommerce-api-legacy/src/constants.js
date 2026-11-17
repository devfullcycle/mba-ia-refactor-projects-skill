const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED'
});

// Regra do gateway simulado: cartões iniciados em "4" são aprovados.
const APPROVED_CARD_PREFIX = '4';

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX };
