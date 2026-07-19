const passwordService = require('../services/passwordService');

// Cria o schema e carrega os seeds. Recebe a conexão injetada (sem estado global).
// A senha do seed é hasheada (nunca em texto puro).
async function initDb(db) {
    await db.exec(`
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
        CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
        CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
        CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
    `);

    const seedPass = passwordService.hash('123');
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        'Leonan',
        'leonan@fullcycle.com.br',
        seedPass,
    ]);
    await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
        ['Clean Architecture', 997.0, 'Docker', 497.0]
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = initDb;
