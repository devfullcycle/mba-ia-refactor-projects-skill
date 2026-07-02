const express = require('express');
const adminAuth = require('../middlewares/adminAuth');

function createAdminRoutes(financialReportController, asyncHandler) {
    const router = express.Router();
    router.get('/financial-report', adminAuth, asyncHandler(financialReportController.getReport));
    return router;
}

module.exports = createAdminRoutes;
