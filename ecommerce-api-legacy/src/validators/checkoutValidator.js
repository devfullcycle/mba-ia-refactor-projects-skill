const AppError = require('../errors/AppError');

const BAD_REQUEST = 'Bad Request';
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;

const isNonEmptyString = value => typeof value === 'string' && value.trim() !== '';

// Converte o corpo externo (usr, eml, pwd, c_id, card) em campos internos validados.
function validateCheckout(body) {
    if (!body || typeof body !== 'object') throw new AppError(BAD_REQUEST, 400);

    const { usr, eml, pwd, c_id: courseId, card } = body;

    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !isNonEmptyString(card)) {
        throw new AppError(BAD_REQUEST, 400);
    }
    if (!EMAIL_PATTERN.test(eml)) throw new AppError(BAD_REQUEST, 400);
    if (courseId === undefined || courseId === null || courseId === '') throw new AppError(BAD_REQUEST, 400);
    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') throw new AppError(BAD_REQUEST, 400);

    return {
        name: usr,
        email: eml,
        password: pwd || null,
        courseId,
        card
    };
}

function validateUserId(rawId) {
    const id = Number(rawId);
    if (!Number.isInteger(id) || id <= 0) throw new AppError(BAD_REQUEST, 400);
    return id;
}

module.exports = { validateCheckout, validateUserId };
