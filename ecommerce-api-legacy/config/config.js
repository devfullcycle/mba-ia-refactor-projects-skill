const crypto = require('crypto');
require('dotenv').config();

const config = {
    dbUser: process.env.DB_USER,
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpUser: process.env.SMTP_USER,
    port: process.env.PORT || 3000
};

module.exports = config;
