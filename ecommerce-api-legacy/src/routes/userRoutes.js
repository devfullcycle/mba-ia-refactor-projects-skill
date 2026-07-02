const express = require('express');

function createUserRoutes(userController, asyncHandler) {
    const router = express.Router();
    router.delete('/users/:id', asyncHandler(userController.deleteUser));
    return router;
}

module.exports = createUserRoutes;
