const { validateCheckout } = require('../validators/requestValidator');

module.exports = ({ checkoutService }) => ({
    async create(req, res) {
        const input = validateCheckout(req.body);
        const { enrollmentId } = await checkoutService.checkout(input);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }
});
