// Model de pagamentos — acesso a dados da entidade Payment.
class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    async create(enrollmentId, amount, status) {
        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return lastID;
    }
}

module.exports = PaymentModel;
