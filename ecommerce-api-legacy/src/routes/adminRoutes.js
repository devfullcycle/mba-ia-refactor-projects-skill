const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { presentFinancialReport } = require('../views/financialReportView');

function buildAdminRoutes(financialReportController, requireAdmin) {
    const router = express.Router();

    router.get('/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
        const report = await financialReportController.build();
        res.json(presentFinancialReport(report));
    }));

    return router;
}

module.exports = { buildAdminRoutes };
