// Logger mínimo com níveis; ponto único para trocar por pino/winston no futuro.
const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
  const threshold = LEVELS[level] ?? LEVELS.info;
  const write = (name, method) => (...args) => {
    if (LEVELS[name] >= threshold) {
      console[method](`${new Date().toISOString()} ${name.toUpperCase()}`, ...args);
    }
  };
  return {
    debug: write('debug', 'log'),
    info: write('info', 'log'),
    warn: write('warn', 'warn'),
    error: write('error', 'error'),
  };
}

module.exports = { createLogger };
