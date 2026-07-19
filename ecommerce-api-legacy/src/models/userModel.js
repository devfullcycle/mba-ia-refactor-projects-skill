// Model de usuários — todo acesso a dados da entidade User vive aqui.
class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
    }

    async create(name, email, passHash) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passHash]
        );
        return lastID;
    }

    // Remove o usuário e seus dados dependentes de forma atômica (sem deixar órfãos).
    async deleteWithDependencies(id) {
        return this.db.transaction(async () => {
            await this.db.run(
                'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                [id]
            );
            await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
            const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes;
        });
    }
}

module.exports = UserModel;
