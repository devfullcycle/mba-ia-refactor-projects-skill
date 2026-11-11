const { Router } = require('express');
const checkoutRoutes = require('./checkoutRoutes');
const adminRoutes = require('./adminRoutes');
const userRoutes = require('./userRoutes');

const router = Router();

router.use('/', checkoutRoutes);      // POST   /api/checkout
router.use('/admin', adminRoutes);    // GET    /api/admin/financial-report
router.use('/users', userRoutes);     // DELETE /api/users/:id

module.exports = router;
