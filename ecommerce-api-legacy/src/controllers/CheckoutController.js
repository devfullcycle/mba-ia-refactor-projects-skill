const CheckoutService = require('../services/CheckoutService')
const { getDb } = require('../database')

async function processCheckout(req, res, next) {
    const { username, email, password, courseId, cardNumber } = req.body

    if (!username || !email || !courseId || !cardNumber) {
        return res.status(400).json({ error: 'Missing required fields: username, email, courseId, cardNumber' })
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return res.status(400).json({ error: 'Invalid email format' })
    }
    if (!Number.isInteger(Number(courseId)) || Number(courseId) <= 0) {
        return res.status(400).json({ error: 'courseId must be a positive integer' })
    }

    try {
        const service = new CheckoutService(getDb())
        const { enrollmentId } = await service.processCheckout({
            username,
            email,
            password,
            courseId: Number(courseId),
            cardNumber,
        })
        res.status(201).json({ msg: 'Sucesso', enrollment_id: enrollmentId })
    } catch (err) {
        next(err)
    }
}

module.exports = { processCheckout }
