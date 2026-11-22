const { validateCheckout } = require('../validators/checkoutValidator');

class CheckoutController {
    constructor({ checkoutService }) {
        this.checkoutService = checkoutService;
    }

    async checkout(req, res) {
        const input = validateCheckout(req.body);
        const result = await this.checkoutService.checkout(input);
        res.status(200).json(result);
    }
}

module.exports = CheckoutController;
