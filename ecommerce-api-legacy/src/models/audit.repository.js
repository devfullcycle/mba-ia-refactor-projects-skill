'use strict';

class AuditRepository {
    constructor(connection) {
        this.db = connection;
    }

    log(action) {
        return this.db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action]
        );
    }
}

module.exports = { AuditRepository };
