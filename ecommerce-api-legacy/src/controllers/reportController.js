const PaymentModel = require('../models/paymentModel');

class ReportController {
    static async getFinancialReport(req, res, next) {
        try {
            const report = await PaymentModel.getFinancialReport();
            return res.status(200).json(report);
        } catch (error) {
            next(error);
        }
    }
}

module.exports = ReportController;
