'use strict';

const { hashPassword } = require('../utils/password');

/** Campos expostos para fora da camada de dados — `password_hash` nunca sai daqui. */
const PUBLIC_FIELDS = 'id, name, email, created_at';

class UserRepository {
    constructor(connection) {
        this.db = connection;
    }

    findById(id) {
        return this.db.get(`SELECT ${PUBLIC_FIELDS} FROM users WHERE id = ?`, [id]);
    }

    findByEmail(email) {
        return this.db.get(`SELECT ${PUBLIC_FIELDS} FROM users WHERE email = ?`, [email]);
    }

    async create({ name, email, password }) {
        const passwordHash = await hashPassword(password);
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return { id: lastID, name, email };
    }

    /** Remove o usuário; matrículas e pagamentos caem por cascade do schema. */
    async deleteById(id) {
        const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
        return changes > 0;
    }
}

module.exports = { UserRepository };
