const express = require('express');
const asyncHandler = require('../utils/asyncHandler');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');

const router = express.Router();

router.post('/api/checkout', asyncHandler(checkoutController.checkout));
router.get('/api/admin/financial-report', asyncHandler(reportController.financialReport));
router.delete('/api/users/:id', asyncHandler(userController.deleteUser));

module.exports = router;
