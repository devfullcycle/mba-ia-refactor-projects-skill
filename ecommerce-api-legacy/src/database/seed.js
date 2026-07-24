'use strict';

/**
 * Dados de demonstração. Senhas são persistidas com hash — o legado inseria `'123'`
 * em texto plano direto no INSERT.
 */

const { hashPassword } = require('../utils/password');

// Credencial de demonstração, usada apenas pelo seed (que não roda em produção).
// Pode ser sobrescrita por SEED_USER_PASSWORD para não deixar valor fixo no código.
const DEMO_PASSWORD = process.env.SEED_USER_PASSWORD || 'demo1234';

const USERS = [
    { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: DEMO_PASSWORD },
];

const COURSES = [
    { title: 'Clean Architecture', price: 997.0, active: 1 },
    { title: 'Docker', price: 497.0, active: 1 },
];

async function seedIfEmpty(connection, logger) {
    const { total } = await connection.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return false;

    for (const user of USERS) {
        const passwordHash = await hashPassword(user.password);
        await connection.run(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            [user.name, user.email, passwordHash]
        );
    }

    for (const course of COURSES) {
        await connection.run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
            [course.title, course.price, course.active]
        );
    }

    // Matrícula e pagamento iniciais do usuário de demonstração (curso 1).
    const enrollment = await connection.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [1, 1]
    );
    await connection.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollment.lastID, 997.0, 'PAID']
    );

    logger.info('Banco populado com dados de demonstração');
    return true;
}

module.exports = { seedIfEmpty };
