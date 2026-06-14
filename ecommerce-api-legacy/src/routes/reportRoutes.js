const express = require('express')
const { getFinancialReport } = require('../controllers/ReportController')
const { requireAdminAuth } = require('../middlewares/auth')

const router = express.Router()

router.get('/financial-report', requireAdminAuth, getFinancialReport)

module.exports = router
