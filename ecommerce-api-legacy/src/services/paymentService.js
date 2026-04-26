const PAYMENT_STATUS = Object.freeze({
  PAID: 'PAID',
  DENIED: 'DENIED',
});

function processPayment(cardNumber) {
  const approved = cardNumber && cardNumber.startsWith('4');
  return approved ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

module.exports = { processPayment, PAYMENT_STATUS };
