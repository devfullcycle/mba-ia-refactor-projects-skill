'use strict';

const { assertRemovable } = require('../domain/enrollment');
const { NotFoundError, ConflictError } = require('../domain/errors');

/**
 * Caso de uso: exclusão de usuário. Política aprovada é RESTRICT: recusa
 * a exclusão (409) quando existir matrícula/pagamento vinculado, evitando
 * o registro órfão do comportamento original (F-006).
 */
function createDeleteUserUseCase({ connection, userRepository, enrollmentRepository, paymentRepository }) {
    return {
        execute({ userId }) {
            const user = userRepository.findById(userId);
            if (!user) {
                throw new NotFoundError('Usuário não encontrado');
            }

            const enrollmentsCount = enrollmentRepository.countByUserId(userId);
            const paymentsCount = paymentRepository.countByUserId(userId);

            if (!assertRemovable({ enrollmentsCount, paymentsCount })) {
                throw new ConflictError('Usuário possui matrículas ou pagamentos vinculados e não pode ser removido');
            }

            connection.transaction(() => {
                userRepository.delete(userId);
            });

            return { id: userId };
        },
    };
}

module.exports = { createDeleteUserUseCase };
