'use strict';

const { NotFoundError } = require('../utils/errors');
const { validateUserId } = require('../validators/checkout.validator');

class UserController {
    constructor({ userRepository, logger }) {
        this.users = userRepository;
        this.logger = logger;
    }

    /**
     * Remove o usuário. As matrículas e pagamentos são removidos por cascade do schema —
     * o legado deixava os registros órfãos e ainda respondia 200 admitindo isso.
     */
    remove = async (req, res, next) => {
        try {
            const id = validateUserId(req.params.id);
            const removido = await this.users.deleteById(id);
            if (!removido) {
                throw new NotFoundError('Usuário não encontrado');
            }
            this.logger.info('Usuário removido', { userId: id });
            res.status(200).json({
                msg: 'Usuário deletado',
                detalhe: 'Matrículas e pagamentos associados foram removidos em cascata.',
            });
        } catch (error) {
            next(error);
        }
    };
}

module.exports = { UserController };
