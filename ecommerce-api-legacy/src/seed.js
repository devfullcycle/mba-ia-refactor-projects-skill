const { hashPassword } = require('./services/passwordService');

const SCHEMA_STATEMENTS = [
    'CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)',
    'CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    'CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)',
    'CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)',
    'CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
];

async function createSchema(db) {
    for (const statement of SCHEMA_STATEMENTS) {
        await db.run(statement);
    }
}

async function seedData(db) {
    const passwordHash = await hashPassword('123');
    const user = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', passwordHash]
    );

    const cleanArchitecture = await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
        ['Clean Architecture', 997.0]
    );
    await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
        ['Docker', 497.0]
    );

    const enrollment = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [user.lastID, cleanArchitecture.lastID]
    );

    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollment.lastID, 997.0, 'PAID']
    );
}

async function initDatabase(db) {
    await createSchema(db);
    await seedData(db);
}

module.exports = { initDatabase };
