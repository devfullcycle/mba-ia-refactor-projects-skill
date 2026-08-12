/**
 * Controller de checkout — fluxo HTTP -> service.
 */
const { processCheckout, CheckoutError } = require('../services/checkoutService');

async function handleCheckout(req, res, next) {
    try {
        const result = await processCheckout(req.body);
        res.status(200).json(result);
    } catch (err) {
        if (err instanceof CheckoutError) {
            return res.status(err.status).json({ error: err.message });
        }
        next(err);
    }
}

module.exports = { handleCheckout };