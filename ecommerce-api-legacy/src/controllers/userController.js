const logger = require('../config/logger');
const UserModel = require('../models/userModel');
const { BadRequestError, NotFoundError } = require('../utils/errors');

async function deleteUser(req, res) {
    const userId = Number(req.params.id);
    if (!Number.isInteger(userId) || userId <= 0) throw new BadRequestError();

    const deleted = await UserModel.deleteById(userId);
    if (!deleted) throw new NotFoundError('Usuário não encontrado');

    logger.info('Usuário removido (matrículas e pagamentos em cascata)', { userId });
    res.send('Usuário deletado, junto com suas matrículas e pagamentos.');
}

module.exports = { deleteUser };
