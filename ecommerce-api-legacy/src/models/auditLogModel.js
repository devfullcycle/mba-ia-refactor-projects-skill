module.exports = (db) => ({
    create: (action) => db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action])
});
