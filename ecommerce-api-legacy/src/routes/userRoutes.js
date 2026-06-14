const express = require('express')
const { deleteUser } = require('../controllers/UserController')
const { requireAdminAuth } = require('../middlewares/auth')

const router = express.Router()

router.delete('/:id', requireAdminAuth, deleteUser)

module.exports = router
