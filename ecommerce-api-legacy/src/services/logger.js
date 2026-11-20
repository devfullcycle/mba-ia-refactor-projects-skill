const LEVELS = Object.freeze({ error: 0, warn: 1, info: 2, debug: 3 });

// Logger mínimo com níveis, sem dependências externas.
function createLogger(level = 'info') {
    const maxLevel = LEVELS[level] ?? LEVELS.info;

    const write = (lvl, message) => {
        if (LEVELS[lvl] > maxLevel) return;
        const stream = lvl === 'error' ? process.stderr : process.stdout;
        stream.write(`${new Date().toISOString()} ${lvl.toUpperCase()} ${message}\n`);
    };

    return {
        error: (message) => write('error', message),
        warn: (message) => write('warn', message),
        info: (message) => write('info', message),
        debug: (message) => write('debug', message),
    };
}

module.exports = { createLogger };
