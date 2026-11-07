class UserModel {
    constructor(db) {
        this._db = db;
    }

    findByEmail(email) {
        return this._db.get('SELECT * FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const result = await this._db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
        );
        return result.lastID;
    }

    /** Deleta o usuário e, em cascata, matrículas e pagamentos (sem órfãos). */
    async deleteWithRelations(userId) {
        const enrollments = await this._db.all(
            'SELECT id FROM enrollments WHERE user_id = ?',
            [userId],
        );
        for (const enr of enrollments) {
            await this._db.run('DELETE FROM payments WHERE enrollment_id = ?', [enr.id]);
        }
        await this._db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
        const result = await this._db.run('DELETE FROM users WHERE id = ?', [userId]);
        return result.changes;
    }
}

module.exports = UserModel;
