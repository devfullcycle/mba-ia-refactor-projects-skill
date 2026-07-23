'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createMemoryCache } = require('../../src/infrastructure/cache/memory-cache');

test('cache aplica limite e remove a entrada menos recente', () => {
    const cache = createMemoryCache({ maxEntries: 2 });
    cache.set('a', 1);
    cache.set('b', 2);
    cache.set('c', 3);

    assert.equal(cache.size, 2);
    assert.equal(cache.get('a'), undefined);
    assert.equal(cache.get('b'), 2);
    assert.equal(cache.get('c'), 3);
});

test('cache rejeita limite inválido', () => {
    assert.throws(() => createMemoryCache({ maxEntries: 0 }), /maxEntries/);
});
