'use strict';

const { STATUS_PAID, STATUS_DENIED } = require('../models/payment.repository');

/** Prefixo aceito pelo simulador de pagamento (era o literal "4" solto no meio da rota). */
const SIMULATOR_APPROVED_PREFIX = '4';

/**
 * Gateway de pagamento simulado, isolado atrás de uma interface: trocar por um provedor
 * real não altera controller nem repository.
 *
 * Nunca registra o número do cartão — o legado logava o PAN completo junto com a chave
 * do gateway.
 */
class FakePaymentGateway {
    constructor({ logger, apiKey = null }) {
        this.logger = logger;
        this.apiKey = apiKey;
    }

    static last4(card) {
        return String(card).slice(-4);
    }

    async charge({ card, amount }) {
        const approved = String(card).startsWith(SIMULATOR_APPROVED_PREFIX);
        const status = approved ? STATUS_PAID : STATUS_DENIED;

        this.logger.info('Cobrança processada', {
            cardLast4: FakePaymentGateway.last4(card),
            amount,
            status,
            gateway: this.apiKey ? 'configurado' : 'simulado',
        });

        return { status, approved, amount };
    }
}

module.exports = { FakePaymentGateway, SIMULATOR_APPROVED_PREFIX };
