const checkoutService = require('../services/checkoutService');
const { HttpError } = checkoutService;

exports.checkout = async (req, res) => {
  const name = req.body.usr ?? req.body.name;
  const email = req.body.eml ?? req.body.email;
  const password = req.body.pwd ?? req.body.password;
  const courseId = Number(req.body.c_id ?? req.body.courseId);
  const card = req.body.card ?? req.body.cardNumber;

  if (!name || !email || !courseId || !card) {
    throw new HttpError('Bad Request', 400);
  }

  const result = await checkoutService.checkout({
    name,
    email,
    password,
    courseId,
    card,
  });
  res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollment_id });
};
