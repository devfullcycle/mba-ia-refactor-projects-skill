const db = require('../config/database');

const AuditLogModel = {
    async create(action) {
        const { lastID } = await db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
        return lastID;
    },
};

module.exports = AuditLogModel;
