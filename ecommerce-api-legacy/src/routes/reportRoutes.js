const express = require('express');
const reportController = require('../controllers/reportController');

function createReportRoutes(db) {
  const router = express.Router();

  router.get('/admin/financial-report', async (_req, res, next) => {
    try {
      const report = await reportController.getFinancialReport(db);
      res.json(report);
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = createReportRoutes;
