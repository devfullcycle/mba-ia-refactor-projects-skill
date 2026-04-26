const express = require('express');
const checkoutController = require('../controllers/checkoutController');

function createCheckoutRoutes(db) {
  const router = express.Router();

  router.post('/checkout', async (req, res, next) => {
    try {
      const result = await checkoutController.checkout(db, {
        userName: req.body.userName,
        email: req.body.email,
        password: req.body.password,
        courseId: req.body.courseId,
        cardNumber: req.body.cardNumber,
      });
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = createCheckoutRoutes;
