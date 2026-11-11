const { Router } = require('express');
const asyncHandler = require('../utils/asyncHandler');
const { requireAdminToken } = require('../middlewares/auth');
const userController = require('../controllers/userController');

const router = Router();

router.delete('/:id', requireAdminToken, asyncHandler(userController.deleteUser));

module.exports = router;
