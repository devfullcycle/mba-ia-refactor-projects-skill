function write(level, message, meta) {
    const line = `[${new Date().toISOString()}] [${level.toUpperCase()}] ${message}`;
    const sink = level === 'error' ? console.error : console.log;
    if (meta === undefined) sink(line);
    else sink(line, meta);
}

module.exports = {
    info: (message, meta) => write('info', message, meta),
    warn: (message, meta) => write('warn', message, meta),
    error: (message, meta) => write('error', message, meta)
};
