class UserService {
    constructor({ userModel, logger }) {
        this.userModel = userModel;
        this.logger = logger;
    }

    async remove(id) {
        const { changes } = await this.userModel.deleteById(id);
        this.logger.info(`Usuário ${id} removido (${changes} registro(s))`);
    }
}

module.exports = UserService;
