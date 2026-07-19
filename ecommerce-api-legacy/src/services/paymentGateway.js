const config = require('../config');

// Encapsula a integração com o gateway de pagamento.
// Regra de aprovação isolada aqui (antes era um cc.startsWith("4") mágico no handler).
const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Cartões que começam com este prefixo são aprovados (simulação do gateway legado).
const APPROVED_CARD_PREFIX = '4';

function charge(card) {
    // Não logamos o número do cartão nem a chave do gateway (dados sensíveis / PCI).
    if (!config.paymentGatewayKey) {
        // Sem chave configurada, seguimos a simulação sem expor segredos.
    }
    return String(card).startsWith(APPROVED_CARD_PREFIX)
        ? PaymentStatus.PAID
        : PaymentStatus.DENIED;
}

module.exports = { charge, PaymentStatus };
