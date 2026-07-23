'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createPasswordHasher } = require('../../src/infrastructure/security/password-hasher');

test('gera hashes diferentes para a mesma senha (salt aleatório)', () => {
    const hasher = createPasswordHasher();
    const a = hasher.hash('minha-senha');
    const b = hasher.hash('minha-senha');
    assert.notEqual(a, b);
});

test('verifica corretamente senha válida e inválida', () => {
    const hasher = createPasswordHasher();
    const hash = hasher.hash('correta');
    assert.equal(hasher.verify(hash, 'correta'), true);
    assert.equal(hasher.verify(hash, 'errada'), false);
});

test('nunca armazena a senha em texto puro no hash resultante', () => {
    const hasher = createPasswordHasher();
    const hash = hasher.hash('segredo123');
    assert.equal(hash.includes('segredo123'), false);
});
