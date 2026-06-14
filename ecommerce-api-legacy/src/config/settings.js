require('dotenv').config()

module.exports = {
    port: parseInt(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    adminApiKey: process.env.ADMIN_API_KEY || 'dev-admin-key',
}
