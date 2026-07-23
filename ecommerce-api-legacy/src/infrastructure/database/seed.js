'use strict';

const crypto = require('node:crypto');

/**
 * Seed de demonstração, equivalente ao dataset original, porém com senha
 * hasheada (F-004) em vez de texto puro. Controlado por config.seedDemoData
 * para permitir testes com banco vazio.
 */
function seedDemoData({ connection, userRepository, courseRepository, enrollmentRepository, paymentRepository, passwordHasher }) {
    connection.transaction(() => {
        const course1 = courseRepository.create({ title: 'Clean Architecture', price: 997.0, active: 1 });
        courseRepository.create({ title: 'Docker', price: 497.0, active: 1 });

        const user = userRepository.create({
            name: 'Leonan',
            email: 'leonan@fullcycle.com.br',
            passwordHash: passwordHasher.hash(crypto.randomBytes(18).toString('base64url')),
        });

        const enrollment = enrollmentRepository.create({ userId: user.id, courseId: course1.id });
        paymentRepository.create({ enrollmentId: enrollment.id, amount: 997.0, status: 'PAID' });
    });
}

module.exports = { seedDemoData };
