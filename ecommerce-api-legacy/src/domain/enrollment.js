'use strict';

/**
 * Regra de domínio para decidir se um usuário pode ser removido sem
 * quebrar integridade referencial (F-006/F-007, RESTRICT aprovado).
 */
function assertRemovable({ enrollmentsCount, paymentsCount }) {
    return enrollmentsCount === 0 && paymentsCount === 0;
}

module.exports = { assertRemovable };
