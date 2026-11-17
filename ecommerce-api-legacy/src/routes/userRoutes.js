const express = require('express');
const UserController = require('../controllers/userController');

const router = express.Router();

router.delete('/users/:id', UserController.deleteUser);

module.exports = router;
