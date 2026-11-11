const { Router } = require('express');
const asyncHandler = require('../utils/asyncHandler');
const { requireAdminToken } = require('../middlewares/auth');
const reportController = require('../controllers/reportController');

const router = Router();

router.get('/financial-report', requireAdminToken, asyncHandler(reportController.getFinancialReport));

module.exports = router;
