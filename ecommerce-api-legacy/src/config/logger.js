const config = require('./config');

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
const threshold = LEVELS[config.logLevel] || LEVELS.info;

function log(level, message, meta) {
    if (LEVELS[level] < threshold) return;
    const line = JSON.stringify({ time: new Date().toISOString(), level, message, ...meta });
    if (LEVELS[level] >= LEVELS.error) console.error(line);
    else console.log(line);
}

module.exports = {
    debug: (message, meta) => log('debug', message, meta),
    info: (message, meta) => log('info', message, meta),
    warn: (message, meta) => log('warn', message, meta),
    error: (message, meta) => log('error', message, meta),
};
