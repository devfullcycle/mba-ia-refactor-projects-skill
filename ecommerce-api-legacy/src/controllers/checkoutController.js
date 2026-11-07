const HttpError = require('../middlewares/httpError');

class CheckoutController {
    constructor(checkoutService) {
        this._service = checkoutService;
    }

    async checkout(req, res, next) {
        try {
            // Normaliza os nomes crípticos do payload original.
            const name = req.body.usr;
            const email = req.body.eml;
            const password = req.body.pwd;
            const courseId = req.body.c_id;
            const card = req.body.card;

            if (!name || !email || !courseId || !card) {
                throw new HttpError(400, 'Bad Request');
            }

            const result = await this._service.checkout({ name, email, password, courseId, card });
            res.status(200).json(result);
        } catch (err) {
            next(err);
        }
    }
}

module.exports = CheckoutController;
