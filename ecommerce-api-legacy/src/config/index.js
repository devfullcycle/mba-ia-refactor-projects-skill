const path = require('path');

// Configurações lidas de variáveis de ambiente (segredos nunca hardcoded).
const config = {
    port: Number(process.env.PORT || 3000),
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    dbFile: process.env.DB_FILE || ':memory:',
    minPasswordLength: 6,
    isProduction: process.env.NODE_ENV === 'production',
};

// Re-export da config (compat + facilidade de uso pelos módulos).
module.exports = { config };