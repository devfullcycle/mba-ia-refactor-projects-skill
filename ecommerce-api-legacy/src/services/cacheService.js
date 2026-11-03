// Cache em memória encapsulado (substitui o objeto global mutável). Limite evita crescimento infinito.
const DEFAULT_MAX_ENTRIES = 1000;

class CacheService {
  constructor({ logger, maxEntries = DEFAULT_MAX_ENTRIES }) {
    this.logger = logger;
    this.maxEntries = maxEntries;
    this.store = new Map();
  }

  set(key, value) {
    if (this.store.has(key)) this.store.delete(key);
    this.store.set(key, value);
    if (this.store.size > this.maxEntries) {
      this.store.delete(this.store.keys().next().value);
    }
    this.logger.debug(`Cache atualizado: ${key}`);
  }

  get(key) {
    return this.store.get(key);
  }
}

module.exports = CacheService;
