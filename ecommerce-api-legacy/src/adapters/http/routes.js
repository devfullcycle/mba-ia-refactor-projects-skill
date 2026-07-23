'use strict';

const express = require('express');
const { authenticate, requireRole } = require('./authentication');
const { toCheckoutCommand, toDeleteUserCommand } = require('./validation');
const { presentCheckout, presentFinancialReport, presentDeleteUser } = require('./presenters');

/**
 * View/adapter HTTP: apenas transporte, parsing e apresentação.
 * Toda orquestração vive nos casos de uso (application/*).
 */
function createRouter({ apiKeys, checkoutUseCase, financialReportUseCase, deleteUserUseCase }) {
    const router = express.Router();
    const requireAuth = authenticate(apiKeys);
    const requireAdmin = requireRole('admin');

    // Envolve handlers síncronos para encaminhar exceções ao error-handler central.
    const wrap = (handler) => (req, res, next) => {
        try {
            handler(req, res);
        } catch (error) {
            next(error);
        }
    };

    router.post(
        '/api/checkout',
        requireAuth,
        wrap((req, res) => {
            const command = toCheckoutCommand(req.body);
            const result = checkoutUseCase.execute(command, req.auth);
            res.status(200).json(presentCheckout(result));
        })
    );

    router.get(
        '/api/admin/financial-report',
        requireAuth,
        requireAdmin,
        wrap((req, res) => {
            const report = financialReportUseCase.execute();
            res.status(200).json(presentFinancialReport(report));
        })
    );

    router.delete(
        '/api/users/:id',
        requireAuth,
        requireAdmin,
        wrap((req, res) => {
            const command = toDeleteUserCommand(req.params);
            const result = deleteUserUseCase.execute(command);
            res.status(200).json(presentDeleteUser(result));
        })
    );

    return router;
}

module.exports = { createRouter };
