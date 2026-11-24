const express = require('express');
const asyncHandler = require('../utils/asyncHandler');

// Apenas mapeia método + caminho → controller (e middlewares).
module.exports = ({ controllers, adminAuth }) => {
    const router = express.Router();

    router.post('/checkout', asyncHandler(controllers.checkout.create));
    router.get('/admin/financial-report', adminAuth, asyncHandler(controllers.report.financial));
    router.delete('/users/:id', adminAuth, asyncHandler(controllers.user.remove));

    return router;
};
