const userService = require('../services/userService');

exports.deleteUser = async (req, res) => {
  const id = Number(req.params.id);
  await userService.deleteUser(id);
  res.status(200).json({
    msg: 'Usuario deletado com sucesso (matriculas e pagamentos removidos em cascata).',
  });
};
