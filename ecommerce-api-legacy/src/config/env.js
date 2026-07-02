const env = {
    port: parseInt(process.env.PORT, 10) || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'dev_pk_test_0000000000000000',
    adminApiKey: process.env.ADMIN_API_KEY || 'dev-admin-key-change-me',
};

module.exports = env;
