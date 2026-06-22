const express = require('express')
const router = express.Router()
const { login, deleteUser } = require('../controllers/userController')
const { requireAdmin } = require('../middlewares/auth')

router.post('/login', login)
router.delete('/:id', requireAdmin, deleteUser)

module.exports = router
