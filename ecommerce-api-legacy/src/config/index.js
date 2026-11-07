// Configuração central — tudo vem do ambiente, nada hardcoded.
try {
    require('dotenv').config();
} catch (e) {
    // dotenv é opcional; se ausente, usamos process.env diretamente.
}

module.exports = {
    port: process.env.PORT || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    // Segredos agora vêm exclusivamente do ambiente (ver .env.example).
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    dbUser: process.env.DB_USER || '',
    dbPass: process.env.DB_PASS || '',
    smtpUser: process.env.SMTP_USER || '',
};
