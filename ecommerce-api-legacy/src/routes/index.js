/**
 * Rotas de checkout e administrativas.
 * Rotas finas: extraem dados e delegam a controllers.
 */
const express = require('express');
const { handleCheckout } = require('../controllers/checkoutController');
const { handleFinancialReport } = require('../controllers/reportController');
const { removeUser } = require('../controllers/userController');
const { requireAdmin } = require('../middlewares/authMiddleware');

const router = express.Router();

router.post('/checkout', handleCheckout);

// Relatório financeiro protegido por autenticação de admin.
router.get('/admin/financial-report', requireAdmin, handleFinancialReport);

router.delete('/users/:id', removeUser);

module.exports = router;