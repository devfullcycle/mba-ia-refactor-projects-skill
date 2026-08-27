const { dbRun, dbGet } = require('../database');

class PaymentModel {
    static async create(enrollmentId, amount, status) {
        const result = await dbRun(
            "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
            [enrollmentId, amount, status]
        );
        return result.lastID;
    }

    static async getByEnrollmentId(enrollmentId) {
        return await dbGet("SELECT * FROM payments WHERE enrollment_id = ?", [enrollmentId]);
    }
}

module.exports = PaymentModel;
