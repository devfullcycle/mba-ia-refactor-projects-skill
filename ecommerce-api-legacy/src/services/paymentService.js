// Gateway de pagamento simulado: regra de aprovação isolada do fluxo HTTP.
const { PAYMENT_STATUS } = require('../models/enrollmentModel');

// Simulação: cartões iniciados por este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

const maskCard = (card) => `**** **** **** ${String(card).slice(-4)}`;

class PaymentService {
  constructor({ gatewayKey, logger }) {
    this.gatewayKey = gatewayKey;
    this.logger = logger;
  }

  charge(card, amount) {
    this.logger.info(`Processando pagamento de ${amount} no cartão ${maskCard(card)}`);
    return String(card).startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  }
}

module.exports = { PaymentService, maskCard };
