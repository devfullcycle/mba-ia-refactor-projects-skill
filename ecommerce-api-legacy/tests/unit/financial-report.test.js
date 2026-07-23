'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createConnection } = require('../../src/infrastructure/database/connection');
const { createUserRepository } = require('../../src/infrastructure/database/repositories/user-repository');
const { createCourseRepository } = require('../../src/infrastructure/database/repositories/course-repository');
const { createEnrollmentRepository } = require('../../src/infrastructure/database/repositories/enrollment-repository');
const { createPaymentRepository } = require('../../src/infrastructure/database/repositories/payment-repository');
const { createFinancialReportUseCase } = require('../../src/application/financial-report');

test('relatório mantém quantidade constante de consultas com múltiplas matrículas', () => {
    const connection = createConnection();
    const userRepository = createUserRepository(connection);
    const courseRepository = createCourseRepository(connection);
    const enrollmentRepository = createEnrollmentRepository(connection);
    const paymentRepository = createPaymentRepository(connection);

    const course = courseRepository.create({ title: 'Curso em lote', price: 75, active: 1 });
    for (let index = 0; index < 4; index += 1) {
        const user = userRepository.create({
            name: `Aluno ${index}`,
            email: `aluno${index}@teste.com`,
            passwordHash: `hash-${index}`,
        });
        const enrollment = enrollmentRepository.create({ userId: user.id, courseId: course.id });
        paymentRepository.create({ enrollmentId: enrollment.id, amount: 75, status: 'PAID' });
    }

    let queries = 0;
    const originalPrepare = connection.prepare;
    connection.prepare = (sql) => {
        queries += 1;
        return originalPrepare(sql);
    };

    const useCase = createFinancialReportUseCase({ courseRepository, enrollmentRepository });
    const report = useCase.execute();

    assert.equal(queries, 2);
    assert.equal(report[0].revenue, 300);
    assert.equal(report[0].students.length, 4);
    connection.close();
});
