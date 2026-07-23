'use strict';

/**
 * Cache em memória com lifecycle explícito (F-008). Deve ser instanciado
 * pelo bootstrap e injetado; nunca referenciado como singleton global.
 */
function createMemoryCache({ maxEntries = 1000 } = {}) {
    if (!Number.isInteger(maxEntries) || maxEntries <= 0) {
        throw new Error('maxEntries deve ser um inteiro positivo');
    }

    const store = new Map();

    return {
        set(key, value) {
            if (store.has(key)) {
                store.delete(key);
            }
            store.set(key, value);
            if (store.size > maxEntries) {
                const oldestKey = store.keys().next().value;
                store.delete(oldestKey);
            }
        },
        get(key) {
            return store.get(key);
        },
        clear() {
            store.clear();
        },
        get size() {
            return store.size;
        },
    };
}

module.exports = { createMemoryCache };
