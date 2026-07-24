'use strict';

const { validateCheckout } = require('../validators/checkout.validator');

/** Controller: valida a entrada, chama o service e define a resposta HTTP. */
class CheckoutController {
    constructor({ checkoutService }) {
        this.service = checkoutService;
    }

    create = async (req, res, next) => {
        try {
            const payload = validateCheckout(req.body);
            const result = await this.service.execute(payload);
            res.status(200).json(result);
        } catch (error) {
            next(error);
        }
    };
}

module.exports = { CheckoutController };
