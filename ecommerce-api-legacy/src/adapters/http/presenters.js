'use strict';

/**
 * Presenters: única responsabilidade de formatar a saída pública.
 * Preservam a forma essencial do payload original documentada no relatório.
 */
function presentCheckout(result) {
    return { msg: result.message, enrollment_id: result.enrollmentId };
}

function presentFinancialReport(report) {
    return report;
}

function presentDeleteUser(result) {
    return { message: 'Usuário removido com sucesso', id: result.id };
}

module.exports = { presentCheckout, presentFinancialReport, presentDeleteUser };
