const express = require('express');
const ReportController = require('../controllers/reportController');

const router = express.Router();

router.get('/admin/financial-report', ReportController.getFinancialReport);

module.exports = router;
