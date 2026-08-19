const { dbRun } = require('../database');

class AuditLogModel {
    static async log(action) {
        const result = await dbRun(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action]
        );
        return result.lastID;
    }
}

module.exports = AuditLogModel;
