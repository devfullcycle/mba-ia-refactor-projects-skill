const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

// Camada de rotas: apenas mapeia método + caminho para o controller.
function createRoutes({ checkoutController, adminController, userController, adminAuth }) {
    const router = express.Router();

    router.post('/checkout', asyncHandler((req, res) => checkoutController.checkout(req, res)));
    router.get('/admin/financial-report', adminAuth, asyncHandler((req, res) => adminController.financialReport(req, res)));
    router.delete('/users/:id', adminAuth, asyncHandler((req, res) => userController.remove(req, res)));

    return router;
}

module.exports = createRoutes;
