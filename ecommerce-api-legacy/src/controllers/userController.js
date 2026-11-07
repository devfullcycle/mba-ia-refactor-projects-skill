class UserController {
    constructor(userModel) {
        this._users = userModel;
    }

    async remove(req, res, next) {
        try {
            await this._users.deleteWithRelations(req.params.id);
            res.json({ message: 'Usuário e dados relacionados removidos com sucesso' });
        } catch (err) {
            next(err);
        }
    }
}

module.exports = UserController;
