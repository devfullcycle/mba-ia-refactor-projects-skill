require('dotenv').config()

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  secret: process.env.SECRET_KEY || 'dev-only-fallback',
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
  smtpPass: process.env.SMTP_PASS || '',
  APPROVED_CARD_PREFIXES: ['4'],
}
