const { Router } = require('express');

function createCheckoutRoutes({ checkoutController }) {
    const router = Router();
    // SEC-04: rota pública apenas para cadastro de novo usuário. A posse de
    // uma conta existente é validada no CheckoutService (e-mail + senha),
    // que nunca aceita id/dono/role vindos do body.
    router.post('/checkout', checkoutController.checkout);
    return router;
}

module.exports = { createCheckoutRoutes };
