/**
 * Model de usuários — persistência de usuários e autenticação.
 */
const bcrypt = require('bcryptjs');
const { getDb } = require('./db');

function findById(id) {
    return new Promise((resolve, reject) => {
        getDb().get('SELECT id, name, email FROM users WHERE id = ?', [id], (err, row) => {
            if (err) return reject(err);
            resolve(row || null);
        });
    });
}

function findByEmail(email) {
    return new Promise((resolve, reject) => {
        getDb().get('SELECT * FROM users WHERE email = ?', [email], (err, row) => {
            if (err) return reject(err);
            resolve(row || null);
        });
    });
}

function hashPassword(password) {
    return bcrypt.hash(password, 10);
}

function create(name, email, password) {
    return hashPassword(password).then((passHash) => {
        return new Promise((resolve, reject) => {
            getDb().run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passHash],
                function (err) {
                    if (err) return reject(err);
                    resolve({ id: this.lastID, name, email });
                }
            );
        });
    });
}

function verifyPassword(password, hash) {
    return bcrypt.compareSync(password, hash);
}

function deleteById(id) {
    return new Promise((resolve, reject) => {
        getDb().serialize(() => {
            getDb().run('BEGIN');
            getDb().run(
                'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                [id]
            );
            getDb().run('DELETE FROM enrollments WHERE user_id = ?', [id]);
            getDb().run('DELETE FROM users WHERE id = ?', [id], (err) => {
                if (err) {
                    getDb().run('ROLLBACK');
                    return reject(err);
                }
                getDb().run('COMMIT');
                resolve(true);
            });
        });
    });
}

module.exports = { findById, findByEmail, create, verifyPassword, deleteById };