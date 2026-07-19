const AppError = require('../errors/AppError');

// Controller magro: valida a entrada, delega ao service e formata a resposta.
class CheckoutController {
    constructor({ checkoutService }) {
        this.checkoutService = checkoutService;
        this.checkout = this.checkout.bind(this);
    }

    async checkout(req, res, next) {
        try {
            const { usr, eml, pwd, c_id, card } = req.body || {};

            // Contrato original: usr, eml, c_id e card são obrigatórios (pwd é opcional).
            if (!usr || !eml || !c_id || !card) {
                throw new AppError('Bad Request', 400);
            }

            const courseId = Number(c_id);
            if (!Number.isInteger(courseId)) {
                throw new AppError('Bad Request', 400);
            }

            const result = await this.checkoutService.checkout({
                name: usr,
                email: eml,
                password: pwd,
                courseId,
                card,
            });

            res.status(200).json(result);
        } catch (err) {
            next(err);
        }
    }
}

module.exports = CheckoutController;
