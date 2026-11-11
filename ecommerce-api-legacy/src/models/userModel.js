const db = require('../config/database');

const UserModel = {
    findIdByEmail(email) {
        return db.get('SELECT id FROM users WHERE email = ?', [email]);
    },

    async create({ name, email, passwordHash }) {
        const { lastID } = await db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
        );
        return lastID;
    },

    // Matrículas e pagamentos são removidos via ON DELETE CASCADE.
    async deleteById(id) {
        const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
        return changes > 0;
    },
};

module.exports = UserModel;
