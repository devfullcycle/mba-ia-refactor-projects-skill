// Gateway de pagamento (simulado). Preserva a regra original de aprovação,
// mas NUNCA loga o cartão completo nem a chave do gateway.
class PaymentGateway {
    constructor(apiKey, logger) {
        this._apiKey = apiKey;
        this._logger = logger;
    }

    charge(card, amount) {
        const masked = `****${String(card).slice(-4)}`;
        this._logger.info(`Processando pagamento de ${amount} (cartão ${masked})`);
        const approved = String(card).startsWith('4');
        return { status: approved ? 'PAID' : 'DENIED' };
    }
}

module.exports = PaymentGateway;
