const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');

const router = express.Router();

router.post('/checkout', checkoutController.checkout);
router.get('/admin/financial-report', reportController.getFinancialReport);
router.delete('/users/:id', userController.deleteUser);

module.exports = router;
