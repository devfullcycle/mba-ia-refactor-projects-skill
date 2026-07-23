'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createConnection } = require('../../src/infrastructure/database/connection');
const { createUserRepository } = require('../../src/infrastructure/database/repositories/user-repository');
const { createCourseRepository } = require('../../src/infrastructure/database/repositories/course-repository');
const { createEnrollmentRepository } = require('../../src/infrastructure/database/repositories/enrollment-repository');
const { createPaymentRepository } = require('../../src/infrastructure/database/repositories/payment-repository');
const { createDeleteUserUseCase } = require('../../src/application/delete-user');
const { ConflictError, NotFoundError } = require('../../src/domain/errors');

function buildUseCase() {
    const connection = createConnection();
    const userRepository = createUserRepository(connection);
    const courseRepository = createCourseRepository(connection);
    const enrollmentRepository = createEnrollmentRepository(connection);
    const paymentRepository = createPaymentRepository(connection);

    const useCase = createDeleteUserUseCase({ connection, userRepository, enrollmentRepository, paymentRepository });
    return { useCase, userRepository, courseRepository, enrollmentRepository, paymentRepository };
}

test('recusa exclusão (409) quando usuário possui matrícula/pagamento vinculado', () => {
    const { useCase, userRepository, courseRepository, enrollmentRepository, paymentRepository } = buildUseCase();

    const user = userRepository.create({ name: 'Carla', email: 'carla@teste.com', passwordHash: 'x' });
    const course = courseRepository.create({ title: 'Curso', price: 50, active: 1 });
    const enrollment = enrollmentRepository.create({ userId: user.id, courseId: course.id });
    paymentRepository.create({ enrollmentId: enrollment.id, amount: 50, status: 'PAID' });

    assert.throws(() => useCase.execute({ userId: user.id }), ConflictError);
    assert.ok(userRepository.findById(user.id));
});

test('remove usuário sem vínculos e retorna 404 para usuário inexistente', () => {
    const { useCase, userRepository } = buildUseCase();
    const user = userRepository.create({ name: 'Davi', email: 'davi@teste.com', passwordHash: 'x' });

    const result = useCase.execute({ userId: user.id });
    assert.equal(result.id, user.id);
    assert.equal(userRepository.findById(user.id), null);

    assert.throws(() => useCase.execute({ userId: 999999 }), NotFoundError);
});
