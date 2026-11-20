const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const { toCheckoutInput, presentCheckout } = require('../views/checkoutView');

function buildCheckoutRoutes(checkoutController) {
    const router = express.Router();

    router.post('/checkout', asyncHandler(async (req, res) => {
        const result = await checkoutController.checkout(toCheckoutInput(req.body));
        res.status(200).json(presentCheckout(result));
    }));

    return router;
}

module.exports = { buildCheckoutRoutes };
