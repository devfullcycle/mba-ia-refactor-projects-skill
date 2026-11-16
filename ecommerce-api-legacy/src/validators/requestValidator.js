const { ValidationError } = require('../utils/errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const DIGITS_PATTERN = /^\d+$/;

function parsePositiveInt(value) {
    const number = Number(value);
    return Number.isInteger(number) && number > 0 ? number : null;
}

function validateCheckout(body) {
    const { usr, eml, pwd, c_id: cId, card } = body || {};

    if (!usr || !eml || !cId || !card) throw new ValidationError('Bad Request');
    if (typeof usr !== 'string' || typeof eml !== 'string' || !EMAIL_PATTERN.test(eml)) {
        throw new ValidationError('Dados de usuário inválidos');
    }
    if (typeof card !== 'string' || !DIGITS_PATTERN.test(card)) {
        throw new ValidationError('Cartão inválido');
    }
    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') {
        throw new ValidationError('Senha inválida');
    }
    const courseId = parsePositiveInt(cId);
    if (courseId === null) throw new ValidationError('Curso inválido');

    return { name: usr.trim(), email: eml.trim().toLowerCase(), password: pwd || null, courseId, card };
}

function validateId(value) {
    const id = parsePositiveInt(value);
    if (id === null) throw new ValidationError('Id inválido');
    return id;
}

module.exports = { validateCheckout, validateId };
