'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createConnection } = require('../../src/infrastructure/database/connection');
const { createUserRepository } = require('../../src/infrastructure/database/repositories/user-repository');
const { createCourseRepository } = require('../../src/infrastructure/database/repositories/course-repository');
const { createEnrollmentRepository } = require('../../src/infrastructure/database/repositories/enrollment-repository');
const { createPaymentRepository } = require('../../src/infrastructure/database/repositories/payment-repository');
const { createAuditLogRepository } = require('../../src/infrastructure/database/repositories/audit-log-repository');
const { createPasswordHasher } = require('../../src/infrastructure/security/password-hasher');
const { createMemoryCache } = require('../../src/infrastructure/cache/memory-cache');
const { createCheckoutUseCase } = require('../../src/application/checkout');
const { PaymentDeniedError, AuthorizationError } = require('../../src/domain/errors');

function userIdentity(email) {
    return { role: 'user', email, canCheckoutForAnyEmail: false };
}

function buildUseCase(overrides = {}) {
    const connection = createConnection();
    const userRepository = createUserRepository(connection);
    const courseRepository = createCourseRepository(connection);
    const enrollmentRepository = createEnrollmentRepository(connection);
    const paymentRepository = createPaymentRepository(connection);
    const auditLogRepository = overrides.auditLogRepository || createAuditLogRepository(connection);
    const passwordHasher = createPasswordHasher();
    const cache = createMemoryCache();
    const logger = { info() {}, error() {} };

    const course = courseRepository.create({ title: 'Curso Teste', price: 100, active: 1 });

    const useCase = createCheckoutUseCase({
        connection,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        passwordHasher,
        paymentGateway: { charge: ({ card }) => ({ status: card.startsWith('4') ? 'PAID' : 'DENIED' }) },
        cache,
        logger,
    });

    return { useCase, connection, userRepository, course };
}

test('checkout aprovado cria usuário, matrícula e pagamento de forma atômica', () => {
    const { useCase, userRepository, course } = buildUseCase();

    const result = useCase.execute({
        name: 'Ana',
        email: 'ana@teste.com',
        password: 'senha-forte',
        courseId: course.id,
        card: '4111111111111111',
    }, userIdentity('ana@teste.com'));

    assert.equal(result.message, 'Sucesso');
    assert.ok(result.enrollmentId);
    assert.ok(userRepository.findByEmail('ana@teste.com'));
});

test('checkout recusado não deixa usuário órfão criado (sem estado parcial)', () => {
    const { useCase, userRepository, course } = buildUseCase();

    assert.throws(
        () => useCase.execute({
            name: 'Bruno',
            email: 'bruno@teste.com',
            password: 'senha-forte',
            courseId: course.id,
            card: '5111111111111111',
        }, userIdentity('bruno@teste.com')),
        PaymentDeniedError
    );

    assert.equal(userRepository.findByEmail('bruno@teste.com'), null);
});

test('falha após matrícula e pagamento reverte todas as escritas do checkout', () => {
    const auditFailure = new Error('falha de auditoria injetada');
    const { useCase, connection, userRepository, course } = buildUseCase({
        auditLogRepository: { record() { throw auditFailure; } },
    });

    assert.throws(
        () => useCase.execute({
            name: 'Caio',
            email: 'caio@teste.com',
            password: 'senha-forte',
            courseId: course.id,
            card: '4111111111111111',
        }, userIdentity('caio@teste.com')),
        auditFailure
    );

    assert.equal(userRepository.findByEmail('caio@teste.com'), null);
    assert.equal(connection.prepare('SELECT COUNT(*) AS total FROM enrollments').get().total, 0);
    assert.equal(connection.prepare('SELECT COUNT(*) AS total FROM payments').get().total, 0);
});

test('usuário não pode executar checkout em nome de outro e-mail', () => {
    const { useCase, userRepository, course } = buildUseCase();

    assert.throws(
        () => useCase.execute({
            name: 'Vítima',
            email: 'vitima@teste.com',
            password: 'senha-forte',
            courseId: course.id,
            card: '4111111111111111',
        }, userIdentity('atacante@teste.com')),
        AuthorizationError
    );
    assert.equal(userRepository.findByEmail('vitima@teste.com'), null);
});

test('administrador segue política explícita de checkout para qualquer e-mail', () => {
    const { useCase, userRepository, course } = buildUseCase();
    const result = useCase.execute({
        name: 'Cliente administrado',
        email: 'cliente@teste.com',
        password: 'senha-forte',
        courseId: course.id,
        card: '4111111111111111',
    }, { role: 'admin', email: null, canCheckoutForAnyEmail: true });

    assert.equal(result.message, 'Sucesso');
    assert.ok(userRepository.findByEmail('cliente@teste.com'));
});
