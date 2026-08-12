/**
 * Controller de usuários — fluxo HTTP -> model (com transação limpa).
 */
const userModel = require('../models/userModel');

function removeUser(req, res, next) {
    userModel
        .deleteById(Number(req.params.id))
        .then(() => {
            res.json({ msg: 'Usuário removido juntamente com matrículas e pagamentos' });
        })
        .catch(next);
}

module.exports = { removeUser };