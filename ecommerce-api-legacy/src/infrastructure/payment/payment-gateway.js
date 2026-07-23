'use strict';

/**
 * Adapter de pagamento. Simulação local (não há gateway real neste desafio),
 * mantendo a regra observável original: cartão iniciado em "4" é aprovado.
 * Nunca registrar o PAN completo em log (F-001) — ver logger.redactCard.
 */
function createPaymentGateway(gatewayKey) {
    if (!gatewayKey) {
        throw new Error('PaymentGateway requer uma chave configurada');
    }

    return {
        charge({ card, amount }) {
            if (typeof card !== 'string' || card.length === 0) {
                return { status: 'DENIED', reason: 'invalid_card' };
            }
            const approved = card.startsWith('4');
            return {
                status: approved ? 'PAID' : 'DENIED',
                reason: approved ? null : 'card_declined',
                amount,
            };
        },
    };
}

module.exports = { createPaymentGateway };
