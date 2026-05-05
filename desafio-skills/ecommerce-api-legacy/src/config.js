const port = Number(process.env.PORT) || 3000;

module.exports = {
  port,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
  dbUser: process.env.DB_USER || '',
  dbPass: process.env.DB_PASS || '',
};
