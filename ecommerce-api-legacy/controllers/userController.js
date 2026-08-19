const UserModel = require('../models/userModel');

const deleteUser = async (req, res, next) => {
    try {
        const id = req.params.id;
        await UserModel.delete(id);
        
        return res.status(200).json({ mensagem: "Usuário e dados relacionados deletados com sucesso." });
    } catch (err) {
        next(err);
    }
};

module.exports = { deleteUser };
