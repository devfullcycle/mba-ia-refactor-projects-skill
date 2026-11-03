// Fluxo do checkout: validação → curso → pagamento → matrícula atômica → cache.
const { NotFoundError, PaymentDeclinedError, ValidationError } = require('../utils/errors');
const { PAYMENT_STATUS } = require('../models/enrollmentModel');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d{13,19}$/;

function parseCheckoutInput(body = {}) {
  // Nomes do payload (usr, eml, pwd, c_id, card) fazem parte do contrato público da API.
  const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card } = body;
  const courseId = Number(rawCourseId);
  const cardNumber = String(card ?? '').replace(/\s+/g, '');

  if (!name || !email || !rawCourseId || !card) throw new ValidationError('Bad Request');
  if (!EMAIL_PATTERN.test(email) || !Number.isInteger(courseId) || courseId <= 0 || !CARD_PATTERN.test(cardNumber)) {
    throw new ValidationError('Bad Request');
  }
  return { name: String(name), email: String(email), password, courseId, card: cardNumber };
}

class CheckoutController {
  constructor({ db, userModel, courseModel, enrollmentModel, paymentService, passwordService, cacheService }) {
    this.db = db;
    this.users = userModel;
    this.courses = courseModel;
    this.enrollments = enrollmentModel;
    this.payments = paymentService;
    this.passwords = passwordService;
    this.cache = cacheService;
  }

  async checkout(body) {
    const input = parseCheckoutInput(body);

    const course = await this.courses.findActiveById(input.courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const existingUser = await this.users.findIdByEmail(input.email);
    if (!existingUser && !input.password) {
      throw new ValidationError('Senha obrigatória para novo usuário');
    }

    const paymentStatus = this.payments.charge(input.card, course.price);
    if (paymentStatus === PAYMENT_STATUS.DENIED) throw new PaymentDeclinedError('Pagamento recusado');

    const passwordHash = existingUser ? null : await this.passwords.hashPassword(String(input.password));

    const { userId, enrollmentId } = await this.db.transaction(async (tx) => {
      const id = existingUser
        ? existingUser.id
        : await this.users.create({ name: input.name, email: input.email, passwordHash }, tx);
      const newEnrollmentId = await this.enrollments.create(id, course.id, tx);
      await this.enrollments.addPayment(newEnrollmentId, course.price, paymentStatus, tx);
      await this.enrollments.recordAudit(`Checkout curso ${course.id} por ${id}`, tx);
      return { userId: id, enrollmentId: newEnrollmentId };
    });

    this.cache.set(`last_checkout_${userId}`, course.title);
    return { msg: 'Sucesso', enrollment_id: enrollmentId };
  }
}

module.exports = CheckoutController;
