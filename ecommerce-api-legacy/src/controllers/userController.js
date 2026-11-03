const { NotFoundError, ValidationError } = require('../utils/errors');

class UserController {
  constructor({ db, userModel, logger }) {
    this.db = db;
    this.users = userModel;
    this.logger = logger;
  }

  async deleteUser(rawId) {
    const id = Number(rawId);
    if (!Number.isInteger(id) || id <= 0) throw new ValidationError('Bad Request');

    const deleted = await this.db.transaction((tx) => this.users.deleteWithDependents(id, tx));
    if (!deleted) throw new NotFoundError('Usuário não encontrado');

    this.logger.info(`Usuário ${id} removido com matrículas e pagamentos`);
    return 'Usuário deletado, junto com suas matrículas e pagamentos.';
  }
}

module.exports = UserController;
