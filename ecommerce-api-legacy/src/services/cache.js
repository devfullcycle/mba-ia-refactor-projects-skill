// Cache encapsulado e injetável — substitui o `globalCache` global mutável.
class Cache {
    constructor(logger) {
        this._store = {};
        this._logger = logger;
    }

    set(key, value) {
        this._logger.info(`Salvando no cache: ${key}`);
        this._store[key] = value;
    }

    get(key) {
        return this._store[key];
    }
}

module.exports = Cache;
