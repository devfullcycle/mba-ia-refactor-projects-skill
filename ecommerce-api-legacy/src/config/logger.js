const LEVELS = ['debug', 'info', 'warn', 'error'];

function log(level, message, meta = {}) {
    const entry = { timestamp: new Date().toISOString(), level, message, ...meta };
    console.log(JSON.stringify(entry));
}

const logger = LEVELS.reduce((acc, level) => {
    acc[level] = (message, meta) => log(level, message, meta);
    return acc;
}, {});

module.exports = logger;
