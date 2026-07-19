const express = require('express');
const requireAdmin = require('../middlewares/requireAdmin');

// Camada "view" das APIs: apenas mapeia caminho + método HTTP → controller.
// Não contém regra de negócio nem acesso a dados. Preserva os contratos originais.
function buildRouter({ checkoutController, reportController, userController }) {
    const router = express.Router();

    router.post('/checkout', checkoutController.checkout);

    // Rotas administrativas/destrutivas protegidas por autenticação de admin.
    router.get('/admin/financial-report', requireAdmin, reportController.financialReport);
    router.delete('/users/:id', requireAdmin, userController.remove);

    return router;
}

module.exports = buildRouter;
