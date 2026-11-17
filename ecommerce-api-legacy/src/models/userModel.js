const db = require('./database');
const { hashPassword } = require('../utils/security');

class UserModel {
    static async findByEmail(email) {
        return db.get(
            "SELECT id, name, email FROM users WHERE email = ?",
            [email]
        );
    }

    static async findById(id) {
        return db.get(
            "SELECT id, name, email FROM users WHERE id = ?",
            [id]
        );
    }

    static async create({ name, email, password }) {
        const hashedPassword = hashPassword(password);
        const result = await db.run(
            "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
            [name, email, hashedPassword]
        );
        return {
            id: result.lastID,
            name,
            email
        };
    }

    static async deleteById(id) {
        // Garante a integridade referencial: remove pagamentos, matrículas e usuário
        const enrollments = await db.all("SELECT id FROM enrollments WHERE user_id = ?", [id]);
        if (enrollments && enrollments.length > 0) {
            const enrollmentIds = enrollments.map(e => e.id);
            const placeholders = enrollmentIds.map(() => '?').join(',');
            await db.run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
            await db.run("DELETE FROM enrollments WHERE user_id = ?", [id]);
        }

        const result = await db.run("DELETE FROM users WHERE id = ?", [id]);
        return result.changes > 0;
    }
}

module.exports = UserModel;
