'use strict';

const express = require('express');

/**
 * Camada de View: apenas mapeia caminho → controller e declara o middleware da rota.
 * Nenhuma lógica de negócio e nenhum acesso a dados aqui.
 */
function createRouter({ checkoutController, reportController, userController, requireAdmin }) {
    const router = express.Router();

    router.post('/checkout', checkoutController.create);

    router.get('/admin/financial-report', requireAdmin, reportController.financial);

    router.delete('/users/:id', requireAdmin, userController.remove);

    return router;
}

module.exports = { createRouter };
