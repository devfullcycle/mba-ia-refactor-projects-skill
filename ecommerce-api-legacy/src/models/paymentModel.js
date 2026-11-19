class PaymentModel {
    constructor(db) {
        this._db = db;
    }

    async create(enrollmentId, amount, status) {
        const result = await this._db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
        );
        return result.lastID;
    }
}

module.exports = PaymentModel;
