const DEFAULT_PORT = 3000;
const DEFAULT_DATABASE_FILE = ':memory:';

function loadConfig(env = process.env) {
    const port = Number.parseInt(env.PORT || DEFAULT_PORT, 10);
    if (!Number.isInteger(port) || port <= 0) {
        throw new Error('Invalid config: PORT must be a positive integer');
    }

    return {
        port,
        databaseFile: env.DATABASE_FILE || DEFAULT_DATABASE_FILE,
        // Sem ADMIN_TOKEN as rotas administrativas ficam bloqueadas (fail closed).
        adminToken: env.ADMIN_TOKEN || null
    };
}

module.exports = { loadConfig };
