// Camada de roteamento — delega imediatamente aos controllers.
// Mantém os mesmos paths e métodos do projeto original.
module.exports = function registerRoutes(app, { checkoutController, reportController, userController }) {
    app.post('/api/checkout', (req, res, next) => checkoutController.checkout(req, res, next));
    app.get('/api/admin/financial-report', (req, res, next) => reportController.financialReport(req, res, next));
    app.delete('/api/users/:id', (req, res, next) => userController.remove(req, res, next));
};
