// Gateway de pagamento simulado (mesma regra do legado: cartões iniciados em "4" são aprovados).
// Substituível por um adaptador real injetado no composition root.
const APPROVED_CARD_PREFIX = '4';

class FakePaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    async authorize({ cardNumber, amount }) {
        // Nunca registrar o número completo do cartão nem a chave do gateway.
        this.logger.info(`Processando pagamento de ${amount} no cartão ****${cardNumber.slice(-4)}`);
        return { approved: cardNumber.startsWith(APPROVED_CARD_PREFIX) };
    }
}

module.exports = FakePaymentGateway;
