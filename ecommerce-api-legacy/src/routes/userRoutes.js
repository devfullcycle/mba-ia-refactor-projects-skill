const express = require('express');
const userController = require('../controllers/userController');

function createUserRoutes(db) {
  const router = express.Router();

  router.delete('/users/:id', async (req, res, next) => {
    try {
      const result = await userController.deleteUser(db, req.params.id);
      res.json(result);
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = createUserRoutes;
