'use strict';

const PAID = 'PAID';
const DENIED = 'DENIED';

function isPaid(payment) {
    return Boolean(payment) && payment.status === PAID;
}

module.exports = { PAID, DENIED, isPaid };
