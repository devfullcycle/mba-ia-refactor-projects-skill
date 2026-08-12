/**
 * Persistência — encapsula a conexão SQLite.
 * Substitui o estado global por uma única factory inicializada no boot.
 */
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const { config } = require('../config');

let db = null;

function initDb() {
    if (db) return db;
    db = new sqlite3.Database(config.dbFile);
    db.serialize(() => {
        db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
        db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
    });
    return db;
}

function getDb() {
    if (!db) return initDb();
    return db;
}

function seed() {
    const database = getDb();
    const { hashPassword } = require('../utils/security');
    const hashedPass = hashPassword('123');
    database.run("INSERT OR IGNORE INTO users (id, name, email, pass) VALUES (1, 'Leonan', 'leonan@fullcycle.com.br', ?)", [hashedPass]);
    database.run("INSERT OR IGNORE INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    database.run("INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (1, 1)");
    database.run("INSERT OR IGNORE INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { initDb, getDb, seed };