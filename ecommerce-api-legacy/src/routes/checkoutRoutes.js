const express = require('express');
const CheckoutController = require('../controllers/checkoutController');

const router = express.Router();

router.post('/checkout', CheckoutController.processCheckout);

module.exports = router;
