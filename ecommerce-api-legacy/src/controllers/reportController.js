/**
 * Controller de relatório — fluxo HTTP -> service.
 */
const { buildFinancialReport } = require('../services/reportService');

async function handleFinancialReport(req, res, next) {
    try {
        const report = await buildFinancialReport();
        res.json(report);
    } catch (err) {
        next(err);
    }
}

module.exports = { handleFinancialReport };