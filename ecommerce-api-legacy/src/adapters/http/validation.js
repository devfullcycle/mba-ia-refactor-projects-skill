'use strict';

const { ValidationError } = require('../../domain/errors');

/**
 * Traduz o corpo HTTP bruto em comandos independentes de protocolo.
 * Mantém os mesmos nomes de campo externos do contrato original
 * (usr, eml, pwd, c_id, card) para não quebrar o payload observado.
 */
function toCheckoutCommand(body = {}) {
    return {
        name: body.usr,
        email: body.eml,
        password: body.pwd,
        courseId: body.c_id,
        card: body.card,
    };
}

function toDeleteUserCommand(params = {}) {
    const userId = Number(params.id);
    if (!Number.isInteger(userId) || userId <= 0) {
        throw new ValidationError('id de usuário inválido');
    }
    return { userId };
}

module.exports = { toCheckoutCommand, toDeleteUserCommand };
