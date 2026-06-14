const express = require('express')
const { processCheckout } = require('../controllers/CheckoutController')

const router = express.Router()

router.post('/', processCheckout)

module.exports = router
