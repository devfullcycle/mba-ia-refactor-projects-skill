const { validateId } = require('../validators/requestValidator');

module.exports = ({ models }) => ({
    async remove(req, res) {
        const id = validateId(req.params.id);
        await models.user.deleteWithRelations(id);
        res.send('Usuário deletado, junto com suas matrículas e pagamentos.');
    }
});
