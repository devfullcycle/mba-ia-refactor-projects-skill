class CacheService {
    constructor() {
        this._store = {};
    }

    set(key, value) {
        this._store[key] = value;
    }

    get(key) {
        return this._store[key];
    }
}

module.exports = CacheService;
