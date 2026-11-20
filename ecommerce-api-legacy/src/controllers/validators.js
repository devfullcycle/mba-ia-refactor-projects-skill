const { ValidationError } = require('./errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_NUMBER_PATTERN = /^\d+$/;
const CARD_SEPARATORS = /[\s-]/g;

function requireText(value) {
    if (typeof value !== 'string' || value.trim() === '') throw new ValidationError();
    return value.trim();
}

function requirePositiveInteger(value) {
    const number = typeof value === 'string' && value.trim() !== '' ? Number(value) : value;
    if (!Number.isInteger(number) || number <= 0) throw new ValidationError();
    return number;
}

function requireEmail(value) {
    const email = requireText(value);
    if (!EMAIL_PATTERN.test(email)) throw new ValidationError();
    return email;
}

function requireCardNumber(value) {
    const cardNumber = requireText(value).replace(CARD_SEPARATORS, '');
    if (!CARD_NUMBER_PATTERN.test(cardNumber)) throw new ValidationError();
    return cardNumber;
}

function optionalText(value) {
    if (value === undefined || value === null || value === '') return null;
    return requireText(value);
}

function validateCheckoutInput({ name, email, password, courseId, cardNumber }) {
    return {
        name: requireText(name),
        email: requireEmail(email),
        password: optionalText(password),
        courseId: requirePositiveInteger(courseId),
        cardNumber: requireCardNumber(cardNumber),
    };
}

module.exports = { validateCheckoutInput, requirePositiveInteger };
