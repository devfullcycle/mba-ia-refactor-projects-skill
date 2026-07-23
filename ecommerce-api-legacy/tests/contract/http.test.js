'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('../../src/app');

const CARD_NUMBER = '4111222233334444';
const DENIED_CARD_NUMBER = '5111222233334444';

function buildTestConfig() {
    return {
        port: 0,
        paymentGatewayKey: 'test-gateway-key',
        seedDemoData: false,
        apiKeys: new Map([
            ['admin-key', Object.freeze({ role: 'admin', email: null, canCheckoutForAnyEmail: true })],
            ['user-key', Object.freeze({ role: 'user', email: 'fulano@teste.com', canCheckoutForAnyEmail: false })],
        ]),
    };
}

async function bootTestServer() {
    const logs = [];
    const logger = {
        info(message, context) { logs.push(['info', message, context]); },
        error(message, context) { logs.push(['error', message, context]); },
    };

    const { app, connection, repositories } = createApp({ config: buildTestConfig(), logger });
    const course = repositories.courseRepository.create({ title: 'Curso Contrato', price: 200, active: 1 });

    const server = await new Promise((resolve) => {
        const s = app.listen(0, () => resolve(s));
    });
    const { port } = server.address();
    const baseUrl = `http://127.0.0.1:${port}`;
    const close = () => new Promise((resolve) => server.close(() => { connection.close(); resolve(); }));

    return { baseUrl, close, logs, course, repositories };
}

test('contrato HTTP: checkout, relatório financeiro e exclusão de usuário', async (t) => {
    const { baseUrl, close, logs, course, repositories } = await bootTestServer();
    t.after(() => close());

    // Sem API key: checkout deve ser recusado com 401
    const unauthorized = await fetch(`${baseUrl}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usr: 'X', eml: 'x@teste.com', c_id: course.id, card: CARD_NUMBER }),
    });
    assert.equal(unauthorized.status, 401);

    // JSON malformado deve ser traduzido na fronteira e nunca virar 500/crash.
    const malformedJson = await fetch(`${baseUrl}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'user-key' },
        body: '{',
    });
    assert.equal(malformedJson.status, 400);
    assert.equal((await malformedJson.json()).code, 'INVALID_JSON');

    // Relatório financeiro exige papel admin; user comum recebe 403
    const forbidden = await fetch(`${baseUrl}/api/admin/financial-report`, {
        headers: { 'x-api-key': 'user-key' },
    });
    assert.equal(forbidden.status, 403);

    // A identidade user não pode executar checkout em nome de outro e-mail.
    const impersonation = await fetch(`${baseUrl}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'user-key' },
        body: JSON.stringify({ usr: 'Intruso', eml: 'vitima@teste.com', pwd: 'senha-forte', c_id: course.id, card: CARD_NUMBER }),
    });
    assert.equal(impersonation.status, 403);
    assert.equal(repositories.userRepository.findByEmail('vitima@teste.com'), null);

    // Checkout aprovado: 200, msg e enrollment_id (forma do payload preservada)
    const approved = await fetch(`${baseUrl}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'user-key' },
        body: JSON.stringify({ usr: 'Fulano', eml: 'fulano@teste.com', pwd: 'senha-forte', c_id: course.id, card: CARD_NUMBER }),
    });
    assert.equal(approved.status, 200);
    const approvedBody = await approved.json();
    assert.equal(approvedBody.msg, 'Sucesso');
    assert.ok(approvedBody.enrollment_id);

    // Checkout recusado: 400, sem side effect de novo usuário
    const denied = await fetch(`${baseUrl}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'user-key' },
        body: JSON.stringify({ usr: 'Fulano', eml: 'fulano@teste.com', pwd: 'senha-forte', c_id: course.id, card: DENIED_CARD_NUMBER }),
    });
    assert.equal(denied.status, 400);

    // Checkout com curso inexistente: 404, como no contrato original
    const badCheckout = await fetch(`${baseUrl}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'user-key' },
        body: JSON.stringify({ usr: 'Fulano', eml: 'fulano@teste.com', c_id: 999, card: CARD_NUMBER }),
    });
    assert.equal(badCheckout.status, 404);

    // Relatório com papel admin: 200, curso aparece com receita agregada
    const report = await fetch(`${baseUrl}/api/admin/financial-report`, {
        headers: { 'x-api-key': 'admin-key' },
    });
    assert.equal(report.status, 200);
    const reportBody = await report.json();
    const courseEntry = reportBody.find((entry) => entry.course === 'Curso Contrato');
    assert.equal(courseEntry.revenue, 200);
    assert.equal(courseEntry.students.length, 1);

    // DELETE de usuário inexistente -> 404
    const deleteMissing = await fetch(`${baseUrl}/api/users/999999`, {
        method: 'DELETE',
        headers: { 'x-api-key': 'admin-key' },
    });
    assert.equal(deleteMissing.status, 404);

    // DELETE de usuário com matrícula/pagamento vinculado -> 409 (RESTRICT aprovado)
    const enrolledUser = repositories.userRepository.findByEmail('fulano@teste.com');
    const deleteConflict = await fetch(`${baseUrl}/api/users/${enrolledUser.id}`, {
        method: 'DELETE',
        headers: { 'x-api-key': 'admin-key' },
    });
    assert.equal(deleteConflict.status, 409);

    // DELETE sem papel admin -> 403
    const deleteForbidden = await fetch(`${baseUrl}/api/users/${enrolledUser.id}`, {
        method: 'DELETE',
        headers: { 'x-api-key': 'user-key' },
    });
    assert.equal(deleteForbidden.status, 403);

    // Log nunca deve conter o número completo dos cartões usados nas chamadas acima.
    const serialized = JSON.stringify(logs);
    assert.equal(serialized.includes(CARD_NUMBER), false);
    assert.equal(serialized.includes(DENIED_CARD_NUMBER), false);
});
