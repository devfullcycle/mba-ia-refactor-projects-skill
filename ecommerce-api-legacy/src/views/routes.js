// Camada de View/rotas: mapeia HTTP → controller e serializa a resposta. Sem regra de negócio.
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function createRoutes({ checkoutController, reportController, userController, requireAdmin }) {
  const router = express.Router();

  router.post('/api/checkout', asyncHandler(async (req, res) => {
    const result = await checkoutController.checkout(req.body);
    res.status(200).json(result);
  }));

  router.get('/api/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
    res.json(await reportController.financialReport());
  }));

  router.delete('/api/users/:id', requireAdmin, asyncHandler(async (req, res) => {
    res.send(await userController.deleteUser(req.params.id));
  }));

  return router;
}

module.exports = createRoutes;
