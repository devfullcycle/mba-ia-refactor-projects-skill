'use strict';

/**
 * Logger mínimo com níveis — substitui os `console.log` de diagnóstico do legado,
 * que chegavam a imprimir número de cartão e chave do gateway.
 */

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const emit = (levelName, message, context) => {
        if (LEVELS[levelName] > threshold) return;
        const line = {
            ts: new Date().toISOString(),
            level: levelName,
            message,
            ...(context ? { context } : {}),
        };
        const sink = levelName === 'error' ? process.stderr : process.stdout;
        sink.write(`${JSON.stringify(line)}\n`);
    };

    return {
        error: (message, context) => emit('error', message, context),
        warn: (message, context) => emit('warn', message, context),
        info: (message, context) => emit('info', message, context),
        debug: (message, context) => emit('debug', message, context),
    };
}

module.exports = { createLogger };
