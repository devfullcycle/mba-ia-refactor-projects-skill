'use strict';

const STATUS_PAID = 'PAID';
const STATUS_DENIED = 'DENIED';

class PaymentRepository {
    constructor(connection) {
        this.db = connection;
    }

    async create({ enrollmentId, amount, status }) {
        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return { id: lastID, enrollmentId, amount, status };
    }
}

module.exports = { PaymentRepository, STATUS_PAID, STATUS_DENIED };
