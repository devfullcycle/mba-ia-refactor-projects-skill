const { PaymentStatus } = require('./paymentModel');

const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0 },
    { title: 'Docker', price: 497.0 },
];
const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

// Popula o banco apenas quando está vazio (idempotente para bancos em arquivo).
async function seedDatabase(db, passwordHasher) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return;

    const passwordHash = await passwordHasher.hash(SEED_USER.password);
    await db.transaction(async () => {
        const user = await db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [SEED_USER.name, SEED_USER.email, passwordHash],
        );
        const courseIds = [];
        for (const course of SEED_COURSES) {
            const inserted = await db.run(
                'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
                [course.title, course.price],
            );
            courseIds.push(inserted.lastID);
        }
        const enrollment = await db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [user.lastID, courseIds[0]],
        );
        await db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollment.lastID, SEED_COURSES[0].price, PaymentStatus.PAID],
        );
    });
}

module.exports = { seedDatabase };
