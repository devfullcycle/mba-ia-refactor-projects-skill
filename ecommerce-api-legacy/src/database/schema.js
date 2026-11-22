const crypto = require('crypto');
const { PAYMENT_STATUS } = require('../config/constants');

const SCHEMA = [
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)',
    'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    'CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)',
    'CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)',
    'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)'
];

async function initSchema(db) {
    for (const statement of SCHEMA) {
        await db.run(statement);
    }
}

// Dados de demonstração. O usuário seed recebe uma senha aleatória descartada
// (não há endpoint de login), em vez de uma senha fixa em texto puro.
async function seed(db, passwordService) {
    const passwordHash = await passwordService.hash(crypto.randomBytes(16).toString('hex'));

    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', passwordHash]);
    await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', ['Clean Architecture', 997.0, 1]);
    await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', ['Docker', 497.0, 1]);
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [1, 997.0, PAYMENT_STATUS.PAID]);
}

module.exports = { initSchema, seed };
