class AuditLogModel {
    constructor(db) {
        this._db = db;
    }

    create(action) {
        return this._db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
    }
}

module.exports = AuditLogModel;
