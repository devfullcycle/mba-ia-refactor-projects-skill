const { NotFoundError } = require('./errors');
const { requirePositiveInteger } = require('./validators');

class UserController {
    constructor({ db, users, logger }) {
        Object.assign(this, { db, users, logger });
    }

    async delete(rawId) {
        const id = requirePositiveInteger(rawId);
        const deleted = await this.db.transaction(() => this.users.deleteById(id));
        if (!deleted) throw new NotFoundError('Usuário não encontrado');
        this.logger.info(`Usuário ${id} removido com matrículas e pagamentos`);
    }
}

module.exports = UserController;
