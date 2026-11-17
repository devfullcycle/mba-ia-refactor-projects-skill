const UserModel = require('../models/userModel');

class UserController {
    static async deleteUser(req, res, next) {
        try {
            const userId = parseInt(req.params.id, 10);
            if (isNaN(userId)) {
                return res.status(400).send("ID inválido");
            }

            const deleted = await UserModel.deleteById(userId);
            if (!deleted) {
                return res.status(404).send("Usuário não encontrado");
            }

            return res.status(200).send("Usuário e dados associados deletados com sucesso.");
        } catch (error) {
            next(error);
        }
    }
}

module.exports = UserController;
