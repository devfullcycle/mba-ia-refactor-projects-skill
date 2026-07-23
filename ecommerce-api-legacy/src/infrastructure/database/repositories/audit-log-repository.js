'use strict';

function createAuditLogRepository(connection) {
    return {
        record(action, tx = connection) {
            tx.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))").run(action);
        },
    };
}

module.exports = { createAuditLogRepository };
