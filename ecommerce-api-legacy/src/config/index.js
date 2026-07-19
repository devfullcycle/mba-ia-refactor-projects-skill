// Configuração centralizada — segredos vêm do ambiente (process.env), nunca hardcoded.
// Veja .env.example para as variáveis esperadas.
module.exports = {
    port: parseInt(process.env.PORT, 10) || 3000,
    db: {
        // Mantidos por compatibilidade; hoje o banco é SQLite in-memory e não usa credenciais.
        user: process.env.DB_USER || '',
        pass: process.env.DB_PASS || '',
        path: process.env.DB_PATH || ':memory:',
    },
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    // Token administrativo para proteger rotas sensíveis. Defina ADMIN_TOKEN em produção.
    adminToken: process.env.ADMIN_TOKEN || 'dev-admin-token',
};
