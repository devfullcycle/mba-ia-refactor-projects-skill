const config = {
    dbUser: process.env.DB_USER || "admin_master",
    dbPass: process.env.DB_PASS || "dev_db_password",
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "pk_test_sample_gateway_key",
    smtpUser: process.env.SMTP_USER || "no-reply@fullcycle.com.br",
    port: parseInt(process.env.PORT, 10) || 3000,
    nodeEnv: process.env.NODE_ENV || "development"
};

module.exports = config;
