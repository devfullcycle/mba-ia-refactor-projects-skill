const { Router } = require('express');
const asyncHandler = require('../utils/asyncHandler');
const checkoutController = require('../controllers/checkoutController');

const router = Router();

router.post('/checkout', asyncHandler(checkoutController.checkout));

module.exports = router;
