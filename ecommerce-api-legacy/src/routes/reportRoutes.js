const express = require('express')
const router = express.Router()
const { financialReport } = require('../controllers/reportController')
const { requireAdmin } = require('../middlewares/auth')

router.get('/financial-report', requireAdmin, financialReport)

module.exports = router
