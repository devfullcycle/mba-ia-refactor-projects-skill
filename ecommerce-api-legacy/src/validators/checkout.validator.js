'use strict';

const { ValidationError } = require('../utils/errors');

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Validação do payload de checkout.
 *
 * O contrato público é preservado (`usr`, `eml`, `pwd`, `c_id`, `card`), porque clientes
 * existentes dependem dele; os nomes de domínio são aceitos como alias e usados
 * internamente. O legado só verificava presença e substituía senha ausente por "123456".
 */
function validateCheckout(body = {}) {
    const name = body.usr ?? body.name;
    const email = body.eml ?? body.email;
    const password = body.pwd ?? body.password;
    const courseId = body.c_id ?? body.courseId;
    const card = body.card;

    if (!name || !email || !courseId || !card) {
        throw new ValidationError('Bad Request');
    }
    if (!EMAIL_REGEX.test(String(email))) {
        throw new ValidationError('Email inválido');
    }
    if (!Number.isInteger(Number(courseId))) {
        throw new ValidationError('c_id deve ser um inteiro');
    }
    if (!/^\d{13,19}$/.test(String(card))) {
        throw new ValidationError('Número de cartão inválido');
    }

    // A senha só é exigida quando o checkout precisa criar a conta — a regra pertence ao
    // cadastro de usuário e é aplicada por `validateNewUserPassword`, no service. Exigi-la
    // aqui quebraria o checkout de quem já tem conta.
    return {
        name: String(name).trim(),
        email: String(email).trim().toLowerCase(),
        password: password === undefined || password === null ? null : String(password),
        courseId: Number(courseId),
        card: String(card),
    };
}

/** Regra de senha aplicada apenas na criação de conta. */
function validateNewUserPassword(password, { passwordMinLength = 6 } = {}) {
    if (!password || String(password).length < passwordMinLength) {
        throw new ValidationError(
            `pwd é obrigatório para criar a conta e deve ter no mínimo ` +
                `${passwordMinLength} caracteres`
        );
    }
    return String(password);
}

function validateUserId(rawId) {
    const id = Number(rawId);
    if (!Number.isInteger(id) || id <= 0) {
        throw new ValidationError('id inválido');
    }
    return id;
}

module.exports = {
    validateCheckout,
    validateNewUserPassword,
    validateUserId,
    EMAIL_REGEX,
};
