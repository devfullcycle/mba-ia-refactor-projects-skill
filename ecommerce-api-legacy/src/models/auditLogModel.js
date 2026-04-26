const { run } = require('../database/connection');

function create(db, action) {
  return run(db, "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { create };
