'use strict';

/**
 * Logger simples com redaction explícita. Nunca receba PAN, senha ou
 * chave de API diretamente: passe apenas contexto já redigido (F-001, F-002).
 */
function createLogger(sink = console) {
    return {
        info(message, context = {}) {
            sink.log(`[INFO] ${message}`, context);
        },
        error(message, context = {}) {
            sink.error(`[ERROR] ${message}`, context);
        },
    };
}

function redactCard(card) {
    if (typeof card !== 'string' || card.length < 4) return '****';
    return `****${card.slice(-4)}`;
}

module.exports = { createLogger, redactCard };
