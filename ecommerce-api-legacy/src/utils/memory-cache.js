'use strict';

/**
 * Cache em memória com limite de entradas.
 *
 * O legado usava `let globalCache = {}` em escopo de módulo: sem limite, sem TTL e
 * compartilhado por todas as requisições — vazamento de memória e estado global mutável.
 * Aqui a instância é criada no composition root e injetada em quem precisa.
 */

class MemoryCache {
    constructor({ maxEntries = 500 } = {}) {
        this.maxEntries = maxEntries;
        this.entries = new Map();
    }

    set(key, value) {
        if (this.entries.has(key)) this.entries.delete(key);
        this.entries.set(key, value);
        if (this.entries.size > this.maxEntries) {
            // Descarta a entrada mais antiga (FIFO).
            const oldest = this.entries.keys().next().value;
            this.entries.delete(oldest);
        }
    }

    get(key) {
        return this.entries.get(key);
    }

    get size() {
        return this.entries.size;
    }
}

module.exports = { MemoryCache };
