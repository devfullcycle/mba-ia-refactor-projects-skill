// Controller de usuários: orquestra a remoção (com limpeza de dependências no model).
class UserController {
    constructor({ userModel }) {
        this.userModel = userModel;
        this.remove = this.remove.bind(this);
    }

    async remove(req, res, next) {
        try {
            const id = Number(req.params.id);
            await this.userModel.deleteWithDependencies(id);
            res.status(200).send('Usuário e dados relacionados (matrículas e pagamentos) removidos.');
        } catch (err) {
            next(err);
        }
    }
}

module.exports = UserController;
