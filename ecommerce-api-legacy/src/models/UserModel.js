const bcrypt = require('bcryptjs')

class UserModel {
    constructor(db) {
        this.db = db
    }

    async findByEmail(email) {
        return this.db.getAsync("SELECT id, name, email FROM users WHERE email = ?", [email])
    }

    async findById(id) {
        return this.db.getAsync("SELECT id, name, email FROM users WHERE id = ?", [id])
    }

    async create(name, email, password) {
        const hash = await bcrypt.hash(password, 10)
        const { lastID } = await this.db.runAsync(
            "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
            [name, email, hash]
        )
        return lastID
    }

    async deleteById(id) {
        await this.db.runAsync(
            "DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)",
            [id]
        )
        await this.db.runAsync("DELETE FROM enrollments WHERE user_id = ?", [id])
        const { changes } = await this.db.runAsync("DELETE FROM users WHERE id = ?", [id])
        return changes
    }
}

module.exports = UserModel
