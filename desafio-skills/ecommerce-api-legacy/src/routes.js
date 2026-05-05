const express = require('express');

function setupRoutes(app, services) {
  const router = express.Router();

  router.post('/checkout', async (req, res, next) => {
    try {
      const out = await services.checkout.processCheckout(req.body);
      res.status(200).json(out);
    } catch (e) {
      next(e);
    }
  });

  router.get('/admin/financial-report', async (req, res, next) => {
    try {
      const report = await services.report.financialReport();
      res.json(report);
    } catch (e) {
      next(e);
    }
  });

  router.delete('/users/:id', async (req, res, next) => {
    try {
      await services.users.deleteUser(req.params.id);
      res.send('Usuário deletado; matrículas e pagamentos relacionados foram removidos.');
    } catch (e) {
      next(e);
    }
  });

  app.use('/api', router);
}

module.exports = { setupRoutes };
