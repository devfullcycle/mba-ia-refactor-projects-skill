const express = require('express');

function createCheckoutRoutes(checkoutController, asyncHandler) {
    const router = express.Router();
    router.post('/checkout', asyncHandler(checkoutController.checkout));
    return router;
}

module.exports = createCheckoutRoutes;
