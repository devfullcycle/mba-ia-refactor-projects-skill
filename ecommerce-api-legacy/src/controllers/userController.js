const { validateUserId } = require('../validators/checkoutValidator');

const DELETE_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

class UserController {
    constructor({ userService }) {
        this.userService = userService;
    }

    async remove(req, res) {
        const id = validateUserId(req.params.id);
        await this.userService.remove(id);
        res.send(DELETE_MESSAGE);
    }
}

module.exports = UserController;
