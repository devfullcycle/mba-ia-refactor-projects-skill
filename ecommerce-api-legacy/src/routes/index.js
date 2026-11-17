const express = require('express');
const checkoutRoutes = require('./checkoutRoutes');
const reportRoutes = require('./reportRoutes');
const userRoutes = require('./userRoutes');

const router = express.Router();

router.use('/', checkoutRoutes);
router.use('/', reportRoutes);
router.use('/', userRoutes);

module.exports = router;
