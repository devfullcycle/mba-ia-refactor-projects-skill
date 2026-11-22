class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const { lastId } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return lastId;
    }

    deleteById(id) {
        return this.db.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

module.exports = UserModel;
