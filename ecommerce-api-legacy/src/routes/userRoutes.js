const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function buildUserRoutes(userController, requireAdmin) {
    const router = express.Router();

    router.delete('/users/:id', requireAdmin, asyncHandler(async (req, res) => {
        await userController.delete(req.params.id);
        res.send('Usuário deletado');
    }));

    return router;
}

module.exports = { buildUserRoutes };
