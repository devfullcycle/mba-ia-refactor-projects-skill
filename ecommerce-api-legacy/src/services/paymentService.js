const { APPROVED_CARD_PREFIXES } = require('../config/settings')

function processPayment(cardNumber, amount) {
  const approved = APPROVED_CARD_PREFIXES.some(prefix => cardNumber.startsWith(prefix))
  return {
    status: approved ? 'PAID' : 'DENIED',
    amount,
  }
}

module.exports = { processPayment }
