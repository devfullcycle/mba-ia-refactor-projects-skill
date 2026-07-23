const log = (...args) => console.log('[app]', ...args);
const logError = (...args) => console.error('[app:error]', ...args);

module.exports = { log, logError };
