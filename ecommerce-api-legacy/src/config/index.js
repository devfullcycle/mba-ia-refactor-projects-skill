require('dotenv').config();

const config = {
  port: parseInt(process.env.PORT, 10) || 3000,
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
  smtpPass: process.env.SMTP_PASS || '',
  dbUser: process.env.DB_USER || '',
  dbPass: process.env.DB_PASS || '',
};

module.exports = config;
